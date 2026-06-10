__all__ = [\
    'AsmInsPrefix',\
    'AsmInsInputType',\
    'AsmInsInputTypeInfo',\
    'ASMINSINPUTTYPES',\
    'AsmInsAddrMode',\
    'AsmInsAddrModeInfo',\
    'ASMINSADDRMODES',\
    'AsmInsTypeCat',\
    'AsmInsType',\
    'ASMINSTYPES',\
    'AsmPreMode',\
    'ASMINSTYPES_BY_PREMODE',\
    'AsmIns']

from dataclasses import\
    dataclass as _dataclass
from enum import\
    auto as _auto,\
    Enum as _Enum
from typing import\
    Callable as _Callable

from col import\
    ADict as _ADict,\
    RoDict as _RoDict
from help import\
    BadDataError as _BadDataError

from .c_AsmItem import AsmItem as _AsmItem

#region AsmInsPrefix

class AsmInsPrefix(_Enum):
    """ Represents an assembly instruction prefix """
    LDA = _auto()
    TAX = _auto()
    PHA = _auto()
    ASL = _auto()
    AND = _auto()
    ADC = _auto()
    DEC = _auto()
    BRK = _auto()
    BCC = _auto()
    CLC = _auto()
    NOP = _auto()
    LDX = _auto()
    TAY = _auto()
    PHP = _auto()
    LSR = _auto()
    BIT = _auto()
    CMP = _auto()
    DEX = _auto()
    JMP = _auto()
    BCS = _auto()
    CLD = _auto()
    LDY = _auto()
    TSX = _auto()
    PLA = _auto()
    ROL = _auto()
    EOR = _auto()
    CPX = _auto()
    DEY = _auto()
    JSR = _auto()
    BEQ = _auto()
    CLI = _auto()
    STA = _auto()
    TXA = _auto()
    PLP = _auto()
    ROR = _auto()
    ORA = _auto()
    CPY = _auto()
    INC = _auto()
    RTI = _auto()
    BMI = _auto()
    CLV = _auto()
    STX = _auto()
    TXS = _auto()
    SBC = _auto()
    INX = _auto()
    RTS = _auto()
    BNE = _auto()
    SEC = _auto()
    STY = _auto()
    TYA = _auto()
    INY = _auto()
    BPL = _auto()
    SED = _auto()
    BVC = _auto()
    SEI = _auto()
    BVS = _auto()

#endregion

#region AsmInsInputType

class AsmInsInputType(_Enum):
    """ Represents the "input type" of an assembly instruction """
    NONE = _auto()
    """ Instruction takes no additional input """
    BIT8 = _auto()
    """ Instruction takes an 8-bit value as input """
    BIT16 = _auto()
    """ Instruction takes a 16-bit value as input """
    REL = _auto()
    """ Instruction takes a relative offset as input """

