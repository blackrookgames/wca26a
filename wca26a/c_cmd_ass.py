__all__ = ['cmd_ass']

import sys

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from io import StringIO
from typing import cast, Callable
from pathlib import Path

import assutil
import cli
import cliutil
import help

#region chars

class Chr(Enum):
    DOT = ord('.')
    PRE = ord('@')
    ASS = ord('!')
    STR = ord('"')
    UNSCR = ord('_')

class Chr_Op(Enum):
    REM = ord(';')
    OPAR = ord('(')
    CPAR = ord(')')
    OBRK = ord('{')
    CBRK = ord('}')
    IMM = ord('#')
    SEP = ord(',')
    ADD = ord('+')
    SUB = ord('-')
    MUL = ord('*')
    DIV = ord('/')
    AND = ord('&')
    OR = ord('|')
    XOR = ord('^')
    NOT = ord('~')
    LO = ord('<')
    HI = ord('>')

class Chr_Num(Enum):
    HEX = ord('$')
    BIN = ord('%')

def chr_is_word(_ord:int):
    if _ord == Chr.UNSCR.value: return True
    if _ord >= 0x30 and _ord <= 0x39: return True
    if _ord >= 0x41 and _ord <= 0x5A: return True
    if _ord >= 0x61 and _ord <= 0x7A: return True
    return False

#endregion

#region strings

def str_is_quotes(s:str):
    return len(s) >= 2 and s[0] == '"' and s[-1] == '"'

def str_is_word(s:str):
    if len(s) == 0: return False
    if s[0].isdigit(): return False
    for c in s:
        if c.isdigit(): continue
        if c.isalpha(): continue
        if c == '_': continue
        return False
    return True

#endregion

