__all__ = ['cmd_ass']

import math
import sys

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import auto, Enum
from io import StringIO
from pathlib import Path
from typing import cast, Callable

import assutil
import cli
import cliutil
import col
import help

#region chr

CHR_PRE = '@'
CHR_ASS_PRE = '!'
CHR_ASS_POST = '?'

def chr_is_word(c:str):
    return c.isdigit() or c.isalpha() or c == '_'

#endregion

#region str

def str_is_quotes(s:str):
    return len(s) >= 2 and s[0] == '"' and s[-1] == '"'

def str_is_word(s:str):
    if len(s) == 0: return False
    if s[0].isdigit(): return False
    for c in s:
        if chr_is_word(c): continue
        return False
    return True

#endregion

#region err

def err(chunk:None|assutil.SrcChunk|list[assutil.SrcChunk], message):
    def _err(chunk:assutil.SrcChunk):
        nonlocal message
        return cliutil.CommandError(f"{chunk.path}\nLine: {chunk.linenumber}\n{message}")
    if chunk is None: return cliutil.CommandError(message)
    if isinstance(chunk, assutil.SrcChunk): return _err(chunk)   
    if len(chunk) > 0: return _err(chunk[0])
    return cliutil.CommandError(message)

def raise_if_ne(args:list[assutil.SrcChunk], req:int):
    if (len(args) - 1) == req: return
    raise err(args, f"Expected only {req} argument(s).")

def raise_if_lt(args:list[assutil.SrcChunk], req:int):
    if (len(args) - 1) >= req: return
    raise err(args, f"Expected at least {req} argument(s).")

#endregion

#region get

def get_str(chunk:assutil.SrcChunk):
    if not str_is_quotes(chunk.content):
        raise err(chunk, "Invalid string")
    return chunk.content[1:len(chunk.content) - 1]

def get_word(chunk:assutil.SrcChunk):
    # Is this a word?
    if str_is_word(chunk.content): return chunk.content
    # No! Is it empty?
    if len(chunk.content) == 0:
        raise err(chunk, "Word cannot be empty.")
    # No! Does it start with a number?
    if chunk.content[0].isdigit():
        raise err(chunk, "First character of word cannot be a  digit.")
    # No! Look for the unexpected character.
    for _c in chunk.content:
        if chr_is_word(_c): continue
        raise err(chunk, f"Unexpected character: '{_c}'")
    raise Exception("Unexpected exception")

def get_path(chunk:assutil.SrcChunk):
    rawpath = get_str(chunk)
    try: return Path(rawpath)
    except Exception as _e: e = err(chunk, _e)
    raise e

#endregion

#region echo

def echo_tokens(tokens:'_Token|Sequence[_Token]'):
    if isinstance(tokens, _Token):
        return str(tokens)
    with StringIO() as s:
        for _i in range(len(tokens)):
            _token = tokens[_i]
            s.write(str(_token))
            if (_i + 1) == len(tokens):
                continue
            if isinstance(_token, _Token_CmdInsHead):
                s.write(' ')
            elif not (_token.issym or tokens[_i + 1].issym):
                s.write(' ')
        return s.getvalue()

#endregion

#region Token

class _Token:

    #region init

    def __init__(self, src:assutil.SrcChunk):
        self.__src = src

    @classmethod
    def create(cls, *args, **kwargs) -> '_Token':
        raise NotImplementedError("create has not been implemented.")

    #endregion

    #region properties

    @property
    def src(self): return self.__src

    @property
    def issym(self): return bool(False)

    #endregion

class _Token_CmdInsHead(_Token):
    """ Command or instruction """
    pass

class _Token_Symbol(_Token):

    #region init

    def __init__(self, src:assutil.SrcChunk):
        super().__init__(src)
        if src.content != self.symbol: raise err(src, f"Expected {self.symbol}")

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
            labels:dict[str, '_TokenLabelDec'], scope:list[str], sensitive:bool):
        """ NOTE: label and scope may be modified """
        super().__init__(src)
        # Make sure it ends with a colon
        if not src.content.endswith(':'):
            raise err(src, "Label declaration must end with a colon.")
        # Extract level and name
        self.__level, self.__name, self.__path = _TokenLabelRef.extract_labelinfo(
            src.sub(end = len(src.content) - 1), scope, sensitive)
        if self.__path in labels:
            raise err(src, f"{self.__path} has already been defined.")
        # Update labels and scopes (must be done AFTER ensuring label is valid)
        labels[self.__path] = self
        while len(scope) > self.__level: scope.pop()
        scope.append(self.__name)

    @classmethod
    def create(cls, *args, **kwargs) -> '_Token':
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

class _TokenCommand(_Token_CmdInsHead):

    #region init

    def __init__(self, src:assutil.SrcChunk):
        super().__init__(src)
        # Determine type
        if src.content.startswith(CHR_ASS_PRE): self.__post = False
        elif src.content.startswith(CHR_ASS_POST): self.__post = True
        else: raise err(src, f"Assembler command must begin with '{CHR_ASS_PRE}' or '{CHR_ASS_POST}'.")
        # Extract name
        self.__name = get_word(src.sub(1))

    @classmethod
    def create(cls, *args, **kwargs) -> '_Token':
        return cls(*args, **kwargs)
    
    #endregion

    #region operators

    def __str__(self): return (CHR_ASS_POST if self.__post else CHR_ASS_PRE) + self.__name

    #endregion

    #region properties

    @property
    def name(self): return self.__name

    @property
    def post(self): return self.__post

    #endregion

class _TokenInstruct(_Token_CmdInsHead):

    #region init

    def __init__(self, src:assutil.SrcChunk):
        super().__init__(src)
        self.__name = get_word(src).upper()

    @classmethod
    def create(cls, *args, **kwargs) -> '_Token':
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
            raise err(src, "A string must be enclosed with double quotation marks.")
        self.__value = src.content[1:-1]

    #endregion

    #region operators

    def __str__(self): return '"' + self.__value + '"'

    #endregion

    #region properties

    @property
    def value(self):
        """ String value (excluding opening and closing quotation marks)"""
        return self.__value

    #endregion

class _TokenLabelRef(_Token):

    #region init

    def __init__(self, src:assutil.SrcChunk, scope:Sequence[str], sensitive:bool):
        super().__init__(src)
        self.__level, self.__name, self.__path = self.extract_labelinfo(src, scope, sensitive)

    @classmethod
    def create(cls, *args, **kwargs) -> '_Token':
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
            raise err(src, "Label name cannot be empty.")
        if level > len(scope):
            raise err(src, "Invalid scope level")
        # Extract name
        name = get_word(src.sub(level))
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
    def create(cls, *args, **kwargs) -> '_Token':
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
            except: raise err(src, f"{src.content} is not a valid numerical value.")
            # Check range
            if raw < 0 or raw > 0xFFFF:
                raise err(src, f"{raw} is out of range.")
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
            raise err(src, f"{self.__reg} is not a valid register.")

    @classmethod
    def create(cls, *args, **kwargs) -> '_Token':
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

class _TokenOperator_Type(Enum):
    CAST_B8 = auto()
    CAST_B16 = auto()
    ADD = auto()
    SUBTRACT = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    MODULO = auto()
    BIT_AND = auto()
    BIT_OR = auto()
    BIT_XOR = auto()
    BIT_INV = auto()
    BIT_SHIFT_L = auto()
    BIT_SHIFT_R = auto()
    BYTE_LO = auto()
    BYTE_HI = auto()