class AsmInsInputTypeInfo:
    """ Represents information about an input type """

    #region Info

    @_dataclass(frozen = True)
    class __Info:
        type:AsmInsInputType
        size:int
        sanitize:_Callable[[int], int]
        from_bytes:_Callable[[bytes], int]
        to_bytes:_Callable[[int], bytes]

    #endregion

    #region init

    def __init__(self, info:__Info):
        """ Do NOT initialize directly """
        self.__info = info

    @classmethod
    def getall(cls):
        types:list[AsmInsInputTypeInfo] = []
        # NONE
        types.append(cls(cls.__Info(\
            AsmInsInputType.NONE, 0,\
            lambda _i: -1,\
            lambda _b: -1,\
            lambda _i: b'')))
        # BIT8
        types.append(cls(cls.__Info(\
            AsmInsInputType.BIT8, 1,\
            lambda _i: max(0, min(0xFF, _i)),\
            lambda _b: _b[0],\
            lambda _i: bytes([_i]))))
        # BIT16
        types.append(cls(cls.__Info(\
            AsmInsInputType.BIT16, 2,\
            lambda _i: max(0, min(0xFFFF, _i)),\
            lambda _b: _b[0] | (_b[1] << 8),\
            lambda _i: bytes([_i & 0xFF, (_i >> 8) & 0xFF]))))
        # REL
        types.append(cls(cls.__Info(\
            AsmInsInputType.REL, 1,\
            lambda _i: max(-128, min(127, _i)),\
            lambda _b: ((_b[0] + 128) & 0xFF) - 128,\
            lambda _i: bytes([ (_i + 0x100) & 0xFF ]))))
        # Return
        return _ADict[AsmInsInputType, AsmInsInputTypeInfo](types, lambda _i: _i.__info.type)

    #endregion

    #region properties
    
    @property
    def type(self):
        """ Input type """
        return self.__info.type

    @property
    def size(self):
        """ Input size (in bytes) """
        return self.__info.size

    #endregion

    #region methods

    def sanitize(self, rawinput:int):
        """
        Sanitizes raw input

        :param rawinput: Raw input
        :return: Sanitized input
        """
        return self.__info.sanitize(rawinput)

    def from_bytes(self, data:bytes):
        """
        Converts byte data to input

        :param data: Byte data
        :return: Input
        :raise BadDataError: Data is of invalid size
        """
        if len(data) == self.__info.size: return self.__info.from_bytes(data)
        s = "byte" + ('' if (self.__info.size == 1) else 's')
        raise _BadDataError(f"{self.__info.type.name} requires exactly {s} of data.")

    def to_bytes(self, input:int):
        """
        Converts input to byte data

        :param input: Input
        :return: Byte data
        """
        return self.__info.to_bytes(self.__info.sanitize(input))

    #endregion

ASMINSINPUTTYPES = AsmInsInputTypeInfo.getall()
""" All input types """

#endregion

#region AsmInsAddrMode

class AsmInsAddrMode(_Enum):
    """ Represents an assembly address mode """
    IMPLIED = _auto()
    """ Implied """
    ACCUMULATOR = _auto()
    """ Accumulator """
    IMMEDIATE = _auto()
    """ Immediate """
    ABSOLUTE = _auto()
    """ Absolute """
    X_INDEXED_ABSOLUTE = _auto()
    """ X-Indexed Absolute """
    Y_INDEXED_ABSOLUTE = _auto()
    """ Y-Indexed Absolute """
    ABSOLUTE_INDIRECT = _auto()
    """ Absolute Indirect """
    ZERO_PAGE = _auto()
    """ Zero Page """
    X_INDEXED_ZERO_PAGE = _auto()
    """ X-Indexed Zero Page """
    Y_INDEXED_ZERO_PAGE = _auto()
    """ Y-Indexed Zero Page """
    X_INDEXED_ZERO_PAGE_INDIRECT = _auto()
    """ X-Indexed Zero Page Indirect """
    ZERO_PAGE_INDIRECT_Y_INDEXED = _auto()
    """ Zero Page Indirect Y-Indexed """
    RELATIVE = _auto()
    """ Relative """