class cmd_ass(cli.CLICommand):

    #region token

    class _Token:

        #region init

        def __init__(self, src:assutil.SrcChunk):
            self.__src = src

        @classmethod
        def create(cls, *args, **kwargs) -> 'cmd_ass._Token':
            raise NotImplementedError("create has not been implemented.")

        #endregion

        #region properties

        @property
        def src(self): return self.__src

        @property
        def issym(self): return bool(False)

        #endregion

    class _Token_Symbol(_Token):

        #region init

        def __init__(self, src:assutil.SrcChunk):
            super().__init__(src)
            if src.content != self.symbol: raise cmd_ass._error(src, f"Expected {self.symbol}")

        #endregion

        #region operators

        def __str__(self): return self.symbol

        #endregion

        #region properties

        @property
        def issym(self): return True

        @property
        def symbol(self) -> str: raise NotImplementedError("symbol has not been implemented.")

        #endregion
    
    class _TokenLabelDec(_Token):

        #region init

        def __init__(self, src:assutil.SrcChunk,\
                labels:dict[str, 'cmd_ass._TokenLabelDec'], scope:list[str], sensitive:bool):
            """ NOTE: label and scope may be modified """
            super().__init__(src)
            # Make sure it ends with a colon
            if not src.content.endswith(':'):
                raise cmd_ass._error(src, "Label declaration must end with a colon.")
            # Extract level and name
            self.__level, self.__name, self.__path = cmd_ass._TokenLabelRef.extract_labelinfo(
                src.sub(end = len(src.content) - 1), scope, sensitive)
            if self.__path in labels:
                raise cmd_ass._error(src, f"{self.__path} has already been defined.")
            # Update labels and scopes (must be done AFTER ensuring label is valid)
            labels[self.__path] = self
            while len(scope) > self.__level: scope.pop()
            scope.append(self.__name)

        @classmethod
        def create(cls, *args, **kwargs) -> 'cmd_ass._Token':
            return cls(*args, **kwargs)

        #endregion

        #region operators

        def __str__(self): return '.' * self.__level + self.__name + ':'

        #endregion

        #region properties

        @property
        def level(self): return self.__level

        @property
        def name(self): return self.__name

        @property
        def path(self): return self.__path

        #endregion

    class _TokenCommand(_Token):

        #region init

        def __init__(self, src:assutil.SrcChunk):
            super().__init__(src)
            # Make sure it starts with an exclamation point
            if not src.content.startswith('!'):
                raise cmd_ass._error(src, "Assembler command must start with an exclamation point.")
            # Extract name
            self.__name = cmd_ass._get_word(src.sub(1))

        @classmethod
        def create(cls, *args, **kwargs) -> 'cmd_ass._Token':
            return cls(*args, **kwargs)
        
        #endregion

        #region operators

        def __str__(self): return '!' + self.__name

        #endregion

        #region properties

        @property
        def name(self): return self.__name

        #endregion

    class _TokenInstruct(_Token):

        #region init

        def __init__(self, src:assutil.SrcChunk):
            super().__init__(src)
            self.__name = cmd_ass._get_word(src).upper()

        @classmethod
        def create(cls, *args, **kwargs) -> 'cmd_ass._Token':
            return cls(*args, **kwargs)
        
        #endregion

        #region operators

        def __str__(self): return self.__name

        #endregion

        #region properties

        @property
        def name(self): return self.__name

        #endregion

    class _TokenString(_Token):

        #region init

        def __init__(self, src:assutil.SrcChunk):
            super().__init__(src)
            if not str_is_quotes(src.content):
                raise cmd_ass._error(src, "A string must be enclosed with double quotation marks.")
            self.__value = src.content[1:-1]

        #endregion

        #region operators

        def __str__(self): return '"' + self.__value + '"'

        #endregion

        #region properties

        @property
        def value(self): return self.__value

        #endregion

    class _TokenLabelRef(_Token):

        #region init

        def __init__(self, src:assutil.SrcChunk, scope:Sequence[str], sensitive:bool):
            super().__init__(src)
            self.__level, self.__name, self.__path = self.extract_labelinfo(src, scope, sensitive)

        @classmethod
        def create(cls, *args, **kwargs) -> 'cmd_ass._Token':
            return cls(*args, **kwargs)
        
        #endregion

        #region operators

        def __str__(self): return '.' * self.__level + self.__name

        #endregion

        #region properties

        @property
        def level(self): return self.__level

        @property
        def name(self): return self.__name

        @property
        def path(self): return self.__path

        #endregion
        
        #region methods

        @classmethod
        def extract_labelinfo(cls, src:assutil.SrcChunk, scope:Sequence[str], sensitive:bool):
            # Extract level
            level = 0
            while src.content[level] == '.':
                level += 1
            if (level + 1) == len(src.content):
                raise cmd_ass._error(src, "Label name cannot be empty.")
            if level > len(scope):
                raise cmd_ass._error(src, "Invalid scope level")
            # Extract name
            name = cmd_ass._get_word(src.sub(level))
            if not sensitive: name = name.upper()
            # Extract path
            with StringIO() as _path:
                for _i in range(level): _path.write(f"{scope[_i]}.")
                _path.write(name)
                path = _path.getvalue()
            # Success!!!
            return level, name, path

        #endregion

    class _TokenNumber(_Token):

        #region init

        def __init__(self, src:assutil.SrcChunk):
            super().__init__(src)
            self.__value, self.__is16 = self.__parse(src)

        @classmethod
        def create(cls, *args, **kwargs) -> 'cmd_ass._Token':
            return cls(*args, **kwargs)
        
        #endregion

        #region operators

        def __str__(self): return f"${self.__value:04X}" if self.__is16 else f"${self.__value:02X}"

        #endregion

        #region properties

        @property
        def value(self): return self.__value

        @property
        def is16(self): return self.__is16

        #endregion

        #region helper methods

        @classmethod
        def __parse(cls, src:assutil.SrcChunk):
            def _parse(s:str, base:int):
                nonlocal src
                # Parse raw value
                try: raw = int(s, base)
                except: raise cmd_ass._error(src, f"{src.content} is not a valid numerical value.")
                # Check range
                if raw < 0 or raw > 0xFFFF:
                    raise cmd_ass._error(src, f"{raw} is out of range.")
                # Success!!!
                return raw
            def _parse_dec(s:str):
                value = _parse(s, 10)
                return value, value > 0xFF
            def _parse_bin(s:str):
                return _parse(s, 2), len(s) > 8
            def _parse_hex(s:str):
                return _parse(s, 16), len(s) > 2
            if len(src.content) == 0: return 0, False
            first = src.content[0]
            if first == '$': return _parse_hex(src.content[1:])
            if first == '%': return _parse_bin(src.content[1:])
            if first != '0': return _parse_dec(src.content)
            if len(src.content) == 1: return 0, False
            second = src.content[1]
            if second == 'x': return _parse_hex(src.content[2:])
            if second == 'b': return _parse_bin(src.content[2:])
            return _parse_dec(src.content)

        #endregion

    class _TokenRegRef(_Token):

        #region init

        def __init__(self, src:assutil.SrcChunk):
            super().__init__(src)
            self.__reg = src.content.upper()
            if not (self.__reg in self.__REGS):
                raise cmd_ass._error(src, f"{self.__reg} is not a valid register.")

        @classmethod
        def create(cls, *args, **kwargs) -> 'cmd_ass._Token':
            return cls(*args, **kwargs)
        
        #endregion

        #region const

        __REGS = set([ 'A', 'X', 'Y', ])

        #endregion

        #region operators

        def __str__(self): return self.__reg

        #endregion

        #region properties

        @property
        def reg(self): return self.__reg

        #endregion

        #region methods

        @classmethod
        def isvalid(cls, s:str):
            return s.upper() in cls.__REGS

        #endregion

    class _TokenOperator(_Token):

        #region init

        def __init__(self, src:assutil.SrcChunk):
            super().__init__(src)
            self.__type = src.content.upper()
            if not (self.__type in self.__TYPES):
                raise cmd_ass._error(src, f"{self.__type} is not a valid operator type.")

        @classmethod
        def create(cls, *args, **kwargs) -> 'cmd_ass._Token':
            return cls(*args, **kwargs)
        
        #endregion

        #region const

        __WORDS = set([ 'MOD', 'LSHFT', 'RSHFT', 'B8', 'B16', ])
        __CHARS = set([ '+', '-', '*', '/', '&', '|', '^', '~', '<', '>', ])
        __TYPES = set([_i for _i in __WORDS] + [_i for _i in __CHARS])

        #endregion

        #region operators

        def __str__(self): return self.__type

        #endregion

        #region properties

        @property
        def type(self): return self.__type

        #endregion

        #region methods

        @classmethod
        def isvalid(cls, s:str):
            return s.upper() in cls.__TYPES

        #endregion

    class _TokenParOpen(_Token):

        #region init

        def __init__(self, src:assutil.SrcChunk):
            super().__init__(src)
            if src.content != '(' and src.content != '{':
                raise cmd_ass._error(src, "Expected ( or {")
            self.__symbol = src.content

        @classmethod
        def create(cls, *args, **kwargs) -> 'cmd_ass._Token':
            return cls(*args, **kwargs)
        
        #endregion

        #region operators

        def __str__(self): return self.__symbol

        #endregion

        #region properties

        @property
        def issym(self): return True

        @property
        def symbol(self): return self.__symbol

        #endregion
    
    class _TokenParClose(_Token):

        #region init

        def __init__(self, src:assutil.SrcChunk):
            super().__init__(src)
            if src.content != ')' and src.content != '}':
                raise cmd_ass._error(src, "Expected ) or }")
            self.__symbol = src.content

        @classmethod
        def create(cls, *args, **kwargs) -> 'cmd_ass._Token':
            return cls(*args, **kwargs)
        
        #endregion

        #region operators

        def __str__(self): return self.__symbol

        #endregion

        #region properties

        @property
        def issym(self): return True

        @property
        def symbol(self): return self.__symbol

        #endregion
    
    class _TokenImmediate(_Token_Symbol):

        #region init

        def __init__(self, src:assutil.SrcChunk):
            super().__init__(src)

        @classmethod
        def create(cls, *args, **kwargs) -> 'cmd_ass._Token':
            return cls(*args, **kwargs)
        
        #endregion

        #region properties

        @property
        def symbol(self): return '#'

        #endregion
    
    class _TokenDelimiter(_Token_Symbol):

        #region init

        def __init__(self, src:assutil.SrcChunk):
            super().__init__(src)

        @classmethod
        def create(cls, *args, **kwargs) -> 'cmd_ass._Token':
            return cls(*args, **kwargs)
        
        #endregion

        #region properties

        @property
        def symbol(self): return ','

        #endregion

    class _TokenBlock(_Token):

        #region P

        @dataclass(frozen = True)
        class __P:
            tokens:tuple['cmd_ass._Token', ...]
            open:'cmd_ass._TokenParOpen'
            close:'cmd_ass._TokenParClose'

        #endregion

        #region init

        def __init__(self, p):
            assert isinstance(p, self.__P)
            super().__init__(p.open.src)
            self.__p = p
        
        #endregion

        #region operators

        def __str__(self): return f"{self.__p.open}{cmd_ass._echo_tokens(self.__p.tokens)}{self.__p.close}"

        #endregion

        #region properties

        @property
        def tokens(self): return self.__p.tokens

        @property
        def open(self): return self.__p.open
        
        @property
        def close(self): return self.__p.close

        #endregion

        #region helper methods

        @classmethod
        def __blockify(cls, tokens_reversed:list['cmd_ass._Token'], open:'None|cmd_ass._TokenParOpen'):
            blockified:list['cmd_ass._Token'] = []
            while len(tokens_reversed) > 0:
                _token = tokens_reversed.pop()
                if isinstance(_token, cmd_ass._TokenParOpen):
                    blockified.append(cast(cmd_ass._Token, cls.__blockify(tokens_reversed, _token)))
                elif isinstance(_token, cmd_ass._TokenParClose):
                    if open is None:
                        raise cmd_ass._error(_token.src, "Unexpected closing bracket")
                    if open.symbol == '(' and _token.symbol != ')':
                        raise cmd_ass._error(_token.src, "Closing bracket must match opening bracket.")
                    if open.symbol == '{' and _token.symbol != '}':
                        raise cmd_ass._error(_token.src, "Closing bracket must match opening bracket.")
                    return cls(cls.__P(tuple(blockified), open, _token))
                else: blockified.append(_token)
            if open is not None:
                src = blockified[0].src if (len(blockified) > 0) else None
                raise cmd_ass._error(src, "Line ends before block is closed.")
            return blockified

        #endregion

        #region methods

        @classmethod
        def blockify(cls, tokens:list['cmd_ass._Token']):
            tokens_reversed = [tokens[_i] for _i in range(len(tokens) - 1, -1, -1)]
            return cast(list[cmd_ass._Token], cls.__blockify(tokens_reversed, None))

        #endregion

    #endregion

    #region preprocessor

    class __Preprocessor:

        #region init

        def __init__(self, cmd:'cmd_ass', path:Path, macros:dict[str, list[assutil.SrcChunk]]):
            self.__cmd = cmd
            self.__rawlines = assutil.FileUtil.read_all_lines(path)
            self.__directory = path.parent
            self.__case = cast(bool, self.__cmd.case) # type: ignore
            self.__macros = macros
            # Phase 0
            self.__p0_chunksbyline:list[list[assutil.SrcChunk]] = []
            # Phase 1
            self.__p1_if_level:int = 0
            self.__p1_if_true:int = 0
            self.__p1_if_ignore:bool = False
            self.__p1_chunksbyline:list[list[assutil.SrcChunk]] = []

        #endregion

        #region helper methods
        
        @classmethod
        def __raise_if_ne(cls, line:list[assutil.SrcChunk], req:int):
            if (len(line) - 1) == req: return
            raise cmd_ass._error(line, f"Expected only {req} argument(s).")
        
        @classmethod
        def __raise_if_lt(cls, line:list[assutil.SrcChunk], req:int):
            if (len(line) - 1) >= req: return
            raise cmd_ass._error(line, f"Expected at least {req} argument(s).")

        def __raise_if_ndef(self, chunk:assutil.SrcChunk, macro:str):
            if macro in self.__macros: return
            raise cmd_ass._error(chunk, f"Undefined macro: {macro}")

        #endregion

        #region phase0
        
        def __phase0(self):
            def __split(rawline:assutil.SrcChunk):
                pos = 0
                inquotes = False
                def ___read():
                    nonlocal rawline
                    nonlocal pos, inquotes
                    def readchar():
                        nonlocal rawline
                        nonlocal pos
                        c = rawline.content[pos]
                        pos += 1
                        return c
                    # Is this an escape sequence?
                    c = readchar()
                    if not (inquotes and c == '\\'): return False, c
                    # Yes! Is this a simple escape sequence?
                    if pos == len(rawline.content): return True, chr(0)
                    c = readchar()
                    match c:
                        case 'n': return True, '\n'
                        case 't': return True, '\t'
                        case '\\': return True, '\\'
                        case '\"': return True, '\"'
                        case '\'': return True, '\''
                        case 'b': return True, '\b'
                        case 'r': return True, '\r'
                        case 'a': return True, '\a'
                        case '0': return True, '\0'
                    # No! It must be a character code.
                    match c:
                        case 'x': count = 2
                        case 'u': count = 4
                        case _: count = 0
                    code = 0
                    while count > 0:
                        if pos == len(rawline.content): break
                        code <<= 4
                        c = ord(readchar())
                        if c >= 0x30 and c <= 0x39: code |= c - 0x30
                        elif c >= 0x41 and c <= 0x46: code |= (c - 0x41) + 10
                        elif c >= 0x61 and c <= 0x66: code |= (c - 0x61) + 10
                        count -= 1
                    return True, chr(code)
                chunks:list[str] = []
                strio = StringIO()
                def ___flush():
                    nonlocal chunks, strio
                    s = strio.getvalue()
                    if len(s) == 0: return # No empty strings allowed
                    chunks.append(s)
                    strio.close()
                    strio = StringIO()
                try:
                    while pos < len(rawline.content):
                        _escape, _char = ___read()
                        _ord = ord(_char)
                        # Are these quotes?
                        if (not _escape) and _ord == Chr.STR.value:
                            inquotes = not inquotes
                            strio.write(_char)
                        # No! Is this in quotes?
                        elif inquotes:
                            strio.write(_char)
                        # No! Is this a comment?
                        elif _ord == Chr_Op.REM.value:
                            ___flush()
                            break
                        # No! Is this whitespace?
                        elif _ord <= 0x20:
                            ___flush()
                        # No! Is this an "operator"
                        elif _ord in Chr_Op._value2member_map_:
                            ___flush()
                            chunks.append(_char)
                        # No!
                        else: strio.write(_char)
                    ___flush()
                    return chunks
                finally: strio.close()
            self.__p0_chunksbyline.clear()
            for _rawline in self.__rawlines:
                _chunks:list[assutil.SrcChunk] = []
                for _chunk in __split(_rawline):
                    _chunks.append(assutil.SrcChunk(_rawline.path, _rawline.linenumber, _chunk))
                self.__p0_chunksbyline.append(_chunks)

        #endregion

        #region phase1

        def __phase1(self):
            directives = self.__p1_directives()
            # Initialize block counter
            self.__p1_if_level = 0
            self.__p1_if_ignore = False
            self.__p1_if_true = 0
            # Loop thru
            self.__p1_chunksbyline.clear()
            for _line in self.__p0_chunksbyline:
                # Skip if empty
                if len(_line) == 0: continue
                # Is this a preprocessor directive?
                _dirname = _line[0].content.upper()
                if len(_dirname) > 0 and ord(_dirname[0]) == Chr.PRE.value:
                    if not _dirname in directives:
                        raise cmd_ass._error(_line[0], f"Unknown preprocessor directive: {_dirname}")
                    directives[_dirname](_line) # type: ignore
                    continue
                # No! Skip if this is within a 'false' block.
                if self.__p1_if_level > self.__p1_if_true: continue
                # Look for macros
                self.__p1_chunksbyline.append(self.__p1_expandmacros(_line))

        def __p1_directives(self):
            PREFIX = '__p1_dir_'
            directives:dict[str, object] = {}
            for _attrname in dir(self):
                _attr = getattr(self, _attrname)
                if not callable(_attr): continue
                if not _attr.__name__.startswith(PREFIX): continue
                directives[f"@{_attr.__name__[len(PREFIX):]}"] = _attr.__call__
            return directives
    
        def __p1_expandmacros(self, line:list[assutil.SrcChunk]):
            chunks:list[assutil.SrcChunk] = []
            for _chunk in line:
                # Is this a valid macro?
                _macro = _chunk.content if self.__case else _chunk.content.upper()
                if _macro in self.__macros:
                    for _macro_chunk in self.__macros[_macro]:
                        chunks.append(_macro_chunk)
                # No!
                else: chunks.append(_chunk)
            return chunks
        
        def __p1_raise_if_noblock(self, line:list[assutil.SrcChunk]):
            if self.__p1_if_level > 0: return
            if len(line) == 0: raise cmd_ass._error(line, "Unexpected directive")
            raise cmd_ass._error(line, f"Unexpected {line[0].content}")

        def __p1_dir_INCLUDE(self, line:list[assutil.SrcChunk]):
            if self.__p1_if_level > self.__p1_if_true: return
            self.__raise_if_ne(line, 1)
            path = help.PathUtil.absolute(cmd_ass._get_path(line[1]), self.__directory)
            for _line in self.__run(self.__cmd, path, self.__macros):
                self.__p1_chunksbyline.append(_line)

        def __p1_dir_DEFINE(self, line:list[assutil.SrcChunk]):
            if self.__p1_if_level > self.__p1_if_true: return
            self.__raise_if_lt(line, 1)
            # Get macro name
            macro = cmd_ass._get_word(line[1])
            if not self.__case: macro = macro.upper()
            # Add macro
            self.__macros[macro] = self.__p1_expandmacros(line[2:])
        
        def __p1_dir_UNDEF(self, line:list[assutil.SrcChunk]):
            if self.__p1_if_level > self.__p1_if_true: return
            self.__raise_if_ne(line, 1)
            arg_macro = line[1]
            # Get macro name
            macro = cmd_ass._get_word(arg_macro)
            if not self.__case: macro = macro.upper()
            self.__raise_if_ndef(arg_macro, macro)
            # Remove macro
            self.__macros.pop(macro)

        def __p1_dir_IFDEF(self, line:list[assutil.SrcChunk]):
            if self.__p1_if_level == self.__p1_if_true and self.__p1__dir_ifdef(line, False):
                self.__p1_if_true += 1
            self.__p1_if_level += 1

        def __p1_dir_IFNDEF(self, line:list[assutil.SrcChunk]):
            if self.__p1_if_level == self.__p1_if_true and self.__p1__dir_ifdef(line, True):
                self.__p1_if_true += 1
            self.__p1_if_level += 1

        def __p1_dir_IF(self, line:list[assutil.SrcChunk]):
            if self.__p1_if_level == self.__p1_if_true and self.__p1__dir_if(line):
                self.__p1_if_true += 1
            self.__p1_if_level += 1

        def __p1_dir_ELIF(self, line:list[assutil.SrcChunk]):
            self.__p1_raise_if_noblock(line)
            if (self.__p1_if_level - 1) > self.__p1_if_true: return
            # Was the last block true?
            if self.__p1_if_level == self.__p1_if_true:
                self.__p1_if_true -= 1
                self.__p1_if_ignore = True
            # No! Shall we execute the 'elif' block?
            elif (not self.__p1_if_ignore) and self.__p1__dir_if(line):
                self.__p1_if_true = self.__p1_if_level

        def __p1_dir_ELSE(self, line:list[assutil.SrcChunk]):
            self.__p1_raise_if_noblock(line)
            self.__raise_if_ne(line, 0)
            if (self.__p1_if_level - 1) > self.__p1_if_true: return
            # Was the last block true?
            if self.__p1_if_level == self.__p1_if_true:
                self.__p1_if_true -= 1
                self.__p1_if_ignore = True
            # No! Shall we execute the 'else' block?
            elif not self.__p1_if_ignore:
                self.__p1_if_true = self.__p1_if_level

        def __p1_dir_ENDIF(self, line:list[assutil.SrcChunk]):
            self.__p1_raise_if_noblock(line)
            self.__raise_if_ne(line, 0)
            # Decrement
            self.__p1_if_level -= 1
            if self.__p1_if_true > self.__p1_if_level:
                self.__p1_if_true = self.__p1_if_level
            # Should we stop ignoring?
            if self.__p1_if_level == self.__p1_if_true:
                self.__p1_if_ignore = False

        def __p1__dir_ifdef(self, line:list[assutil.SrcChunk], ndef:bool):
            self.__raise_if_ne(line, 1)
            arg_macro = line[1]
            # Get macro name
            macro = cmd_ass._get_word(arg_macro)
            if not self.__case: macro = macro.upper()
            # Check if the macro is defined
            condition = macro in self.__macros
            if ndef: return not condition
            return condition

        def __p1__dir_if(self, line:list[assutil.SrcChunk]):
            def _equals(a:list[assutil.SrcChunk], b:list[assutil.SrcChunk]):
                if len(a) != len(b): return False
                for _i in range(len(a)):
                    if a[_i].content != b[_i].content: return False
                return True
            self.__raise_if_lt(line, 2)
            arg_macro = line[1]
            arg_operator = line[2]
            arg_value = self.__p1_expandmacros(line[3:])
            # Get macro name
            macro = cmd_ass._get_word(arg_macro)
            if not self.__case: macro = macro.upper()
            self.__raise_if_ndef(arg_macro, macro)
            macro_value = self.__macros[macro]
            # Get operator
            operator = cmd_ass._get_word(arg_operator)
            # Check condition
            match operator.upper():
                case 'eq': return _equals(macro_value, arg_value)
                case 'ne': return not _equals(macro_value, arg_value)
                case _: raise cmd_ass._error(arg_operator, f"Unknown equality operator: {operator}")

        #endregion

        #region run

        @classmethod
        def __run(cls, cmd:'cmd_ass', path:Path, macros:dict[str, list[assutil.SrcChunk]]):
            instance = cls(cmd, path, macros)
            instance.__phase0()
            instance.__phase1()
            return instance.__p1_chunksbyline

        @classmethod
        def run(cls, cmd:'cmd_ass', path:Path):
            macros:dict[str, list[assutil.SrcChunk]] = {}
            for _flag in cmd.flags: macros[_flag if self.case else _flag.upper()] = [] # type: ignore
            return cls.__run(cmd, path, macros)

        #endregion

    #endregion

    #region assembler

    class __Assembler:

        #region init

        def __init__(self, cmd:'cmd_ass', lines:list[list[assutil.SrcChunk]]):
            self.__cmd = cmd
            self.__lines = lines
            self.__source = cast(Path, self.__cmd.source) # type: ignore
            self.__output = cast(None|Path, self.__cmd.output) # type: ignore
            self.__intmd = cast(None|Path, self.__cmd.intmd) # type: ignore
            self.__case = cast(bool, self.__cmd.case) # type: ignore
            if self.__output is None: output = self.__source.with_suffix('.a26')
            self.__p0_tokengroups:list[cmd_ass._TokenLabelDec|list[cmd_ass._Token]] = []
            self.__p0_labels:dict[str, cmd_ass._TokenLabelDec] = {}

        #endregion
        
        #region phase 0

        def __phase0(self):
            self.__p0_tokengroups.clear()
            self.__p0_labels.clear()
            labelscope:list[str] = []
            for _line in self.__lines:
                # Filter out labels
                _start = 0
                while _start < len(_line):
                    _chunk = _line[_start]
                    if not _chunk.content.endswith(':'): break
                    self.__p0_tokengroups.append(cmd_ass._TokenLabelDec(_chunk, self.__p0_labels, labelscope, self.__case))
                    _start += 1
                if _start == len(_line): continue
                # First chunk
                _tokens:list[cmd_ass._Token] = []
                _first = _line[_start]
                if _first.content.startswith('!'): # Is this an assembler command? (ex: '!entry')
                    _tokens.append(cmd_ass._TokenCommand(_first))
                else: # No! Parse as assembly instruction! (ex: 'lda')
                    _tokens.append(cmd_ass._TokenInstruct(_first))
                # Next chunks
                for _chunk in _line[1:]:
                    _tokenptr = help.Ptr[cmd_ass._Token]()
                    def _try_create(create:Callable, *args, **kwargs):
                        nonlocal _tokenptr
                        try:
                            _tokenptr.value = create(*args, **kwargs)
                            return True
                        except NotImplementedError as _e: e = _e
                        except TypeError as _e: e = _e 
                        except: return False
                        raise e
                    _chunk_first = _chunk.content[0]
                    if str_is_quotes(_chunk.content): # Is this a string?
                        _tokens.append(cmd_ass._TokenString(_chunk))
                    elif _chunk_first == '.': # Is this a label (lv1, lv2, ...) reference?
                        _tokens.append(cmd_ass._TokenLabelRef(_chunk, labelscope, self.__case))
                    elif _chunk_first == '$': # Is this a 6502-style hex number?
                        _tokens.append(cmd_ass._TokenNumber(_chunk))
                    elif _chunk_first == '%': # Is this a 6502-style bin number?
                        _tokens.append(cmd_ass._TokenNumber(_chunk))
                    elif _chunk_first.isdigit(): # Is this a number?
                        _tokens.append(cmd_ass._TokenNumber(_chunk))
                    elif str_is_word(_chunk.content):
                        if _try_create(cmd_ass._TokenRegRef.create, _chunk): # Is this a register reference?
                            _tokens.append(_tokenptr.value)
                        elif _try_create(cmd_ass._TokenOperator.create, _chunk): # Is this an operator?
                            _tokens.append(_tokenptr.value)
                        else: # Consider it a label reference
                            _tokens.append(cmd_ass._TokenLabelRef(_chunk, labelscope, self.__case))
                    elif _try_create(cmd_ass._TokenParOpen.create, _chunk): # Is this an open parenthesis?
                        _tokens.append(_tokenptr.value)
                    elif _try_create(cmd_ass._TokenParClose.create, _chunk): # Is this a close parenthesis?
                        _tokens.append(_tokenptr.value)
                    elif _try_create(cmd_ass._TokenImmediate.create, _chunk): # Is this an immediate indicator?
                        _tokens.append(_tokenptr.value)
                    elif _try_create(cmd_ass._TokenDelimiter.create, _chunk): # Is this a delimiter?
                        _tokens.append(_tokenptr.value)
                    elif _try_create(cmd_ass._TokenOperator.create, _chunk): # Is this an operator?
                        _tokens.append(_tokenptr.value)
                    else: # Invalid
                        raise cmd_ass._error(_chunk, f"Unexpected: {_chunk.content}")
                # Add line
                self.__p0_tokengroups.append(cmd_ass._TokenBlock.blockify(_tokens))

        #endregion
        
        #region run

        @classmethod
        def run(cls, cmd:'cmd_ass', lines:list[list[assutil.SrcChunk]]):
            instance = cls(cmd, lines)
            instance.__phase0()
            # Test
            # for _tokens in instance.__p0_tokengroups:
            #     print(cmd_ass._echo_tokens(_tokens))

        #endregion

    #endregion

    #region cli

    @property
    def _desc(self) -> None|str:
        return "Assembles a ROM (NOTE: Bank switching not currently supported)"
    
    __source = cli.CLIRequiredDef(\
        name = "source",\
        desc = "Source file (*.asm)",\
        parse = cliutil.ParseUtil.to_path)
    
    __output = cli.CLIOptionWArgDef(\
        name = "output",\
        short = 'o',\
        desc = "Output file (*.a26;*.bin)",\
        parse = cliutil.ParseUtil.to_path)
    
    __intmd = cli.CLIOptionWArgDef(\
        name = "intmd",\
        desc = "Path of an intermediate file (*.asm); this is basically an expanded version of the source file",\
        parse = cliutil.ParseUtil.to_path)
    
    __flags = cli.CLIOptionWArgDef(\
        name = "flags",\
        short = 'f',\
        desc = "Flags (separate with comma)",\
        parse = cliutil.ParseUtil.to_set,\
        default = set())
    
    __case = cli.CLIOptionFlagDef(\
        name = "case",\
        desc = "Require case-sensitive labels and macros")

    #endregion

    #region helper methods

    @classmethod
    def _error(cls, chunk:None|assutil.SrcChunk|list[assutil.SrcChunk], message):
        def __error(chunk:assutil.SrcChunk):
            nonlocal message
            return cliutil.CommandError(f"{chunk.path}\nLine: {chunk.linenumber}\n{message}")
        if chunk is None: return cliutil.CommandError(message)
        if isinstance(chunk, assutil.SrcChunk): return __error(chunk)   
        if len(chunk) > 0: return __error(chunk[0])
        return cliutil.CommandError(message)
    
    @classmethod
    def _get_str(cls, chunk:assutil.SrcChunk):
        def _error():
            nonlocal chunk
            return cmd_ass._error(chunk, "Invalid string") 
        # Make sure chunk has room for two quotation marks
        if len(chunk.content) < 2: raise _error()
        # Make sure chunk begins with quotation mark
        if ord(chunk.content[0]) != Chr.STR.value: raise _error()
        # Make sure chunk ends with quotation mark
        last = len(chunk.content) - 1
        if ord(chunk.content[last]) != Chr.STR.value: raise _error()
        # Success!!!
        return chunk.content[1:last]
    
    @classmethod
    def _get_word(cls, chunk:assutil.SrcChunk):
        def _unexpected(char:str):
            nonlocal chunk
            return cls._error(chunk, f"Unexpected character: '{char}'")
        if len(chunk.content) == 0: raise cls._error(chunk, "Word cannot be empty.")
        # Make sure word does not start with a number
        _first = ord(chunk.content[0])
        if _first >= 0x30 and _first <= 0x39: raise _unexpected(chr(_first))
        # Make sure all characters are word characters
        for _c in chunk.content:
            if not chr_is_word(ord(_c)): raise _unexpected(_c)
        # Success!!!
        return chunk.content
    
    @classmethod
    def _get_path(cls, chunk:assutil.SrcChunk):
        rawpath = cls._get_str(chunk)
        try: return Path(rawpath)
        except Exception as _e: e = cls._error(chunk, _e)
        raise e

    @classmethod
    def _echo_tokens(cls, tokens:'cmd_ass._Token|Sequence[cmd_ass._Token]'):
        if isinstance(tokens, cmd_ass._Token):
            return str(tokens)
        with StringIO() as s:
            for _i in range(len(tokens)):
                _token = tokens[_i]
                s.write(str(_token))
                if (_i + 1) == len(tokens):
                    continue
                if isinstance(_token, cmd_ass._TokenCommand):
                    s.write(' ')
                elif isinstance(_token, cmd_ass._TokenInstruct):
                    s.write(' ')
                elif not (_token.issym or tokens[_i + 1].issym):
                    s.write(' ')
            return s.getvalue()

    #endregion

    #region methods

    def _main(self):
        try: 
            source = cast(Path, self.source) # type: ignore
            # Preprocess
            preprocessed = self.__Preprocessor.run(self, source)
            self.__Assembler.run(self, preprocessed)
            # Success!!!
            return 0
        except cliutil.CommandError as _e:
            print("ERROR", file = sys.stderr)
            print(_e, file = sys.stderr)
            return 1

    #endregion