class _TokenOperator_TypeInfo:
    
    #region P

    @dataclass(frozen = True)
    class __P:
        type:_TokenOperator_Type
        sym:str
        unary:bool
        order:int

    #endregion

    #region init

    def __init__(self, p:__P):
        self.__p = p

    @classmethod
    def get(cls):
        items:list[_TokenOperator_TypeInfo] = []
        # Unary operations are done first
        items.append(cls(cls.__P(_TokenOperator_Type.CAST_B8, 'b8', True, 0)))
        items.append(cls(cls.__P(_TokenOperator_Type.CAST_B16, 'b16', True, 0)))
        items.append(cls(cls.__P(_TokenOperator_Type.BYTE_LO, '<', True, 0)))
        items.append(cls(cls.__P(_TokenOperator_Type.BYTE_HI, '>', True, 0)))
        items.append(cls(cls.__P(_TokenOperator_Type.BIT_INV, '~', True, 0)))
        # Followed by multiplication, division, and modulus
        items.append(cls(cls.__P(_TokenOperator_Type.MULTIPLY, '*', False, 1)))
        items.append(cls(cls.__P(_TokenOperator_Type.DIVIDE, '/', False, 1)))
        items.append(cls(cls.__P(_TokenOperator_Type.MODULO, '%', False, 1)))
        # Followed by addition and subtraction
        items.append(cls(cls.__P(_TokenOperator_Type.ADD, '+', False, 2)))
        items.append(cls(cls.__P(_TokenOperator_Type.SUBTRACT, '-', False, 2)))
        # Followed by bit shift
        items.append(cls(cls.__P(_TokenOperator_Type.BIT_SHIFT_L, 'lshft', False, 3)))
        items.append(cls(cls.__P(_TokenOperator_Type.BIT_SHIFT_R, 'rshft', False, 3)))
        # Followed by bitwise AND
        items.append(cls(cls.__P(_TokenOperator_Type.BIT_AND, '&', False, 4)))
        # Followed by bitwise XOR
        items.append(cls(cls.__P(_TokenOperator_Type.BIT_XOR, '^', False, 5)))
        # Followed by bitwise OR
        items.append(cls(cls.__P(_TokenOperator_Type.BIT_OR, '|', False, 6)))
        # Success!!!
        return col.ADict(items, lambda _item: _item.type)

    #endregion

    #region properties

    @property
    def type(self): return self.__p.type

    @property
    def sym(self): return self.__p.sym

    @property
    def unary(self): return self.__p.unary

    @property
    def order(self): return self.__p.order

    #endregion

class _TokenOperator(_Token):

    #region init

    def __init__(self, src:assutil.SrcChunk):
        super().__init__(src)
        s = src.content.upper()
        if not (s in self.KEYWORDS):
            raise err(src, f"{s} is not a valid operator.")
        self.__src = src
        self.__type = self.KEYWORDS[s]

    @classmethod
    def create(cls, *args, **kwargs) -> '_Token':
        return cls(*args, **kwargs)
    
    #endregion

    #region const

    @staticmethod
    def __get_types():
        # Get types
        types = _TokenOperator_TypeInfo.get()
        # Group by order
        types_group_order:list[col.RoList[_TokenOperator_TypeInfo]] = []
        if len(types):
            _sorted = sorted(types, key = lambda _t: _t.order)
            _first = _sorted[0].order
            _last = _sorted[-1].order
            _group = []
            _pos = 0
            for _i in range(_first, _last + 1):
                # Gets items in group
                while _pos < len(_sorted):
                    _op = _sorted[_pos]
                    if _op.order != _i: break
                    _group.append(_op)
                    _pos += 1
                # Make sure group is not empty
                if len(_group) == 0: continue
                # Add group
                types_group_order.append(col.RoList(_group))
                _group = [] # Create new group
        # Success!!!
        return types, col.RoList[col.RoList[_TokenOperator_TypeInfo]](types_group_order)

    TYPES, TYPES_GROUP_ORDER = __get_types()

    KEYWORDS = col.RoDict[str, _TokenOperator_TypeInfo]({\
        'B8': TYPES[_TokenOperator_Type.CAST_B8],\
        'B16': TYPES[_TokenOperator_Type.CAST_B16],\
        '+': TYPES[_TokenOperator_Type.ADD],\
        '-': TYPES[_TokenOperator_Type.SUBTRACT],\
        '*': TYPES[_TokenOperator_Type.MULTIPLY],\
        '/': TYPES[_TokenOperator_Type.DIVIDE],\
        'MOD': TYPES[_TokenOperator_Type.MODULO],\
        '&': TYPES[_TokenOperator_Type.BIT_AND],\
        '|': TYPES[_TokenOperator_Type.BIT_OR],\
        '^': TYPES[_TokenOperator_Type.BIT_XOR],\
        '~': TYPES[_TokenOperator_Type.BIT_INV],\
        'LSHFT': TYPES[_TokenOperator_Type.BIT_SHIFT_L],\
        'RSHFT': TYPES[_TokenOperator_Type.BIT_SHIFT_R],\
        '<': TYPES[_TokenOperator_Type.BYTE_LO],\
        '>': TYPES[_TokenOperator_Type.BYTE_HI],})

    #endregion

    #region operators

    def __str__(self): return self.__src.content

    #endregion

    #region properties

    @property
    def type(self):
        """ Operator type """
        return self.__type

    #endregion

class _TokenParOpen(_Token):

    #region init

    def __init__(self, src:assutil.SrcChunk):
        super().__init__(src)
        if src.content != '(':
            raise err(src, "Expected (")
        self.__symbol = src.content

    @classmethod
    def create(cls, *args, **kwargs) -> '_Token':
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
        if src.content != ')':
            raise err(src, "Expected )")
        self.__symbol = src.content

    @classmethod
    def create(cls, *args, **kwargs) -> '_Token':
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
    def create(cls, *args, **kwargs) -> '_Token':
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
    def create(cls, *args, **kwargs) -> '_Token':
        return cls(*args, **kwargs)
    
    #endregion

    #region properties

    @property
    def symbol(self): return ','

    #endregion

#endregion

#region OType, OArgTypes, OValue

#region OType

class _OType:

    #region Name

    class Name(Enum):
        NONE = auto()
        B8 = auto()
        B16 = auto()
        STR = auto()
        REG = auto()
        TUPLE = auto()

    #endregion

    #region init

    def __init__(self, name:Name):
        self.__name = name

    #endregion

    #region operators

    def __eq__(self, other): return self.__eq(other)
    def __ne__(self, other): return not self.__eq(other)
    def __hash__(self): return hash(self.__name)

    #endregion

    #region properties

    @property
    def name(self): return self.__name

    #endregion

    #region helper methods

    def __eq(self, other):
        if not isinstance(other, _OType): return False
        if not type(self) == type(other): return False
        return self._eq(other)
    
    def _eq(self, other:'_OType'):
        return self.__name == other.__name

    #endregion

    #region methods

    def echo(self, obj:object) -> str:
        raise NotImplementedError("echo has not been implemented.")

    #endregion

class _OTypeNONE(_OType):

    #region init

    def __init__(self):
        super().__init__(_OType.Name.NONE)

    #endregion

    #region methods

    @classmethod
    def cast(cls, obj:object): return cast(None, obj)

    def echo(self, obj:object): return ""

    #endregion

class _OTypeB8(_OType):

    #region init

    def __init__(self):
        super().__init__(_OType.Name.B8)

    #endregion

    #region methods

    @classmethod
    def cast(cls, obj:object): return cast(int, obj)

    @classmethod
    def fixvalue(cls, value:int):
        return value - math.floor(value / 0x100) * 0x100

    def echo(self, obj:object): return f"${obj:02X}"

    #endregion

class _OTypeB16(_OType):

    #region init

    def __init__(self):
        super().__init__(_OType.Name.B16)

    #endregion

    #region methods

    @classmethod
    def cast(cls, obj:object): return cast(int, obj)

    @classmethod
    def fixvalue(cls, value:int):
        return value - math.floor(value / 0x10000) * 0x10000

    def echo(self, obj:object): return f"${obj:04X}"

    #endregion

class _OTypeSTR(_OType):

    #region init

    def __init__(self):
        super().__init__(_OType.Name.STR)

    #endregion

    #region methods

    @classmethod
    def cast(cls, obj:object): return cast(str, obj)

    def echo(self, obj:object): return (f"\"{obj}\"")

    #endregion

class _OTypeREG(_OType):

    #region init

    def __init__(self):
        super().__init__(_OType.Name.REG)

    #endregion

    #region methods

    @classmethod
    def cast(cls, obj:object): return cast(str, obj)

    def echo(self, obj:object): return str(obj)

    #endregion