class AsmInsAddrModeInfo:
    """ Represents information about an addressing mode """

    #region Info

    @_dataclass(frozen = True)
    class __Info:
        mode:AsmInsAddrMode
        syntax:str
        input_type:AsmInsInputTypeInfo
        input_is_addr:bool
        size:int
        gen:_Callable[[int, AsmInsPrefix, int], str]
        absaddr:_Callable[[int, int], int]

    #endregion

    #region init

    def __init__(self, info:__Info):
        """ Do NOT initialize directly """
        self.__info = info

    @classmethod
    def getall(cls):
        modes:list[AsmInsAddrModeInfo] = []
        # IMPLIED
        modes.append(AsmInsAddrModeInfo(cls.__Info(\
            AsmInsAddrMode.IMPLIED,\
            '',\
            ASMINSINPUTTYPES[AsmInsInputType.NONE],\
            False,\
            ASMINSINPUTTYPES[AsmInsInputType.NONE].size + 1,\
            lambda insaddr, prefix, input: f"{prefix.name}",\
            lambda insaddr, addr: 0)))
        # ACCUMULATOR
        modes.append(AsmInsAddrModeInfo(cls.__Info(\
            AsmInsAddrMode.ACCUMULATOR,\
            "A",\
            ASMINSINPUTTYPES[AsmInsInputType.NONE],\
            False,\
            ASMINSINPUTTYPES[AsmInsInputType.NONE].size + 1,\
            lambda insaddr, prefix, input: f"{prefix.name} A",\
            lambda insaddr, addr: 0)))
        # IMMEDIATE
        modes.append(AsmInsAddrModeInfo(cls.__Info(\
            AsmInsAddrMode.IMMEDIATE,\
            "#$nn",\
            ASMINSINPUTTYPES[AsmInsInputType.BIT8],\
            False,\
            ASMINSINPUTTYPES[AsmInsInputType.BIT8].size + 1,\
            lambda insaddr, prefix, input: f"{prefix.name} #${input:02X}",\
            lambda insaddr, addr: 0)))
        # ABSOLUTE
        modes.append(AsmInsAddrModeInfo(cls.__Info(\
            AsmInsAddrMode.ABSOLUTE,\
            "$nnnn",\
            ASMINSINPUTTYPES[AsmInsInputType.BIT16],\
            True,\
            ASMINSINPUTTYPES[AsmInsInputType.BIT16].size + 1,\
            lambda insaddr, prefix, input: f"{prefix.name} ${input:04X}",\
            lambda insaddr, addr: addr)))
        # X_INDEXED_ABSOLUTE
        modes.append(AsmInsAddrModeInfo(cls.__Info(\
            AsmInsAddrMode.X_INDEXED_ABSOLUTE,\
            "$nnnn,X",\
            ASMINSINPUTTYPES[AsmInsInputType.BIT16],\
            True,\
            ASMINSINPUTTYPES[AsmInsInputType.BIT16].size + 1,\
            lambda insaddr, prefix, input: f"{prefix.name} ${input:04X},X",\
            lambda insaddr, addr: addr)))
        # Y_INDEXED_ABSOLUTE
        modes.append(AsmInsAddrModeInfo(cls.__Info(\
            AsmInsAddrMode.Y_INDEXED_ABSOLUTE,\
            "$nnnn,Y",\
            ASMINSINPUTTYPES[AsmInsInputType.BIT16],\
            True,\
            ASMINSINPUTTYPES[AsmInsInputType.BIT16].size + 1,\
            lambda insaddr, prefix, input: f"{prefix.name} ${input:04X},Y",\
            lambda insaddr, addr: addr)))
        # ABSOLUTE_INDIRECT
        modes.append(AsmInsAddrModeInfo(cls.__Info(\
            AsmInsAddrMode.ABSOLUTE_INDIRECT,\
            "($nnnn)",\
            ASMINSINPUTTYPES[AsmInsInputType.BIT16],\
            True,\
            ASMINSINPUTTYPES[AsmInsInputType.BIT16].size + 1,\
            lambda insaddr, prefix, input: f"{prefix.name} (${input:04X})",\
            lambda insaddr, addr: addr)))
        # ZERO_PAGE
        modes.append(AsmInsAddrModeInfo(cls.__Info(\
            AsmInsAddrMode.ZERO_PAGE,\
            "$nn",\
            ASMINSINPUTTYPES[AsmInsInputType.BIT8],\
            True,\
            ASMINSINPUTTYPES[AsmInsInputType.BIT8].size + 1,\
            lambda insaddr, prefix, input: f"{prefix.name} ${input:02X}",\
            lambda insaddr, addr: addr)))
        # X_INDEXED_ZERO_PAGE
        modes.append(AsmInsAddrModeInfo(cls.__Info(\
            AsmInsAddrMode.X_INDEXED_ZERO_PAGE,\
            "$nn,X",\
            ASMINSINPUTTYPES[AsmInsInputType.BIT8],\
            True,\
            ASMINSINPUTTYPES[AsmInsInputType.BIT8].size + 1,\
            lambda insaddr, prefix, input: f"{prefix.name} ${input:02X},X",\
            lambda insaddr, addr: addr)))
        # Y_INDEXED_ZERO_PAGE
        modes.append(AsmInsAddrModeInfo(cls.__Info(\
            AsmInsAddrMode.Y_INDEXED_ZERO_PAGE,\
            "$nn,Y",\
            ASMINSINPUTTYPES[AsmInsInputType.BIT8],\
            True,\
            ASMINSINPUTTYPES[AsmInsInputType.BIT8].size + 1,\
            lambda insaddr, prefix, input: f"{prefix.name} ${input:02X},Y",\
            lambda insaddr, addr: addr)))
        # X_INDEXED_ZERO_PAGE_INDIRECT
        modes.append(AsmInsAddrModeInfo(cls.__Info(\
            AsmInsAddrMode.X_INDEXED_ZERO_PAGE_INDIRECT,\
            "($nn,X)",\
            ASMINSINPUTTYPES[AsmInsInputType.BIT8],\
            True,\
            ASMINSINPUTTYPES[AsmInsInputType.BIT8].size + 1,\
            lambda insaddr, prefix, input: f"{prefix.name} (${input:02X},X)",\
            lambda insaddr, addr: addr)))
        # ZERO_PAGE_INDIRECT_Y_INDEXED
        modes.append(AsmInsAddrModeInfo(cls.__Info(\
            AsmInsAddrMode.ZERO_PAGE_INDIRECT_Y_INDEXED,\
            "($nn),Y",\
            ASMINSINPUTTYPES[AsmInsInputType.BIT8],\
            True,\
            ASMINSINPUTTYPES[AsmInsInputType.BIT8].size + 1,\
            lambda insaddr, prefix, input: f"{prefix.name} (${input:02X}),Y",\
            lambda insaddr, addr: addr)))
        # RELATIVE
        modes.append(AsmInsAddrModeInfo(cls.__Info(\
            AsmInsAddrMode.RELATIVE,\
            "$nnnn",\
            ASMINSINPUTTYPES[AsmInsInputType.REL],\
            True,\
            ASMINSINPUTTYPES[AsmInsInputType.REL].size + 1,\
            lambda insaddr, prefix, input: f"{prefix.name} ${(insaddr + 2 + input):04X}",\
            lambda insaddr, addr: insaddr + 2 + addr)))
        # Return
        return _ADict[AsmInsAddrMode, AsmInsAddrModeInfo](modes, lambda _i: _i.__info.mode)

    #endregion

    #region properties
    
    @property
    def mode(self):
        """ Addressing mode """
        return self.__info.mode
    
    @property
    def syntax(self):
        """ Instruction syntax (excluding prefix) """
        return self.__info.syntax
    
    @property
    def input_type(self):
        """ Input type """
        return self.__info.input_type

    @property
    def input_is_addr(self):
        """ Whether or not the input refers to an address """
        return self.__info.input_is_addr

    @property
    def size(self):
        """ Required instruction size (including opcode) (in bytes) """
        return self.__info.size

    #endregion

    #region methods

    def gen(self, insaddr:int, prefix:AsmInsPrefix, input:int):
        """
        Generates a string representation of an assembly instruction

        :param addr: Instruction address
        :param prefix: Instruction prefix
        :param input: Input value
        :return: Generated string
        """
        return self.__info.gen(insaddr, prefix, input)

    def absaddr(self, insaddr:int, addr:int):
        """
        Computes the an absolute address\n
        For non-RELATIVE addressing modes, addr is returned.\n
        For IMPLIED, ACCUMULATOR, IMMEDIATE addressing modes, this function is useless.

        :param insaddr: Instruction address
        :param addr: Address to compute
        :return: Computed absolute address
        """
        return self.__info.absaddr(insaddr, addr)

    #endregion

