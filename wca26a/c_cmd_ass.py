__all__ = ['cmd_ass']

import sys

from enum import Enum
from io import StringIO
from typing import cast
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
    OPAR = ord('(')
    CPAR = ord(')')
    IMM = ord('#')
    SEP = ord(',')
    REM = ord(';')

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

class cmd_ass(cli.CLICommand):

    #region preprocessor

    class Preprocessor:

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
                _dirname = _line[0].content
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
                _macro = _chunk.content if self.__case else _chunk.content.lower()
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

        def __p1_dir_include(self, line:list[assutil.SrcChunk]):
            if self.__p1_if_level > self.__p1_if_true: return
            self.__raise_if_ne(line, 1)
            path = help.PathUtil.absolute(cmd_ass._get_path(line[1]), self.__directory)
            for _line in self.__run(self.__cmd, path, self.__macros):
                self.__p1_chunksbyline.append(_line)

        def __p1_dir_define(self, line:list[assutil.SrcChunk]):
            if self.__p1_if_level > self.__p1_if_true: return
            self.__raise_if_lt(line, 1)
            # Get macro name
            macro = cmd_ass._get_word(line[1])
            if not self.__case: macro = macro.lower()
            # Add macro
            self.__macros[macro] = self.__p1_expandmacros(line[2:])
        
        def __p1_dir_undef(self, line:list[assutil.SrcChunk]):
            if self.__p1_if_level > self.__p1_if_true: return
            self.__raise_if_ne(line, 1)
            arg_macro = line[1]
            # Get macro name
            macro = cmd_ass._get_word(arg_macro)
            if not self.__case: macro = macro.lower()
            self.__raise_if_ndef(arg_macro, macro)
            # Remove macro
            self.__macros.pop(macro)

        def __p1_dir_ifdef(self, line:list[assutil.SrcChunk]):
            if self.__p1_if_level == self.__p1_if_true and self.__p1__dir_ifdef(line, False):
                self.__p1_if_true += 1
            self.__p1_if_level += 1

        def __p1_dir_ifndef(self, line:list[assutil.SrcChunk]):
            if self.__p1_if_level == self.__p1_if_true and self.__p1__dir_ifdef(line, True):
                self.__p1_if_true += 1
            self.__p1_if_level += 1

        def __p1_dir_if(self, line:list[assutil.SrcChunk]):
            if self.__p1_if_level == self.__p1_if_true and self.__p1__dir_if(line):
                self.__p1_if_true += 1
            self.__p1_if_level += 1

        def __p1_dir_elif(self, line:list[assutil.SrcChunk]):
            self.__p1_raise_if_noblock(line)
            if (self.__p1_if_level - 1) > self.__p1_if_true: return
            # Was the last block true?
            if self.__p1_if_level == self.__p1_if_true:
                self.__p1_if_true -= 1
                self.__p1_if_ignore = True
            # No! Shall we execute the 'elif' block?
            elif (not self.__p1_if_ignore) and self.__p1__dir_if(line):
                self.__p1_if_true = self.__p1_if_level

        def __p1_dir_else(self, line:list[assutil.SrcChunk]):
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

        def __p1_dir_endif(self, line:list[assutil.SrcChunk]):
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
            if not self.__case: macro = macro.lower()
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
            if not self.__case: macro = macro.lower()
            self.__raise_if_ndef(arg_macro, macro)
            macro_value = self.__macros[macro]
            # Get operator
            operator = cmd_ass._get_word(arg_operator)
            # Check condition
            match operator.lower():
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
            for _flag in cmd.flags: macros[_flag if self.case else _flag.lower()] = [] # type: ignore
            return cls.__run(cmd, path, macros)

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

    #endregion

    #region methods

    def _main(self):
        try: 
            source = cast(Path, self.source) # type: ignore
            output = cast(None|Path, self.output) # type: ignore
            intmd = cast(None|Path, self.intmd) # type: ignore
            flags = cast(set[str], self.flags) # type: ignore
            case = cast(bool, self.case) # type: ignore
            # resolve
            if output is None: output = source.with_suffix('.a26')
            # Print
            print(f"Source:            {source}")
            print(f"Output:            {output}")
            print(f"Intermediate:      {intmd}")
            print(f"Flags:             {flags}")
            print(f"Case-Sensitive:    {case}")
            # Open source
            for _line in self.Preprocessor.run(self, source):
                for _chunk in _line: print(_chunk.content, end = ' ')
                print()
            # Success!!!
            return 0
        except cliutil.CommandError as _e:
            print("ERROR", file = sys.stderr)
            print(_e, file = sys.stderr)
            return 1

    #endregion