class _OTypeTUPLE(_OType):

    #region init

    def __init__(self, types:Iterable[_OType]):
        super().__init__(_OType.Name.TUPLE)
        self.__types = tuple(types)

    #endregion

    #region operators

    def __len__(self):
        return len(self.__types)
    
    def __getitem__(self, index:int):
        try:
            return self.__types[index]
        except:
            if index >= 0 and index < len(self.__types):
                raise
        raise IndexError("Index is out of range.")
    
    def __iter__(self):
        for _item in self.__types:
            yield _item
    
    def __contains__(self, item):
        return item in self.__types

    #endregion

    #region helper methods

    def _eq(self, other:_OType):
        if not super()._eq(other): return False
        if not isinstance(other, _OTypeTUPLE): return False
        if len(self.__types) != len(other.__types): return False
        for _i in range(len(self.__types)):
            if self.__types[_i] != other.__types[_i]: return False
        return True
    
    #endregion

    #region methods

    @classmethod
    def cast(cls, obj:object): return cast(tuple, obj)

    def echo(self, obj:object):
        assert isinstance(obj, tuple)
        with StringIO() as s:
            s.write('(')
            for _i in range(len(self.__types)):
                if _i > 0: s.write(',')
                s.write(self.__types[_i].echo(obj[_i]))
            s.write(')')
            return s.getvalue()

    #endregion

#endregion

#region OArgTypes

class _OArgTypes:

    #region init

    def __init__(self, types:Iterable[_OType.Name]):
        self.__types:list[_OType.Name] = [_t for _t in types]

    #endregion

    #region operators

    def __str__(self):
        with StringIO() as s:
            for _i in range(len(self.__types)):
                if _i > 0: s.write(', ')
                s.write(f"{self.__types[_i].name}")
            return s.getvalue()

    def __eq__(self, other): return self.__eq(other)
    def __ne__(self, other): return not self.__eq(other)
    def __hash__(self): return len(self.__types)

    def __len__(self):
        return len(self.__types)

    def __getitem__(self, index:int):
        try:
            return self.__types[index]
        except:
            if index >= 0 and index < len(self.__types): raise
        raise IndexError("Index is out of range.")
    
    def __iter__(self):
        for _type in self.__types:
            yield _type

    #endregion

    #region helper methods

    def __eq(self, other):
        if not isinstance(other, _OArgTypes): return False
        if len(self.__types) != len(other.__types): return False
        for _i in range(len(self.__types)):
            if self.__types[_i] != other.__types[_i]: return False
        return True

    #endregion

#endregion

#region OValue

class _OValue:

    #region properties

    @property
    def src(self) -> assutil.SrcChunk:
        raise NotImplementedError("src has not been implemented.")

    @property
    def type(self) -> _OType:
        raise NotImplementedError("type has not been implemented.")

    #endregion

    #region methods

    def echo_format(self) -> str:
        raise NotImplementedError("echo_format has not been implemented.")

    def get_value(self) -> object:
        raise NotImplementedError("get_value has not been implemented.")

    #endregion

class _OValueLiteral(_OValue):

    #region init

    def __init__(self, token:_TokenNumber|_TokenString|_TokenRegRef):
        self.__src = token.src
        if isinstance(token, _TokenNumber):
            if token.is16:
                self.__type = _OTypeB16()
                self.__value = _OTypeB16.fixvalue(token.value)
            else:
                self.__type = _OTypeB8()
                self.__value = _OTypeB8.fixvalue(token.value)
        elif isinstance(token, _TokenString):
            self.__type = _OTypeSTR()
            self.__value = token.value
        else:
            self.__type = _OTypeREG()
            self.__value = token.reg

    #endregion

    #region properties

    @property
    def src(self): return self.__src

    @property
    def type(self): return self.__type

    #endregion

    #region methods

    def echo_format(self) -> str:
        if isinstance(self.__type, _OTypeB8):
            return f"${self.__value:02X}"
        if isinstance(self.__type, _OTypeB16):
            return f"${self.__value:04X}"
        return str(self.__value)

    def get_value(self): return self.__value

    #endregion

class _OValueLabelRef(_OValue):

    #region init

    def __init__(self, token:_TokenLabelRef, labeldict:col.RoDict[str, int]):
        self.__src = token.src
        self.__type = _OTypeB16()
        self.__path = token.path
        self.__labeldict = labeldict

    #endregion

    #region properties

    @property
    def src(self): return self.__src

    @property
    def type(self): return self.__type

    #endregion

    #region methods

    def echo_format(self) -> str:
        return str(self.__path)

    def get_value(self):
        if self.__path in self.__labeldict: return self.__labeldict[self.__path]
        raise err(self.__src, f"The label {self.__path} has not been declared.")

    #endregion

class _OValueInPar(_OValue):

    #region init

    def __init__(self, src:assutil.SrcChunk, input:_OValue|Iterable[_OValue]):
        self.__src = src
        if isinstance(input, _OValue):
            self.__type = input.type
            self.__input = input
        else:
            self.__type = _OTypeTUPLE(_i.type for _i in input)
            self.__input = tuple(input)

    #endregion

    #region properties

    @property
    def src(self): return self.__src

    @property
    def type(self): return self.__type

    @property
    def input(self): return self.__input

    #endregion

    #region methods

    def echo_format(self) -> str:
        with StringIO() as s:
            s.write('(')
            if isinstance(self.__input, tuple):
                for _i in range(len(self.__input)):
                    if _i > 0: s.write(',')
                    s.write(self.__input[_i].echo_format())
            else: s.write(self.__input.echo_format())
            s.write(')')
            return s.getvalue()

    def get_value(self):
        if not isinstance(self.__input, tuple):
            return self.__input.get_value()
        return tuple(_i.get_value() for _i in self.__input)

    #endregion