ASMINSADDRMODES = AsmInsAddrModeInfo.getall()
""" All addressing modes """

#endregion

#region AsmInsType

class AsmInsTypeCat(_Enum):
    LOAD = _auto()
    """ Instruction either loads from or save to memory """
    TRANS = _auto()
    """ Instruction transfers values between different registers or between a register and the stack """
    STACK = _auto()
    """ Instruction is used manipulate the stack """
    SHIFT = _auto()
    """ Instruction performs a bit-shift operation """
    LOGIC = _auto()
    """ Instruction performs a bit-wise logic operation """
    ARITH = _auto()
    """ Instruction performs an addition, subtraction, or comparison operation """
    INC = _auto()
    """ Instruction performs an increment or decrement operation """
    CTRL = _auto()
    """ Instruction is used to control the flow of the program """
    BRANCH = _auto()
    """ Instruction performs a branch if a certain condition is met """
    FLAGS = _auto()
    """ Instruction manipulates the flag states """
    NOP = _auto()
    """ No operation """

class AsmInsType:
    """ Represents a type of assembly instruction """
    
    #region Info

    @_dataclass(frozen = True)
    class __Info:
        prefix:AsmInsPrefix
        category:AsmInsTypeCat
        mode:AsmInsAddrModeInfo
        opcode:int

    #endregion

    #region init

    def __init__(self, info:__Info):
        """ Do NOT initialize directly """
        self.__info = info
        self.__syntax =\
            self.__info.prefix.name +\
            ("" if (len(self.__info.mode.syntax) == 0) else f" {self.__info.mode.syntax}")

    @classmethod
    def getall(cls):
        modes:list[AsmInsType] = []
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.BRK,\
            AsmInsTypeCat.CTRL,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0x00)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.CLC,\
            AsmInsTypeCat.FLAGS,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0x18)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.CLD,\
            AsmInsTypeCat.FLAGS,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0xD8)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.CLI,\
            AsmInsTypeCat.FLAGS,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0x58)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.CLV,\
            AsmInsTypeCat.FLAGS,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0xB8)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.DEX,\
            AsmInsTypeCat.INC,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0xCA)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.DEY,\
            AsmInsTypeCat.INC,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0x88)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.INX,\
            AsmInsTypeCat.INC,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0xE8)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.INY,\
            AsmInsTypeCat.INC,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0xC8)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.NOP,\
            AsmInsTypeCat.NOP,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0xEA)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.PHA,\
            AsmInsTypeCat.STACK,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0x48)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.PHP,\
            AsmInsTypeCat.STACK,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0x08)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.PLA,\
            AsmInsTypeCat.STACK,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0x68)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.PLP,\
            AsmInsTypeCat.STACK,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0x28)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.RTI,\
            AsmInsTypeCat.CTRL,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0x40)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.RTS,\
            AsmInsTypeCat.CTRL,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0x60)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.SEC,\
            AsmInsTypeCat.FLAGS,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0x38)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.SED,\
            AsmInsTypeCat.FLAGS,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0xF8)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.SEI,\
            AsmInsTypeCat.FLAGS,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0x78)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.TAX,\
            AsmInsTypeCat.TRANS,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0xAA)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.TAY,\
            AsmInsTypeCat.TRANS,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0xA8)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.TSX,\
            AsmInsTypeCat.TRANS,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0xBA)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.TXA,\
            AsmInsTypeCat.TRANS,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0x8A)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.TXS,\
            AsmInsTypeCat.TRANS,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0x9A)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.TYA,\
            AsmInsTypeCat.TRANS,\
            ASMINSADDRMODES[AsmInsAddrMode.IMPLIED],\
            0x98)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ASL,\
            AsmInsTypeCat.SHIFT,\
            ASMINSADDRMODES[AsmInsAddrMode.ACCUMULATOR],\
            0x0A)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LSR,\
            AsmInsTypeCat.SHIFT,\
            ASMINSADDRMODES[AsmInsAddrMode.ACCUMULATOR],\
            0x4A)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ROL,\
            AsmInsTypeCat.SHIFT,\
            ASMINSADDRMODES[AsmInsAddrMode.ACCUMULATOR],\
            0x2A)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ROR,\
            AsmInsTypeCat.SHIFT,\
            ASMINSADDRMODES[AsmInsAddrMode.ACCUMULATOR],\
            0x6A)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ADC,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.IMMEDIATE],\
            0x69)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.AND,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.IMMEDIATE],\
            0x29)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.CMP,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.IMMEDIATE],\
            0xC9)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.CPX,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.IMMEDIATE],\
            0xE0)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.CPY,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.IMMEDIATE],\
            0xC0)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.EOR,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.IMMEDIATE],\
            0x49)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LDA,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.IMMEDIATE],\
            0xA9)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LDX,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.IMMEDIATE],\
            0xA2)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LDY,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.IMMEDIATE],\
            0xA0)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ORA,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.IMMEDIATE],\
            0x09)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.SBC,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.IMMEDIATE],\
            0xE9)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ADC,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0x6D)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.AND,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0x2D)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ASL,\
            AsmInsTypeCat.SHIFT,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0x0E)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.BIT,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0x2C)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.CMP,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0xCD)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.CPX,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0xEC)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.CPY,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0xCC)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.DEC,\
            AsmInsTypeCat.INC,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0xCE)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.EOR,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0x4D)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.INC,\
            AsmInsTypeCat.INC,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0xEE)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.JMP,\
            AsmInsTypeCat.CTRL,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0x4C)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.JSR,\
            AsmInsTypeCat.CTRL,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0x20)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LDA,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0xAD)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LDX,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0xAE)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LDY,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0xAC)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LSR,\
            AsmInsTypeCat.SHIFT,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0x4E)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ORA,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0x0D)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ROL,\
            AsmInsTypeCat.SHIFT,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0x2E)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ROR,\
            AsmInsTypeCat.SHIFT,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0x6E)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.SBC,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0xED)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.STA,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0x8D)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.STX,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0x8E)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.STY,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE],\
            0x8C)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ADC,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ABSOLUTE],\
            0x7D)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.AND,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ABSOLUTE],\
            0x3D)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ASL,\
            AsmInsTypeCat.SHIFT,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ABSOLUTE],\
            0x1E)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.CMP,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ABSOLUTE],\
            0xDD)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.DEC,\
            AsmInsTypeCat.INC,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ABSOLUTE],\
            0xDE)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.EOR,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ABSOLUTE],\
            0x5D)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.INC,\
            AsmInsTypeCat.INC,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ABSOLUTE],\
            0xFE)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LDA,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ABSOLUTE],\
            0xBD)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LDY,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ABSOLUTE],\
            0xBC)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LSR,\
            AsmInsTypeCat.SHIFT,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ABSOLUTE],\
            0x5E)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ORA,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ABSOLUTE],\
            0x1D)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ROL,\
            AsmInsTypeCat.SHIFT,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ABSOLUTE],\
            0x3E)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ROR,\
            AsmInsTypeCat.SHIFT,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ABSOLUTE],\
            0x7E)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.SBC,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ABSOLUTE],\
            0xFD)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.STA,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ABSOLUTE],\
            0x9D)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ADC,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.Y_INDEXED_ABSOLUTE],\
            0x79)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.AND,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.Y_INDEXED_ABSOLUTE],\
            0x39)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.CMP,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.Y_INDEXED_ABSOLUTE],\
            0xD9)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.EOR,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.Y_INDEXED_ABSOLUTE],\
            0x59)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LDA,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.Y_INDEXED_ABSOLUTE],\
            0xB9)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LDX,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.Y_INDEXED_ABSOLUTE],\
            0xBE)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ORA,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.Y_INDEXED_ABSOLUTE],\
            0x19)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.SBC,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.Y_INDEXED_ABSOLUTE],\
            0xF9)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.STA,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.Y_INDEXED_ABSOLUTE],\
            0x99)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.JMP,\
            AsmInsTypeCat.CTRL,\
            ASMINSADDRMODES[AsmInsAddrMode.ABSOLUTE_INDIRECT],\
            0x6C)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ADC,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE],\
            0x65)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.AND,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE],\
            0x25)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ASL,\
            AsmInsTypeCat.SHIFT,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE],\
            0x06)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.BIT,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE],\
            0x24)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.CMP,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE],\
            0xC5)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.CPX,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE],\
            0xE4)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.CPY,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE],\
            0xC4)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.DEC,\
            AsmInsTypeCat.INC,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE],\
            0xC6)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.EOR,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE],\
            0x45)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.INC,\
            AsmInsTypeCat.INC,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE],\
            0xE6)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LDA,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE],\
            0xA5)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LDX,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE],\
            0xA6)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LDY,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE],\
            0xA4)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LSR,\
            AsmInsTypeCat.SHIFT,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE],\
            0x46)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ORA,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE],\
            0x05)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ROL,\
            AsmInsTypeCat.SHIFT,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE],\
            0x26)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ROR,\
            AsmInsTypeCat.SHIFT,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE],\
            0x66)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.SBC,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE],\
            0xE5)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.STA,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE],\
            0x85)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.STX,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE],\
            0x86)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.STY,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE],\
            0x84)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ADC,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE],\
            0x75)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.AND,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE],\
            0x35)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ASL,\
            AsmInsTypeCat.SHIFT,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE],\
            0x16)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.CMP,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE],\
            0xD5)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.DEC,\
            AsmInsTypeCat.INC,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE],\
            0xD6)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.EOR,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE],\
            0x55)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.INC,\
            AsmInsTypeCat.INC,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE],\
            0xF6)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LDA,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE],\
            0xB5)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LDY,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE],\
            0xB4)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LSR,\
            AsmInsTypeCat.SHIFT,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE],\
            0x56)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ORA,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE],\
            0x15)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ROL,\
            AsmInsTypeCat.SHIFT,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE],\
            0x36)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ROR,\
            AsmInsTypeCat.SHIFT,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE],\
            0x76)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.SBC,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE],\
            0xF5)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.STA,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE],\
            0x95)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.STY,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE],\
            0x94)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LDX,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.Y_INDEXED_ZERO_PAGE],\
            0xB6)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.STX,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.Y_INDEXED_ZERO_PAGE],\
            0x96)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ADC,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE_INDIRECT],\
            0x61)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.AND,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE_INDIRECT],\
            0x21)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.CMP,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE_INDIRECT],\
            0xC1)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.EOR,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE_INDIRECT],\
            0x41)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LDA,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE_INDIRECT],\
            0xA1)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ORA,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE_INDIRECT],\
            0x01)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.SBC,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE_INDIRECT],\
            0xE1)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.STA,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.X_INDEXED_ZERO_PAGE_INDIRECT],\
            0x81)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ADC,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE_INDIRECT_Y_INDEXED],\
            0x71)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.AND,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE_INDIRECT_Y_INDEXED],\
            0x31)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.CMP,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE_INDIRECT_Y_INDEXED],\
            0xD1)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.EOR,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE_INDIRECT_Y_INDEXED],\
            0x51)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.LDA,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE_INDIRECT_Y_INDEXED],\
            0xB1)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.ORA,\
            AsmInsTypeCat.LOGIC,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE_INDIRECT_Y_INDEXED],\
            0x11)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.SBC,\
            AsmInsTypeCat.ARITH,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE_INDIRECT_Y_INDEXED],\
            0xF1)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.STA,\
            AsmInsTypeCat.LOAD,\
            ASMINSADDRMODES[AsmInsAddrMode.ZERO_PAGE_INDIRECT_Y_INDEXED],\
            0x91)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.BCC,\
            AsmInsTypeCat.BRANCH,\
            ASMINSADDRMODES[AsmInsAddrMode.RELATIVE],\
            0x90)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.BCS,\
            AsmInsTypeCat.BRANCH,\
            ASMINSADDRMODES[AsmInsAddrMode.RELATIVE],\
            0xB0)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.BEQ,\
            AsmInsTypeCat.BRANCH,\
            ASMINSADDRMODES[AsmInsAddrMode.RELATIVE],\
            0xF0)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.BMI,\
            AsmInsTypeCat.BRANCH,\
            ASMINSADDRMODES[AsmInsAddrMode.RELATIVE],\
            0x30)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.BNE,\
            AsmInsTypeCat.BRANCH,\
            ASMINSADDRMODES[AsmInsAddrMode.RELATIVE],\
            0xD0)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.BPL,\
            AsmInsTypeCat.BRANCH,\
            ASMINSADDRMODES[AsmInsAddrMode.RELATIVE],\
            0x10)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.BVC,\
            AsmInsTypeCat.BRANCH,\
            ASMINSADDRMODES[AsmInsAddrMode.RELATIVE],\
            0x50)))
        modes.append(cls(cls.__Info(\
            AsmInsPrefix.BVS,\
            AsmInsTypeCat.BRANCH,\
            ASMINSADDRMODES[AsmInsAddrMode.RELATIVE],\
            0x70)))
        # Return
        return _ADict[int, AsmInsType](modes, lambda _i: _i.__info.opcode)

    #endregion

    #region operators

    def __str__(self): return self.__syntax
    
    def __eq__(self, other): return self.__eq(other)
    def __ne__(self, other): return not self.__eq(other)

    #endregion

    #region properties

    @property
    def prefix(self):
        """ Prefix """
        return self.__info.prefix

    @property
    def category(self):
        """ Category """
        return self.__info.category

    @property
    def mode(self):
        """ Addressing mode """
        return self.__info.mode

    @property
    def opcode(self):
        """ Opcode """
        return self.__info.opcode

    @property
    def syntax(self):
        """ Instruction syntax """
        return self.__syntax

    #endregion

    #region helper methods

    def __eq(self, other):
        if not isinstance(other, AsmInsType): return False
        return self.__info.prefix == other.__info.prefix and\
            self.__info.mode == other.__info.mode and\
            self.__info.opcode == other.__info.opcode

    #endregion

ASMINSTYPES = AsmInsType.getall()
""" All instruction types by opcode """

#endregion

#region AsmPreMode

class AsmPreMode:
    """ Represents an assembly instruction prefix accompanied by an addressing mode """

    #region init

    def __init__(self, prefix:AsmInsPrefix, addrmode:AsmInsAddrMode):
        self.__prefix = prefix
        self.__addrmode = addrmode

    #endregion

    #region operators

    def __str__(self): return f"{self.__prefix.name} {self.__addrmode.name}"
    
    def __eq__(self, other): return self.__eq(other)
    def __ne__(self, other): return not self.__eq(other)
    def __hash__(self): return hash(self.__prefix)

    #endregion

    #region helper methods

    def __eq(self, other):
        if not isinstance(other, AsmPreMode): return False
        return self.__prefix == other.__prefix and self.__addrmode == other.__addrmode

    #endregion

ASMINSTYPES_BY_PREMODE = _ADict[AsmPreMode, AsmInsType](ASMINSTYPES, lambda i: AsmPreMode(i.prefix, i.mode.mode))
""" All instruction types by prefix and addressing mode """

#endregion

#region AsmIns 

class AsmIns(_AsmItem):
    """ Represents an assembly instruction """
    
    #region init

    def __init__(self, opcode:None|int = None, input:None|int = None, data:None|bytes = None):
        """
        Initializer for AsmIns\n
        - If opcode is defined (IOW not None), input must be defined
        - If data is defined, opcode and input are ignored

        :param opcode: Opcode
        :param input: Opcode
        :param data: Byte data (Including opcode)
        :raise BadDataError: Data is not valid
        """
        if data is not None:
            if len(data) == 0: raise _BadDataError("Data cannot be empty.")
            # What kind of instruction is this?
            _opcode = data[0]
            if not (_opcode in ASMINSTYPES):
                raise _BadDataError("Unrecognized opcode")
            self.__type = ASMINSTYPES[_opcode]
            # Make sure data is of required size
            if len(data) != self.__type.mode.size:
                raise _BadDataError("Opcode/data mismatch")
            self.__input = self.__type.mode.input_type.from_bytes(data[1:])
        elif opcode is not None:
            if input is None:
                raise ValueError("A definition for opcode must be accompanied by a definition for input.")
            self.__type = ASMINSTYPES[opcode]
            self.__input = self.__type.mode.input_type.sanitize(input)
        else:
            raise ValueError("Either opcode or data must be defined.")

    #endregion

    #region properties

    @property
    def type(self):
        """ Instruction type """
        return self.__type
    
    @property
    def input(self):
        """ Instruction input """
        return self.__input

    #endregion

    #region methods

    def gen_str(self, addr:int):
        return self.__type.mode.gen(addr, self.__type.prefix, self.__input)
    
    def gen_bytes(self):
        return bytes([self.__type.opcode]) + self.__type.mode.input_type.to_bytes(self.__input)

    #endregion

#endregion