class _OValueOperation(_OValue):

    #region OpAndTypes

    class _OpAndTypes:

        #region init

        def __init__(self, operator:_TokenOperator_Type, types:_OArgTypes):
            self.__operator = operator
            self.__types = types

        #endregion

        #region operators

        def __str__(self):
            return f"{self.__operator} {self.__types}"

        def __eq__(self, other): return self.__eq(other)
        def __ne__(self, other): return not self.__eq(other)
        def __hash__(self): return hash(self.__operator)

        #endregion

        #region properties

        @property
        def operator(self): return self.__operator
        
        @property
        def types(self): return self.__types

        #endregion

        #region helper methods

        def __eq(self, other):
            if not isinstance(other, _OValueOperation._OpAndTypes): return False
            return self.__operator == other.__operator and self.__types == other.__types

        #endregion

    #endregion

    #region Func

    @dataclass(frozen = True)
    class __Func:
        opandtypes:'_OValueOperation._OpAndTypes'
        func:object
        rtype:object

    #endregion

    #region init

    def __init__(self, operator:_TokenOperator, inputs:Iterable[_OValue]):
        self.__operator = operator
        self.__inputs = tuple(inputs)
        self.__func = self.__ops_get(self.__operator, self.__inputs)
        self.__type = self.__func.rtype(self) # type: ignore
    
    #endregion

    #region properties

    @property
    def operator(self): return self.__operator

    @property
    def inputs(self): return self.__inputs

    @property
    def src(self): return self.__operator.src

    @property
    def type(self): return self.__type

    #endregion

    #region methods

    def echo_format(self) -> str:
        opname = self.__operator.type.sym
        if len(self.__inputs) == 1:
            return f"{opname} {self.__inputs[0].echo_format()}"
        if len(self.__inputs) == 2:
            return f"{self.__inputs[0].echo_format()} {opname} {self.__inputs[1].echo_format()}"
        with StringIO() as s:
            s.write(opname)
            for _i in self.__inputs:
                s.write(f" {_i.echo_format()}")
            return s.getvalue()

    def get_value(self) -> object:
        return self.__func.func(self) # type: ignore

    #endregion
    
    #region ops

    @classmethod
    def __ops_get(cls, operator:_TokenOperator, inputs:Sequence[_OValue]):
        ATTRNAME = '__ops'
        CLASS_OP = '_op_'
        CLASS_IN = '_in_'
        # Make sure dictionary is initialized
        attr = cast(None|col.ADict[_OValueOperation._OpAndTypes, _OValueOperation.__Func], getattr(cls, ATTRNAME, None))
        if attr is None:
            # Create dictionary
            _funcs:list[_OValueOperation.__Func] = []
            def extract_funcs(t:type):
                nonlocal _funcs
                # Make sure class name prefix is valid
                if not t.__name__.startswith(CLASS_OP): return
                # Extract operator type
                optype = _TokenOperator_Type[t.__name__[len(CLASS_OP):]]
                # Extract operations
                for _name in dir(t):
                    _type = getattr(t, _name)
                    if not callable(_type): continue
                    if not isinstance(_type, type): continue
                    if not _type.__name__.startswith(CLASS_IN): continue
                    # Extract input types
                    _input = tuple(_OType.Name[_itype] for _itype in _type.__name__[len(CLASS_IN):].split('_'))
                    _opandtypes = _OValueOperation._OpAndTypes(optype, _OArgTypes(_input))
                    # Extract functions
                    _func = getattr(_type, 'func').__call__
                    _rtype = getattr(_type, 'rtype').__call__
                    # Add to dictionary
                    _funcs.append(_OValueOperation.__Func(_opandtypes, _func, _rtype))
            for _name in dir(cls):
                _type = getattr(cls, _name)
                if not callable(_type): continue
                if not isinstance(_type, type): continue
                extract_funcs(_type)
            # Set variable
            attr = col.ADict[_OValueOperation._OpAndTypes, _OValueOperation.__Func](_funcs, lambda _f: _f.opandtypes)
            setattr(cls, ATTRNAME, attr)
        # Look for matching functions
        opandtypes = _OValueOperation._OpAndTypes(operator.type.type, _OArgTypes(_i.type.name for _i in inputs))
        if opandtypes in attr: return attr[opandtypes]
        raise err(operator.src, "Type mismatch")

    class _op_CAST_B8:

        class _in_B8:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                return self.inputs[0].get_value()
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB8()
            
        class _in_B16:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                return _OTypeB16.cast(self.inputs[0].get_value()) & 0xFF
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB8()
    
    class _op_CAST_B16:

        class _in_B8:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                return self.inputs[0].get_value()
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB16()
            
        class _in_B16:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                return self.inputs[0].get_value()
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB16()

    class _op_ADD:

        class _in_B8_B8:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB8.cast(self.inputs[0].get_value())
                b = _OTypeB8.cast(self.inputs[1].get_value())
                return _OTypeB8.fixvalue(a + b)
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB8()
            
        class _in_B16_B16:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB16.cast(self.inputs[0].get_value())
                b = _OTypeB16.cast(self.inputs[1].get_value())
                return _OTypeB16.fixvalue(a + b)
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB16()
            
        class _in_STR_STR:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeSTR.cast(self.inputs[0].get_value())
                b = _OTypeSTR.cast(self.inputs[1].get_value())
                return a + b
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeSTR()
            
        class _in_TUPLE_TUPLE:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeTUPLE.cast(self.inputs[0].get_value())
                b = _OTypeTUPLE.cast(self.inputs[1].get_value())
                return a + b
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                a = cast(_OTypeTUPLE, self.inputs[0].type)
                b = cast(_OTypeTUPLE, self.inputs[1].type)
                return _OTypeTUPLE([_i for _i in a] + [_i for _i in b])
    
    class _op_SUBTRACT:

        class _in_B8_B8:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB8.cast(self.inputs[0].get_value())
                b = _OTypeB8.cast(self.inputs[1].get_value())
                return _OTypeB8.fixvalue(a - b)
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB8()
            
        class _in_B16_B16:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB16.cast(self.inputs[0].get_value())
                b = _OTypeB16.cast(self.inputs[1].get_value())
                return _OTypeB16.fixvalue(a - b)
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB16()
    
    class _op_MULTIPLY:

        class _in_B8_B8:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB8.cast(self.inputs[0].get_value())
                b = _OTypeB8.cast(self.inputs[1].get_value())
                return _OTypeB8.fixvalue(a * b)
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB8()
            
        class _in_B16_B16:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB16.cast(self.inputs[0].get_value())
                b = _OTypeB16.cast(self.inputs[1].get_value())
                return _OTypeB16.fixvalue(a * b)
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB16()
            
        class _in_STR_B8:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeSTR.cast(self.inputs[0].get_value())
                b = _OTypeB8.cast(self.inputs[1].get_value())
                return a * b
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeSTR()
            
        class _in_STR_B16:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeSTR.cast(self.inputs[0].get_value())
                b = _OTypeB16.cast(self.inputs[1].get_value())
                return a * b
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeSTR()
    
    class _op_DIVIDE:

        class _in_B8_B8:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB8.cast(self.inputs[0].get_value())
                b = _OTypeB8.cast(self.inputs[1].get_value())
                if b == 0: raise err(self.operator.src, "Division by zero.")
                return a // b
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB8()
            
        class _in_B16_B16:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB16.cast(self.inputs[0].get_value())
                b = _OTypeB16.cast(self.inputs[1].get_value())
                if b == 0: raise err(self.operator.src, "Division by zero.")
                return a // b
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB16()
    
    class _op_MODULO:

        class _in_B8_B8:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB8.cast(self.inputs[0].get_value())
                b = _OTypeB8.cast(self.inputs[1].get_value())
                if b == 0: raise err(self.operator.src, "Division by zero.")
                return a % b
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB8()
            
        class _in_B16_B16:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB16.cast(self.inputs[0].get_value())
                b = _OTypeB16.cast(self.inputs[1].get_value())
                if b == 0: raise err(self.operator.src, "Division by zero.")
                return a % b
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB16()
    
    class _op_BIT_AND:

        class _in_B8_B8:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB8.cast(self.inputs[0].get_value())
                b = _OTypeB8.cast(self.inputs[1].get_value())
                return a & b
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB8()
            
        class _in_B16_B16:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB16.cast(self.inputs[0].get_value())
                b = _OTypeB16.cast(self.inputs[1].get_value())
                return a & b
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB16()
    
    class _op_BIT_OR:

        class _in_B8_B8:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB8.cast(self.inputs[0].get_value())
                b = _OTypeB8.cast(self.inputs[1].get_value())
                return a | b
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB8()
            
        class _in_B16_B16:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB16.cast(self.inputs[0].get_value())
                b = _OTypeB16.cast(self.inputs[1].get_value())
                return a | b
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB16()
    
    class _op_BIT_XOR:

        class _in_B8_B8:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB8.cast(self.inputs[0].get_value())
                b = _OTypeB8.cast(self.inputs[1].get_value())
                return a ^ b
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB8()
            
        class _in_B16_B16:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB16.cast(self.inputs[0].get_value())
                b = _OTypeB16.cast(self.inputs[1].get_value())
                return a ^ b
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB16()
    
    class _op_BIT_INV:

        class _in_B8:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB8.cast(self.inputs[0].get_value())
                return a ^ 0xFF
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB8()
            
        class _in_B16:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB16.cast(self.inputs[0].get_value())
                return a ^ 0xFFFF
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB16()
    
    class _op_BIT_SHIFT_L:

        class _in_B8_B8:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB8.cast(self.inputs[0].get_value())
                b = _OTypeB8.cast(self.inputs[1].get_value())
                return (a << b) & 0xFF
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB8()
            
        class _in_B16_B8:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB16.cast(self.inputs[0].get_value())
                b = _OTypeB8.cast(self.inputs[1].get_value())
                return (a << b) & 0xFFFF
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB16()
    
    class _op_BIT_SHIFT_R:

        class _in_B8_B8:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB8.cast(self.inputs[0].get_value())
                b = _OTypeB8.cast(self.inputs[1].get_value())
                return (a >> b) & 0xFF
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB8()
            
        class _in_B16_B8:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB16.cast(self.inputs[0].get_value())
                b = _OTypeB8.cast(self.inputs[1].get_value())
                return (a >> b) & 0xFFFF
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB16()
        
    class _op_BYTE_LO:

        class _in_B16:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB16.cast(self.inputs[0].get_value())
                return a & 0xFF
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB8()
        
    class _op_BYTE_HI:

        class _in_B16:
            @classmethod
            def func(cls, self:'_OValueOperation'):
                a = _OTypeB16.cast(self.inputs[0].get_value())
                return (a >> 8) & 0xFF
            @classmethod
            def rtype(cls, self:'_OValueOperation'):
                return _OTypeB8()
        
    #endregion

#endregion

#endregion

#region LCI

class _LCI:
    """ Represents a label declaration, command call, or assembly instruction """

    #region properties

    @property
    def src(self) -> assutil.SrcChunk:
        raise NotImplementedError("src has not been implemented")

    #endregion

    #region methods

    def echo_format(self) -> str:
        raise NotImplementedError("echo_format has not been implemented.")

    #endregion

class _LCI_CmdIns(_LCI):
    """ Represents a command call or assembly instruction """

    #region Q

    class __Q:
        def __init__(self, items:Iterable[_Token]):
            self.__items:list[_Token] = []
            for _item in items: self.__items.insert(0, _item)
        def __len__(self):
            return len(self.__items)
        def __iter__(self):
            for _i in range(len(self.__items) - 1, -1, -1): yield self.__items[_i]
        def pop(self):
            return self.__items.pop()
        def peek(self):
            return self.__items[-1]

    #endregion
    
    #region init

    def __init__(self, rawinput:Iterable[_Token], labeldict:col.RoDict[str, int], allow_immediate:bool):
        extracted = self.__extract(self.__Q(rawinput), labeldict, allow_immediate)
        self.__immediate:bool = extracted[0]
        self.__input = col.RoList[_OValue](extracted[1])

    #endregion
        
    #region properties

    @property
    def immediate(self): return self.__immediate

    @property
    def input(self): return self.__input

    #endregion
        
    #region helper methods

    @classmethod
    def __extract(cls, input:__Q, labeldict:col.RoDict[str, int], allow_immediate:bool):
        def extract(allow_immediate:bool, inner:bool):
            nonlocal input, labeldict
            # immediate
            immediate = False
            # argmaker
            argmaker_args:list[_OValue] = []
            argmaker_current:list[_TokenOperator|_OValue] = []
            def argmaker_add():
                nonlocal argmaker_args, argmaker_current
                def err_unex_end(src):
                    return err(src, "Unexpected end of expression")
                # Simplify unary operations
                _i = 0
                while _i < len(argmaker_current):
                    _op = argmaker_current[_i]
                    # Look for unary operation
                    if not (isinstance(_op, _TokenOperator) and _op.type.unary):
                        _i += 1
                        continue
                    argmaker_current.pop(_i)
                    # Find value as well as any unary operations in between
                    _ops:list[_TokenOperator] = [_op]
                    _value:None|_OValue = None
                    while True:
                        if _i == len(argmaker_current): raise err_unex_end(_ops[-1].src)
                        _oporvalue = argmaker_current.pop(_i)
                        # Is this a value?
                        if isinstance(_oporvalue, _OValue):
                            _value = _oporvalue
                            break
                        # No! Is this a unary operator?
                        if _oporvalue.type.unary:
                            _ops.append(_oporvalue)
                            continue
                        # No! Then it shouldn't be here.
                        raise err(_oporvalue.src, "Value or unary operator expected")
                    # Simplify
                    _simplified = _OValueOperation(_ops.pop(), [_value])
                    while len(_ops) > 0: _simplified = _OValueOperation(_ops.pop(), [_simplified])
                    # Insert simplified version into list
                    argmaker_current.insert(_i, _simplified)
                # Go thru order of operations
                for _group in _TokenOperator.TYPES_GROUP_ORDER:
                    _group_types = [_op.type for _op in _group]
                    # Look for any of the given operations
                    _i = 0
                    while (_i + 2) < len(argmaker_current):
                        # Get operator
                        _op = argmaker_current[_i + 1]
                        if not isinstance(_op, _TokenOperator): raise err(_op.src, "Operator expected")
                        # Check if operator is one of the given
                        if not (_op.type.type in _group_types):
                            _i += 2
                            continue
                        # Get values
                        _v0 = argmaker_current.pop(_i)
                        argmaker_current.pop(_i) # Pop out operator too
                        _v1 = argmaker_current.pop(_i)
                        if not isinstance(_v0, _OValue): raise err(_v0.src, "Value expected")
                        if not isinstance(_v1, _OValue): raise err(_v1.src, "Value expected")
                        # Insert operation into list
                        argmaker_current.insert(_i, _OValueOperation(_op, [_v0, _v1]))
                # Make sure there's exactly one value
                if len(argmaker_current) != 1:
                    raise err(None if (len(argmaker_current) == 0) else argmaker_current[0].src, "Syntax error")
                single_value = argmaker_current[0]
                if not isinstance(single_value, _OValue):
                    raise err(single_value.src, "Value expected")
                # Add
                argmaker_args.append(single_value)
                # Reset
                argmaker_current.clear()
            # closing
            closing:bool = False
            # Loop thru
            while len(input) > 0:
                _token = input.pop()
                # Is it immediate?
                if isinstance(_token, _TokenImmediate):
                    if not allow_immediate:
                        raise err(_token.src, "Unexpected immediate modifier")
                    immediate = True
                # No! Is it an opening parenthesis?
                elif isinstance(_token, _TokenParOpen):
                    _, _args, _closing = extract(False, True)
                    if not _closing: raise err(_token.src, "Closing parenthesis expected")
                    _input = _args if (len(_args) != 1) else _args[0]
                    argmaker_current.append(_OValueInPar(_token.src, _input))
                # No! Is it a closing parenthesis?
                elif isinstance(_token, _TokenParClose):
                    if not inner: raise err(_token.src, "Unexpected closing parenthesis")
                    closing = True
                    break
                # No! Is it a delimiter?
                elif isinstance(_token, _TokenDelimiter):
                    argmaker_add()
                # No! Is it an operator?
                elif isinstance(_token, _TokenOperator):
                    argmaker_current.append(_token)
                # No! Is it a label reference?
                elif isinstance(_token, _TokenLabelRef):
                    argmaker_current.append(_OValueLabelRef(_token, labeldict))
                # No! Is it a string, number, or register reference?
                elif isinstance(_token, _TokenString | _TokenNumber | _TokenRegRef):
                    argmaker_current.append(_OValueLiteral(_token))
                # Do not allow no more immediate modifiers
                allow_immediate = False
            if len(argmaker_current) > 0: argmaker_add()
            # Success!!!
            return immediate, argmaker_args, closing
        # Extract
        extracted = extract(allow_immediate, False)
        return extracted[0], extracted[1]

    def _echo_input(self):
        with StringIO() as s:
            for _i in range(len(self.__input)):
                if _i > 0: s.write(',')
                s.write(self.__input[_i].echo_format())
            return s.getvalue()

    #endregion

class _LCILabel(_LCI):
    """ Represents a label declaration """

    #region init

    def __init__(self, srctoken:_TokenLabelDec):
        self.__src = srctoken.src
        self.__path = srctoken.path

    #endregion

    #region properties

    @property
    def src(self): return self.__src

    @property
    def path(self): return self.__path

    #endregion

    #region methods

    def echo_format(self) -> str:
        return f"{self.__path}:"

    #endregion

class _LCICommand(_LCI_CmdIns):
    """ Represents a command call """

    #region init

    def __init__(self, srctoken:_TokenCommand, labeldict:col.RoDict[str, int], rawinput:Iterable[_Token]):
        super().__init__(rawinput, labeldict, False)
        self.__name = srctoken.name
        self.__src = srctoken.src
    
    #endregion

    #region properties

    @property
    def src(self): return self.__src

    @property
    def name(self): return self.__name

    #endregion

class _LCIPreCommand(_LCICommand):
    """ Represents a pre-command call """

    #region init

    def __init__(self, srctoken:_TokenCommand, labeldict:col.RoDict[str, int], rawinput:Iterable[_Token]):
        super().__init__(srctoken, labeldict, rawinput)
        if srctoken.post: raise err(srctoken.src, "Looking for pre-command, not post-command.")
        self.__cmd = self.__get_command(srctoken.src, self.name)
    
    #endregion

    #region helper methods

    @classmethod
    def __get_command(cls, src:assutil.SrcChunk, name:str) -> type['_PreCmd']:
        ATTRNAME = "__valid_cmds"
        # Create dictionary if missing
        attr = cast(None|col.ADict[str, type[_PreCmd]], getattr(cls, ATTRNAME, None))
        if attr is None:
            _prefix = f"{_PreCmd.__name__}_"
            attr = col.ADict[str, type[_PreCmd]](\
                (_cmd for _cmd in _PreCmd.__subclasses__() if _cmd.__name__.startswith(_prefix)),\
                lambda _cmd: _cmd.__name__[len(_prefix):])
            setattr(cls, ATTRNAME, attr)
        # Look for command
        if not (name in attr): raise err(src, f"Unknown pre-command: {name}")
        return attr[name]

    #endregion

    #region methods

    def echo_format(self) -> str:
        return f"{CHR_ASS_PRE}{self.name} {self._echo_input()}"
    
    def call(self, preass:'_PreAss'):
        self.__cmd.run(self, preass)

    #endregion

class _LCIPostCommand(_LCICommand):
    """ Represents a post-command call """

    #region init

    def __init__(self, srctoken:_TokenCommand, labeldict:col.RoDict[str, int], rawinput:Iterable[_Token]):
        super().__init__(srctoken, labeldict, rawinput)
        if not srctoken.post: raise err(srctoken.src, "Looking for post-command, not pre-command.")
    
    #endregion

    #region methods

    def echo_format(self) -> str:
        return f"{CHR_ASS_POST}{self.name} {self._echo_input()}"

    #endregion

class _LCIInstruct(_LCI_CmdIns):
    """ Represents an assembly instruction """

    #region init

    def __init__(self, srctoken:_TokenInstruct, labeldict:col.RoDict[str, int], rawinput:Iterable[_Token]):
        super().__init__(rawinput, labeldict, True)
        self.__src = srctoken.src
        self.__type, self.__practinput =\
            self.__what_type(srctoken.src, srctoken.name, self.immediate, self.input)

    #endregion

    #region properties

    @property
    def src(self): return self.__src
    
    @property
    def type(self): return self.__type

    @property
    def practinput(self): return self.__practinput

    #endregion

    #region helper methods

    @classmethod
    def __what_type(cls, src:assutil.SrcChunk, name:str, immediate:bool, input:col.RoList[_OValue]):
        def echo_mode():
            nonlocal immediate, input
            def _syntax(_in:_OValue):
                match _in.type.name:
                    case _OType.Name.NONE:
                        return ''
                    case _OType.Name.B8:
                        return '$nn'
                    case _OType.Name.B16:
                        return '$nnnn'
                    case _OType.Name.STR:
                        return 'STRING'
                    case _OType.Name.REG:
                        if isinstance(_in, _OValueLiteral):
                            return str(_in.get_value())
                        return 'REG'
                    case _OType.Name.TUPLE:
                        return 'TUPLE'
                return '' # Should never happen
            with StringIO() as s:
                if immediate: s.write('#')
                for _i in range(len(input)):
                    if _i > 0: s.write(',')
                    _in = input[_i]
                    # Is this a parenthesis
                    if isinstance(_in, _OValueInPar):
                        s.write('(')
                        if isinstance(_in.input, tuple):
                            for __i in range(len(_in.input)):
                                if __i > 0: s.write(',')
                                s.write(_syntax(_in.input[__i]))
                        else: s.write(_syntax(_in.input))
                        s.write(')')
                    # No!
                    else: s.write(_syntax(_in))
                return s.getvalue()
        def bad_mode():
            nonlocal src
            return err(src, f"Invalid addressing syntax: {echo_mode()}")
        def bad_ins(prefix:assutil.AsmInsPrefix):
            nonlocal src
            return err(src, f"Unsupported instruction: {prefix.name} {echo_mode()}")
        # Determine prefix
        prefix_result = help.ParseUtil.to_enum(name, assutil.AsmInsPrefix, True)
        if prefix_result.status != help.ParseUtilStatus.PASS:
            raise err(src, f"Unknown instruction type: {name}")
        prefix = cast(assutil.AsmInsPrefix, prefix_result.value)
        # Determine addressing mode
        if immediate: # Immediate (check this first to ensure # was not improperly used)?
            if len(input) != 1: raise bad_mode()
            if input[0].type.name != _OType.Name.B8: raise bad_mode()
            addrmode = assutil.AsmInsAddrMode.IMMEDIATE
            practinput = input[0]
        elif len(input) == 0: # Implied
            addrmode = assutil.AsmInsAddrMode.IMPLIED
            practinput = None
        elif len(input) == 1:
            input0 = input[0]
            if isinstance(input0, _OValueInPar):
                if isinstance(input0.input, _OValue): # Absolute Indirect
                    if input0.input.type.name != _OType.Name.B16: raise bad_mode()
                    addrmode = assutil.AsmInsAddrMode.ABSOLUTE_INDIRECT
                    practinput = input0.input
                elif len(input0.input) == 2: # X-Indexed Zero Page Indirect
                    input0_0, input0_1 = input0.input
                    if input0_0.type.name != _OType.Name.B8: raise bad_mode()
                    if input0_1.type.name != _OType.Name.REG: raise bad_mode()
                    if not isinstance(input0_1, _OValueLiteral): raise bad_mode()
                    if input0_1.get_value() != 'X': raise bad_mode()
                    addrmode = assutil.AsmInsAddrMode.X_INDEXED_ZERO_PAGE_INDIRECT
                    practinput = input0_0
                else: raise bad_mode()
            elif input0.type.name == _OType.Name.B16: # Absolute (or relative)
                addrmode = assutil.AsmInsAddrMode.ABSOLUTE
                practinput = input0
            elif input0.type.name == _OType.Name.B8: # Zero Page
                addrmode = assutil.AsmInsAddrMode.ZERO_PAGE
                practinput = input0
            elif input0.type.name == _OType.Name.REG: # Accumulator
                if not isinstance(input0, _OValueLiteral): raise bad_mode()
                if input0.get_value() != 'A': raise bad_mode()
                addrmode = assutil.AsmInsAddrMode.ACCUMULATOR
                practinput = None
            else: raise bad_mode()
        elif len(input) == 2:
            input0 = input[0]
            input1 = input[1]
            if input1.type.name != _OType.Name.REG: raise bad_mode()
            if not isinstance(input1, _OValueLiteral): raise bad_mode()
            reg = input1.get_value()
            if isinstance(input0, _OValueInPar): # Zero Page Indirect Y-Indexed
                if isinstance(input0.input, tuple): raise bad_mode()
                if input0.input.type.name != _OType.Name.B8: raise bad_mode()
                if reg != 'Y': raise bad_mode()
                addrmode = assutil.AsmInsAddrMode.ZERO_PAGE_INDIRECT_Y_INDEXED
                practinput = input0.input
            else: 
                practinput = input0
                if input0.type.name == _OType.Name.B8:
                    if reg == 'X': # X-Indexed Zero Page
                        addrmode = assutil.AsmInsAddrMode.X_INDEXED_ZERO_PAGE
                    elif reg == 'Y': # Y-Indexed Zero Page
                        addrmode = assutil.AsmInsAddrMode.Y_INDEXED_ZERO_PAGE
                    else: raise bad_mode()
                elif input0.type.name == _OType.Name.B16:
                    if reg == 'X': # X-Indexed Absolute
                        addrmode = assutil.AsmInsAddrMode.X_INDEXED_ABSOLUTE
                    elif reg == 'Y': # Y-Indexed Absolute
                        addrmode = assutil.AsmInsAddrMode.Y_INDEXED_ABSOLUTE
                    else: raise bad_mode()
                else: raise bad_mode()
        else: raise bad_mode()
        # Determine instruction type
        premode = assutil.AsmPreMode(prefix, addrmode)
        if not (premode in assutil.ASMINSTYPES_BY_PREMODE):
            if addrmode != assutil.AsmInsAddrMode.ABSOLUTE: raise bad_ins(prefix)
            # Check if Relative is a better fit
            addrmode = assutil.AsmInsAddrMode.RELATIVE
            premode = assutil.AsmPreMode(prefix, addrmode)
            if not (premode in assutil.ASMINSTYPES_BY_PREMODE): bad_ins(prefix)
        # Success!!!
        return assutil.ASMINSTYPES_BY_PREMODE[premode], practinput

    #endregion

    #region methods

    def echo_format(self) -> str:
        return f"{self.__type.prefix.name} {('#' if self.immediate else '')}{self._echo_input()}"

    #endregion

#endregion

#region PreAss

class _PreAss:

    class Error(Exception):
        pass

    #region init

    def __init__(self):
        self.__address = assutil.ROM_BEG
        self.__items:list[None | int | _LCIInstruct] =\
            [None for _ in range(assutil.ROM_BEG, assutil.ROM_END)]

    #endregion

    #region properties

    @property
    def address(self):
        """ Current address """
        return self.__address
    
    #endregion

    #region methods

    def goto(self, address:int):
        """ :raises PreAss.Error: address is out of range """
        if address < assutil.ROM_BEG or address > assutil.ROM_END:
            raise _PreAss.Error("Address is out of range.")
        self.__address = address
    
    def write(self, content:bytes|_LCIInstruct):
        """ :raises PreAss.Error: Address overlaps or exceeds ROM limit """
        size = content.type.mode.size if (isinstance(content, _LCIInstruct)) else len(content)
        beg = self.__address - assutil.ROM_BEG
        end = beg + size
        # Make sure it's safe to write
        if end > len(self.__items): raise _PreAss.Error("ROM limit exceeded")
        for _i in range(beg, end):
            if self.__items[_i] is None: continue
            raise _PreAss.Error("Overlap detected")
        # Write
        if isinstance(content, _LCIInstruct):
            for _i in range(beg, end):
                self.__items[_i] = content
        else:
            if isinstance(content, memoryview): content = content.tobytes()
            for _i in range(size): self.__items[beg + _i] = content[_i]
        # Increment address
        self.__address += size

    def iter_data(self):
        for _item in self.__items: yield _item
    
    #endregion

#endregion

#region PreCmd

class _PreCmd:

    #region helper methods

    @classmethod
    def _verify_no_labels(cls, command:_LCICommand):
        def verify_no_labels(value:_OValue):
            nonlocal command
            # Make sure this is not a label reference
            if isinstance(value, _OValueLabelRef):
                raise err(command.src, f"Pre-commands cannot contain label references.")
            # Loop thru items in parenthesis
            if isinstance(value, _OValueInPar):
                if isinstance(value.input, tuple):
                    for _in in value.input: verify_no_labels(_in)
                else: verify_no_labels(value.input)
            # Loop thru items in operation
            elif isinstance(value, _OValueOperation):
                for _in in value.inputs: verify_no_labels(_in)
        for _in in command.input: verify_no_labels(_in)

    @classmethod
    def _verify_input_type(cls, src:assutil.SrcChunk, type:_OType.Name, expected:_OType.Name|tuple[_OType.Name, ...]):
        if isinstance(expected, tuple):
            for _expected in expected:
                if type == _expected: return 
            if len(expected) == 0:
                nouns = ""
            elif len(expected) == 1:
                nouns = expected[0].name
            elif len(expected) == 2:
                nouns = f"{expected[0].name} nor {expected[1].name}"
            else:
                with StringIO() as s:
                    for _i in range(len(expected) - 1): s.write(f"{expected[_i].name}, ")
                    s.write(f"nor {expected[-1].name}")
                    nouns = s.getvalue()
        else: 
            if type == expected: return
            nouns = expected.name
        raise err(src, f"Cannot assign a {type.name} value to a {nouns} parameter.")

    @classmethod
    def _verify_input_types(cls, command:_LCICommand, righttypes:tuple[_OType.Name|tuple[_OType.Name, ...], ...]):
        if len(command.input) != len(righttypes):
            with StringIO() as _s:
                _one = len(righttypes) == 1
                _s.write(f"{command.name} expects {len(righttypes)} ")
                _s.write("argument" + ('' if _one else 's'))
                _s.write(f" but {len(command.input)} {("was" if _one else "were")} received.")
                raise err(command.src, _s.getvalue())
        for _i in range(len(command.input)):
            cls._verify_input_type(command.src, command.input[_i].type.name, righttypes[_i])

    #endregion

    #region run
    
    @classmethod
    def run(cls, command:_LCICommand, preass:_PreAss) -> None:
        raise NotImplementedError("run has not been implemented.")

    #endregion
    
class _PreCmd_OFFSET(_PreCmd):

    #region run
    
    __RIGHTTYPES = (_OType.Name.B16,)
    
    @classmethod
    def run(cls, command:_LCICommand, preass:_PreAss):
        try:
            # Make sure input is valid
            cls._verify_no_labels(command)
            cls._verify_input_types(command, cls.__RIGHTTYPES)
            # Goto address
            preass.goto(_OTypeB16.cast(command.input[0].get_value()))
            # Success!!!
            return
        except _PreAss.Error as _e: e = err(command.src, _e)
        raise e

    #endregion
    
class _PreCmd_BYTE(_PreCmd):

    #region run
    
    @classmethod
    def run(cls, command:_LCICommand, preass:_PreAss):
        try:
            # Make sure input is valid
            cls._verify_no_labels(command)
            for _arg in command.input:
                cls._verify_input_type(command.src, _arg.type.name, _OType.Name.B8)
            # Write bytes
            preass.write(bytes(_OTypeB8.cast(_arg.get_value()) for _arg in command.input))
            # Success!!!
            return
        except _PreAss.Error as _e: e = err(command.src, _e)
        raise e

    #endregion

class _PreCmd_BYTEFILL(_PreCmd):

    #region run
    
    __RIGHTTYPES = (_OType.Name.B8,(_OType.Name.B8, _OType.Name.B16,))
    
    @classmethod
    def run(cls, command:_LCICommand, preass:_PreAss):
        try:
            # Make sure input is valid
            cls._verify_no_labels(command)
            cls._verify_input_types(command, cls.__RIGHTTYPES)
            # Write
            b = _OTypeB8.cast(command.input[0].get_value())
            s = cast(int, command.input[1].get_value())
            preass.write(bytes(b for _ in range(s)))
            # Success!!!
            return
        except _PreAss.Error as _e: e = err(command.src, _e)
        raise e

    #endregion
    
#endregion

#region Preprocessor

class _Preprocessor:

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

    def __raise_if_ndef(self, chunk:assutil.SrcChunk, macro:str):
        if macro in self.__macros: return
        raise err(chunk, f"Undefined macro: {macro}")

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
                    # Are these quotes?
                    if (not _escape) and _char == '"':
                        inquotes = not inquotes
                        strio.write(_char)
                    # No! Is this in quotes?
                    elif inquotes:
                        strio.write(_char)
                    # No! Is this a comment?
                    elif _char == ';':
                        ___flush()
                        break
                    # No! Is this whitespace?
                    elif _char.isspace():
                        ___flush()
                    # No! Is this an "operator"
                    elif _char in ";()#,+-*/&|^~<>":
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
            if _dirname.startswith(CHR_PRE):
                if not _dirname in directives:
                    raise err(_line[0], f"Unknown preprocessor directive: {_dirname}")
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
        if len(line) == 0: raise err(line, "Unexpected directive")
        raise err(line, f"Unexpected {line[0].content}")

    def __p1_dir_INCLUDE(self, line:list[assutil.SrcChunk]):
        if self.__p1_if_level > self.__p1_if_true: return
        raise_if_ne(line, 1)
        path = help.PathUtil.absolute(get_path(line[1]), self.__directory)
        for _line in self.__run(self.__cmd, path, self.__macros):
            self.__p1_chunksbyline.append(_line)

    def __p1_dir_DEFINE(self, line:list[assutil.SrcChunk]):
        if self.__p1_if_level > self.__p1_if_true: return
        raise_if_lt(line, 1)
        # Get macro name
        macro = get_word(line[1])
        if not self.__case: macro = macro.upper()
        # Add macro
        self.__macros[macro] = self.__p1_expandmacros(line[2:])
    
    def __p1_dir_UNDEF(self, line:list[assutil.SrcChunk]):
        if self.__p1_if_level > self.__p1_if_true: return
        raise_if_ne(line, 1)
        arg_macro = line[1]
        # Get macro name
        macro = get_word(arg_macro)
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
        raise_if_ne(line, 0)
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
        raise_if_ne(line, 0)
        # Decrement
        self.__p1_if_level -= 1
        if self.__p1_if_true > self.__p1_if_level:
            self.__p1_if_true = self.__p1_if_level
        # Should we stop ignoring?
        if self.__p1_if_level == self.__p1_if_true:
            self.__p1_if_ignore = False

    def __p1__dir_ifdef(self, line:list[assutil.SrcChunk], ndef:bool):
        raise_if_ne(line, 1)
        arg_macro = line[1]
        # Get macro name
        macro = get_word(arg_macro)
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
        raise_if_lt(line, 2)
        arg_macro = line[1]
        arg_operator = line[2]
        arg_value = self.__p1_expandmacros(line[3:])
        # Get macro name
        macro = get_word(arg_macro)
        if not self.__case: macro = macro.upper()
        self.__raise_if_ndef(arg_macro, macro)
        macro_value = self.__macros[macro]
        # Get operator
        operator = get_word(arg_operator)
        # Check condition
        match operator.upper():
            case 'eq': return _equals(macro_value, arg_value)
            case 'ne': return not _equals(macro_value, arg_value)
            case _: raise err(arg_operator, f"Unknown equality operator: {operator}")

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

#region Assembler

class _Assembler:

    #region init

    def __init__(self, cmd:'cmd_ass', lines:list[list[assutil.SrcChunk]]):
        self.__cmd = cmd
        self.__lines = lines
        self.__source = cast(Path, self.__cmd.source) # type: ignore
        self.__output = cast(None|Path, self.__cmd.output) # type: ignore
        self.__intmd = cast(None|Path, self.__cmd.intmd) # type: ignore
        self.__case = cast(bool, self.__cmd.case) # type: ignore
        if self.__output is None: output = self.__source.with_suffix('.a26')
        self.__p0_lcis:list[_LCI] = []
        self.__p0_labels:dict[str, _TokenLabelDec] = {}
        self.__p1__labels:dict[str, int] = {}
        self.__p1_labels = col.RoDict[str, int](self.__p1__labels)
        self.__p1_cmds:dict[int, list[_LCICommand]] = {}
        self.__p1_data:list[None | int | _LCIInstruct] = []

    #endregion
    
    #region phase 0

    def __phase0(self):
        self.__p0_lcis.clear()
        self.__p0_labels.clear()
        labelscope:list[str] = []
        for _line in self.__lines:
            # Filter out labels
            _start = 0
            while _start < len(_line):
                _chunk = _line[_start]
                if not _chunk.content.endswith(':'): break
                _token = _TokenLabelDec(_chunk, self.__p0_labels, labelscope, self.__case)
                self.__p0_lcis.append(_LCILabel(_token))
                _start += 1
            if _start == len(_line): continue
            # Get command/instruction
            _first = _line[_start]
            if _first.content.startswith(CHR_ASS_PRE) or\
                    _first.content.startswith(CHR_ASS_POST): # Is this an assembler command? (ex: '?entry')
                _cmdins = _TokenCommand(_first)
            else: # No! Parse as assembly instruction! (ex: 'lda')
                _cmdins = _TokenInstruct(_first)
            # Next chunks
            _input:list[_Token] = []
            for _chunk in _line[1:]:
                _tokenptr = help.Ptr[_Token]()
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
                    _input.append(_TokenString(_chunk))
                elif _chunk_first == '.': # Is this a label (lv1, lv2, ...) reference?
                    _input.append(_TokenLabelRef(_chunk, labelscope, self.__case))
                elif _chunk_first == '$': # Is this a 6502-style hex number?
                    _input.append(_TokenNumber(_chunk))
                elif _chunk_first == '%': # Is this a 6502-style bin number?
                    _input.append(_TokenNumber(_chunk))
                elif _chunk_first.isdigit(): # Is this a number?
                    _input.append(_TokenNumber(_chunk))
                elif str_is_word(_chunk.content):
                    if _try_create(_TokenRegRef.create, _chunk): # Is this a register reference?
                        _input.append(_tokenptr.value)
                    elif _try_create(_TokenOperator.create, _chunk): # Is this an operator?
                        _input.append(_tokenptr.value)
                    else: # Consider it a label reference
                        _input.append(_TokenLabelRef(_chunk, labelscope, self.__case))
                elif _try_create(_TokenParOpen.create, _chunk): # Is this an open parenthesis?
                    _input.append(_tokenptr.value)
                elif _try_create(_TokenParClose.create, _chunk): # Is this a close parenthesis?
                    _input.append(_tokenptr.value)
                elif _try_create(_TokenImmediate.create, _chunk): # Is this an immediate indicator?
                    _input.append(_tokenptr.value)
                elif _try_create(_TokenDelimiter.create, _chunk): # Is this a delimiter?
                    _input.append(_tokenptr.value)
                elif _try_create(_TokenOperator.create, _chunk): # Is this an operator?
                    _input.append(_tokenptr.value)
                else: # Invalid
                    raise err(_chunk, f"Unexpected: {_chunk.content}")
            # Add line
            if isinstance(_cmdins, _TokenCommand):
                if _cmdins.post: self.__p0_lcis.append(_LCIPostCommand(_cmdins, self.__p1_labels, _input))
                else: self.__p0_lcis.append(_LCIPreCommand(_cmdins, self.__p1_labels, _input))
            else:
                self.__p0_lcis.append(_LCIInstruct(_cmdins, self.__p1_labels, _input))

    def __phase1(self):
        self.__p1__labels.clear()
        self.__p1_cmds.clear()
        self.__p1_data.clear()
        # Compute positions of everything
        preass = _PreAss()
        for _lci in self.__p0_lcis:
            # Is this a label?
            if isinstance(_lci, _LCILabel):
                self.__p1__labels[_lci.path] = preass.address
            # No! Is this a command?
            elif isinstance(_lci, _LCICommand):
                # Call pre-command
                if isinstance(_lci, _LCIPreCommand): _lci.call(preass)
                # Add command to dictionary
                if not (preass.address in self.__p1_cmds):
                    _cmdlist:list[_LCICommand] = []
                    self.__p1_cmds[preass.address] = _cmdlist
                else: _cmdlist = self.__p1_cmds[preass.address]
                _cmdlist.append(_lci)
            # No! Is this an instruction?
            elif isinstance(_lci, _LCIInstruct):
                try: preass.write(_lci)
                except _PreAss.Error as _e: raise err(_lci.src, _e)
        self.__p1_data.extend(preass.iter_data())
    
    def __phase2(self):
        intmd = None if (self.__intmd is None) else cliutil.FileUtil.open_w(self.__intmd)
        try:
            # cmd
            def cmd_check():
                nonlocal self
                nonlocal intmd, addr_abs
                if not (addr_abs in self.__p1_cmds): return
                for _cmd in self.__p1_cmds[addr_abs]:
                    # Write to intermediate
                    if intmd is not None:
                        # Command name
                        intmd.write(CHR_ASS_POST if isinstance(_cmd, _LCIPostCommand) else CHR_ASS_PRE)
                        intmd.write(f"{_cmd.name} ")
                        # Command args
                        for _i in range(len(_cmd.input)):
                            if _i > 0: intmd.write(', ')
                            _in = _cmd.input[_i]
                            intmd.write(_in.type.echo(_in.get_value()))
                        intmd.write('\n')
                    # TODO: Call post-command
                    # Next
                    continue
            # addr 
            def addr_inc(step:int):
                nonlocal addr_abs, addr_rel
                for _i in range(step):
                    addr_abs += 1
                    addr_rel += 1
                    cmd_check()
            addr_abs = assutil.ROM_BEG
            addr_rel = 0
            cmd_check()
            # Loop
            while addr_rel < len(self.__p1_data):
                _data = self.__p1_data[addr_rel]
                # Is this empty?
                if _data is None:
                    addr_inc(1)
                    continue
                # No! Is this a block of bytes?
                if isinstance(_data, int):
                    # TODO: Write to a26
                    addr_inc(1)
                    continue
                # No! This is an instruction
                if intmd is not None:
                    _s = _data.type.syntax.upper()
                    if _data.practinput is not None:
                        _v = _data.practinput.get_value()
                        _s = _s.replace('$NNNN', '$NN').replace('$NN', _data.practinput.type.echo(_v))
                    intmd.write(f"{_s}\n")
                # TODO: Write to a26
                # Next
                addr_inc(_data.type.mode.size)
        finally:
            if intmd is not None: intmd.close()


    #endregion
    
    #region run

    @classmethod
    def run(cls, cmd:'cmd_ass', lines:list[list[assutil.SrcChunk]]):
        instance = cls(cmd, lines)
        instance.__phase0()
        instance.__phase1()
        instance.__phase2()

    #endregion

#endregion

class cmd_ass(cli.CLICommand):
    
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

    #region methods

    def _main(self):
        try: 
            source = cast(Path, self.source) # type: ignore
            # Preprocess
            preprocessed = _Preprocessor.run(self, source)
            _Assembler.run(self, preprocessed)
            # Success!!!
            return 0
        except cliutil.CommandError as _e:
            print("ERROR", file = sys.stderr)
            print(_e, file = sys.stderr)
            return 1

    #endregion