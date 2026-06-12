__all__ = ['cmd_dbt']

import struct
import sys

from collections.abc import Iterable, Sequence
from enum import Enum, Flag
from typing import Callable, cast
from pathlib import Path

import assutil
import cli
import cliutil
import col
import help

import random

type InsFuncCall = Callable[['_System', int, assutil.AsmIns], None]

#region CPU

class _CPU:

    #region init

    def __init__(self, rnd:bool, allowwrap:bool):
        self.__a = random.randint(0x00, 0xFF) if rnd else 0
        self.__x = random.randint(0x00, 0xFF) if rnd else 0
        self.__y = random.randint(0x00, 0xFF) if rnd else 0
        self.__stack = _CPUStack(rnd, allowwrap)
        self.__flags = _CPUFlags.NONE
    
    #endregion

    #region properties

    @property
    def a(self):
        """ Accumulator """
        return self.__a
    @a.setter
    def a(self, value:int):
        self.__a = 0xFF & value
    
    @property
    def x(self):
        """ X Index Register """
        return self.__x
    @x.setter
    def x(self, value:int):
        self.__x = 0xFF & value
        
    @property
    def y(self):
        """ Y Index Register """
        return self.__y
    @y.setter
    def y(self, value:int):
        self.__y = 0xFF & value
    
    @property
    def stack(self):
        """ Stack """
        return self.__stack
    
    @property
    def flags(self):
        """ Processor status flags """
        return self.__flags
    @flags.setter
    def flags(self, value:'_CPUFlags'):
        self.__flags = value

    #endregion

class _CPUStack:
    
    #region init

    def __init__(self, rnd:bool, allowwrap:bool):
        self.__bytes = bytearray(random.randbytes(0x100) if rnd else (b'\00' * 0x100))
        self.__pos = len(self.__bytes)
        self.__allowwrap = allowwrap

    #endregion

    #region operations

    def __len__(self):
        return len(self.__bytes)
    
    def __getitem__(self, index:int):
        try: return self.__bytes[index]
        except Exception as _e: e = _e
        self.__raise_if_oor(index)
        raise e
    
    def __setitem__(self, index:int, value:int):
        try:
            self.__bytes[index] = value & 0xFF
            return
        except Exception as _e: e = _e
        self.__raise_if_oor(index)
        raise e
    
    def __iter__(self):
        for _b in self.__bytes: yield _b
    
    #endregion

    #region properties

    @property
    def pos(self):
        """ Position of stack pointer """
        return self.__pos
    @pos.setter
    def pos(self, value:int):
        if value < 0 or value > len(self.__bytes):
            raise IndexError("Position is out of range.")
        self.__pos = value

    #endregion

    #region helper methods

    def __raise_if_oor(self, index:int):
        if index >= 0 and index < len(self.__bytes): return
        raise IndexError("Index is out of range.")
    
    #endregion

    #region methods

    def push(self, value:int):
        # Fix if overflow
        if self.__pos == 0:
            if (not self.__allowwrap):
                raise cliutil.CommandError("Stack overflow")
            self.__pos = len(self.__bytes)
        # Decrement and set value
        self.__pos -= 1
        self.__bytes[self.__pos] = value & 0xFF
        
    def pull(self):
        # Fix if underflow
        if self.__pos == len(self.__bytes):
            if (not self.__allowwrap):
                raise cliutil.CommandError("Stack underflow")
            self.__pos = 0
        # Get value and increment
        value = self.__bytes[self.__pos]
        self.__pos += 1
        return value

    #endregion

class _CPUFlags(Flag):

    #region values

    NONE = 0
    NEGATIVE = 1 << 7
    OVERFLOW = 1 << 6
    EXPANSION = 1 << 5
    BREAK = 1 << 4
    DECIMAL = 1 << 3
    INTDIS = 1 << 2
    ZERO = 1 << 1
    CARRY = 1 << 0

    #endregion

    #region methods

    def isset(self, flag:'_CPUFlags'):
        return (self.value & flag.value) != 0

    def set(self, flag:'_CPUFlags', value:bool):
        if value: return _CPUFlags(self.value | flag.value)
        return _CPUFlags(self.value & (0xFF ^ flag.value))
    
    def set_multi(self, flagconds:Iterable[tuple['_CPUFlags', bool]]) -> '_CPUFlags':
        flags = self
        for flag, value in flagconds:
            flags = flags.set(flag, value)
        return flags

    #endregion

#endregion

#region Memory

class _Memory:

    #region init

    def __init__(self, rnd:bool):
        # For the sake of simplicity, this will be 64 KB in size (since the memory addresses are 16-bit).
        # In other words, this will not be an accurate emulation of the Atari VCS's memory.
        self.__bytes = bytearray(random.randbytes(assutil.ROM_VECTOR) if rnd else (b'\00' * assutil.ROM_VECTOR))
        self.__pos = 0
    
    #endregion

    #region operations

    def __len__(self):
        return len(self.__bytes)
    
    def __getitem__(self, address:int):
        try: return self.__bytes[address]
        except Exception as _e: e = _e
        self.__raise_if_oor(address)
        raise e
    
    def __setitem__(self, address:int, value:int):
        try:
            self.__bytes[address] = value & 0xFF
            return
        except Exception as _e: e = _e
        self.__raise_if_oor(address)
        raise e
    
    def __iter__(self):
        for _b in self.__bytes: yield _b
    
    #endregion

    #region properties

    @property
    def pos(self):
        """ Current position """
        return self.__pos

    #endregion

    #region helper methods

    def __raise_if_oor(self, address:int):
        if address >= 0 and address < len(self.__bytes): return
        raise IndexError("Address is out of range.")
    
    def __read(self, size:int) -> bytes:
        newaddr = self.__pos + size
        if newaddr <= len(self.__bytes):
            oldaddr = self.__pos
            self.__pos = newaddr
            return bytes(self.__bytes[_i] for _i in range(oldaddr, newaddr))
        raise cliutil.CommandError("ROM limit exceeded")
    
    #endregion

    #region methods

    def goto(self, address:int):
        self.__raise_if_oor(address)
        self.__pos = address
    
    def read(self, size:int):
        return self.__read(max(0, size))
    
    def read_8(self):
        return self.__read(1)[0]
    
    def read_16(self) -> int:
        return struct.unpack('<H', self.__read(2))[0]
    
    def populate(self, offset:int, data:Sequence[int]):
        if offset < 0 or (offset + len(data)) > len(self.__bytes):
            raise IndexError("Out of range.")
        for _i in range(len(data)):
            self.__bytes[offset + _i] = data[_i]

    #endregion

#endregion

#region System

class _System:

    #region init

    def __init__(self, cmd:'cmd_dbt'):
        peek = cast(None|int, cmd.peek) # type: ignore
        nogarb = cast(bool, cmd.nogarb) # type: ignore
        stackwrap = cast(bool, cmd.stackwrap) # type: ignore
        self.__cpu = _CPU(not nogarb, stackwrap)
        self.__memory = _Memory(not nogarb)
        self.__peek = peek
        self.__stop = False

    #endregion

    #region properties

    @property
    def cpu(self): return self.__cpu

    @property
    def memory(self): return self.__memory
    
    @property
    def peek(self): return self.__peek

    @property
    def stop(self): return self.__stop
    @stop.setter
    def stop(self, value:bool): self.__stop = value

    #endregion

#endregion

#region InsFunc

class InsFunc:

    #region helper methods

    @classmethod
    def __get_value(cls, system:_System, addr:int, ins:assutil.AsmIns):
        if ins.type.mode.mode == assutil.AsmInsAddrMode.ACCUMULATOR:
            return system.cpu.a
        if ins.type.mode.mode == assutil.AsmInsAddrMode.IMMEDIATE:
            return ins.input
        if ins.type.mode.input_is_addr:
            return system.memory[ins.type.mode.absaddr(addr, ins.input)]
        return 0

    @classmethod
    def __set_value(cls, system:_System, addr:int, ins:assutil.AsmIns, value:int):
        if ins.type.mode.mode == assutil.AsmInsAddrMode.ACCUMULATOR:
            system.cpu.a = value
        elif ins.type.mode.input_is_addr:
            system.memory[ins.type.mode.absaddr(addr, ins.input)] = value
    
    @classmethod
    def __update_nz(cls, system:_System, value:int):
        system.cpu.flags = system.cpu.flags.set_multi((\
            (_CPUFlags.NEGATIVE, (value & 0b10000000) != 0),\
            (_CPUFlags.ZERO, value == 0),))
        
    @classmethod
    def __print_if_peek(cls, system:_System, dest:int):
        if system.peek is None: return
        if system.peek == dest: print(f"${system.memory[dest]:02X}")

    #endregion

    #region methods

    @classmethod
    def get(cls):
        PREFIX = "ins_"
        funcs:dict[str, InsFuncCall] = {}
        for _attrname in dir(cls):
            _attr = getattr(cls, _attrname)
            if not callable(_attr): continue
            if not _attr.__name__.startswith(PREFIX): continue
            funcs[_attr.__name__[len(PREFIX):]] = _attr.__call__
        return col.RoDict[str, InsFuncCall](funcs)
    
    #region load/store
    
    @classmethod
    def ins_LDA(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.a = cls.__get_value(system, addr, ins)
        cls.__update_nz(system, system.cpu.a)

    @classmethod
    def ins_LDX(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.x = cls.__get_value(system, addr, ins)
        cls.__update_nz(system, system.cpu.x)

    @classmethod
    def ins_LDY(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.y = cls.__get_value(system, addr, ins)
        cls.__update_nz(system, system.cpu.y)
    
    @classmethod
    def ins_STA(cls, system:_System, addr:int, ins:assutil.AsmIns):
        dest = ins.type.mode.absaddr(addr, ins.input)
        system.memory[dest] = system.cpu.a
        cls.__print_if_peek(system, dest)
    
    @classmethod
    def ins_STX(cls, system:_System, addr:int, ins:assutil.AsmIns):
        dest = ins.type.mode.absaddr(addr, ins.input)
        system.memory[dest] = system.cpu.x
        cls.__print_if_peek(system, dest)
    
    @classmethod
    def ins_STY(cls, system:_System, addr:int, ins:assutil.AsmIns):
        dest = ins.type.mode.absaddr(addr, ins.input)
        system.memory[dest] = system.cpu.y
        cls.__print_if_peek(system, dest)

    #endregion

    #region transfer
    
    @classmethod
    def ins_TAX(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.x = system.cpu.a
        cls.__update_nz(system, system.cpu.x)
    
    @classmethod
    def ins_TAY(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.y = system.cpu.a
        cls.__update_nz(system, system.cpu.x)
    
    @classmethod
    def ins_TSX(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.x = system.cpu.stack.pos
        cls.__update_nz(system, system.cpu.x)
    
    @classmethod
    def ins_TXA(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.a = system.cpu.x
        cls.__update_nz(system, system.cpu.a)
    
    @classmethod
    def ins_TXS(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.stack.pos = system.cpu.x
    
    @classmethod
    def ins_TYA(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.a = system.cpu.y
        cls.__update_nz(system, system.cpu.a)

    #endregion

    #region stack
    
    @classmethod
    def ins_PHA(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.stack.push(system.cpu.a)
    
    @classmethod
    def ins_PHP(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.stack.push(system.cpu.flags.value)

    @classmethod
    def ins_PLA(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.a = system.cpu.stack.pull()
        cls.__update_nz(system, system.cpu.a)
    
    @classmethod
    def ins_PLP(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.flags = _CPUFlags(system.cpu.stack.pull())

    #endregion

    #region bit-shift
    
    @classmethod
    def ins_ASL(cls, system:_System, addr:int, ins:assutil.AsmIns):
        old = cls.__get_value(system, addr, ins)
        new = (old << 1) & 0xFF
        cls.__set_value(system, addr, ins, new)
        cls.__update_nz(system, new)
        system.cpu.flags = system.cpu.flags.set(_CPUFlags.CARRY, (old & 0x80) != 0)
    
    @classmethod
    def ins_LSR(cls, system:_System, addr:int, ins:assutil.AsmIns):
        old = cls.__get_value(system, addr, ins)
        new = old >> 1
        cls.__set_value(system, addr, ins, new)
        cls.__update_nz(system, new)
        system.cpu.flags = system.cpu.flags.set(_CPUFlags.CARRY, (old & 0x01) != 0)
    
    @classmethod
    def ins_ROL(cls, system:_System, addr:int, ins:assutil.AsmIns):
        old = cls.__get_value(system, addr, ins)
        new = ((old << 1) & 0xFF) | (0x01 if system.cpu.flags.isset(_CPUFlags.CARRY) else 0x00)
        cls.__set_value(system, addr, ins, new)
        cls.__update_nz(system, new)
        system.cpu.flags = system.cpu.flags.set(_CPUFlags.CARRY, (old & 0x80) != 0)
    
    @classmethod
    def ins_ROR(cls, system:_System, addr:int, ins:assutil.AsmIns):
        old = cls.__get_value(system, addr, ins)
        new = (old >> 1) | (0x80 if system.cpu.flags.isset(_CPUFlags.CARRY) else 0x00)
        cls.__set_value(system, addr, ins, new)
        cls.__update_nz(system, new)
        system.cpu.flags = system.cpu.flags.set(_CPUFlags.CARRY, (old & 0x01) != 0)
    
    #endregion

    #region logic

    @classmethod
    def ins_AND(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.a &= cls.__get_value(system, addr, ins)
        cls.__update_nz(system, system.cpu.a)
    
    @classmethod
    def ins_BIT(cls, system:_System, addr:int, ins:assutil.AsmIns):
        value = cls.__get_value(system, addr, ins)
        system.cpu.flags = system.cpu.flags.set_multi((\
            (_CPUFlags.NEGATIVE, (value & 0b10000000) != 0),\
            (_CPUFlags.OVERFLOW, (value & 0b01000000) != 0),\
            (_CPUFlags.ZERO, (system.cpu.a & value) == 0),))
    
    @classmethod
    def ins_EOR(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.a ^= cls.__get_value(system, addr, ins)
        cls.__update_nz(system, system.cpu.a)
    
    @classmethod
    def ins_ORA(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.a |= cls.__get_value(system, addr, ins)
        cls.__update_nz(system, system.cpu.a)
    
    #endregion

    #region arithmetic

    @classmethod
    def ins_ADC(cls, system:_System, addr:int, ins:assutil.AsmIns):
        # TODO: Ensure calculations are correct
        value = system.cpu.a + cls.__get_value(system, addr, ins) +\
            (1 if system.cpu.flags.isset(_CPUFlags.CARRY) else 0)
        old = system.cpu.a
        system.cpu.a = value & 0xFF
        # Determine carry
        if system.cpu.flags.isset(_CPUFlags.DECIMAL):
            carry = value > 99
        else:
            carry = value > 0xFF
        # Update flags
        system.cpu.flags = system.cpu.flags.set_multi((\
            (_CPUFlags.CARRY, carry),\
            (_CPUFlags.OVERFLOW, (old & 0x80) != (system.cpu.a & 0x80))))
        cls.__update_nz(system, system.cpu.a)
    
    @classmethod
    def ins_CMP(cls, system:_System, addr:int, ins:assutil.AsmIns):
        value = system.cpu.a - cls.__get_value(system, addr, ins)
        system.cpu.flags = system.cpu.flags.set(_CPUFlags.CARRY, value >= 0)
        cls.__update_nz(system, value)
    
    @classmethod
    def ins_CPX(cls, system:_System, addr:int, ins:assutil.AsmIns):
        value = system.cpu.x - cls.__get_value(system, addr, ins)
        system.cpu.flags = system.cpu.flags.set(_CPUFlags.CARRY, value >= 0)
        cls.__update_nz(system, value)
    
    @classmethod
    def ins_CPY(cls, system:_System, addr:int, ins:assutil.AsmIns):
        value = system.cpu.y - cls.__get_value(system, addr, ins)
        system.cpu.flags = system.cpu.flags.set(_CPUFlags.CARRY, value >= 0)
        cls.__update_nz(system, value)
    
    @classmethod
    def ins_SBC(cls, system:_System, addr:int, ins:assutil.AsmIns):
        # TODO: Ensure calculations are correct
        value = system.cpu.a - cls.__get_value(system, addr, ins) -\
            (0 if system.cpu.flags.isset(_CPUFlags.CARRY) else 1)
        old = system.cpu.a
        system.cpu.a = (0x100 + value) & 0xFF
        # Update flags
        system.cpu.flags = system.cpu.flags.set_multi((\
            (_CPUFlags.CARRY, value >= 0 ),\
            (_CPUFlags.OVERFLOW, (old & 0x80) != (system.cpu.a & 0x80))))
        cls.__update_nz(system, system.cpu.a)
    
    #endregion

    #region increment/decrement

    @classmethod
    def ins_DEC(cls, system:_System, addr:int, ins:assutil.AsmIns):
        value = (cls.__get_value(system, addr, ins) + 0xFF) & 0xFF
        cls.__set_value(system, addr, ins, value)
        cls.__update_nz(system, value)

    @classmethod
    def ins_DEX(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.x = (system.cpu.x + 0xFF) & 0xFF
        cls.__update_nz(system, system.cpu.x)
        
    @classmethod
    def ins_DEY(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.y = (system.cpu.y + 0xFF) & 0xFF
        cls.__update_nz(system, system.cpu.y)
    
    @classmethod
    def ins_INC(cls, system:_System, addr:int, ins:assutil.AsmIns):
        value = (cls.__get_value(system, addr, ins) + 1) & 0xFF
        cls.__set_value(system, addr, ins, value)
        cls.__update_nz(system, value)

    @classmethod
    def ins_INX(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.x = (system.cpu.x + 1) & 0xFF
        cls.__update_nz(system, system.cpu.x)
        
    @classmethod
    def ins_INY(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.y = (system.cpu.y + 1) & 0xFF
        cls.__update_nz(system, system.cpu.y)
    
    #endregion

    #region control

    @classmethod
    def ins_BRK(cls, system:_System, addr:int, ins:assutil.AsmIns):
        raise cliutil.CommandError("BRK is not yet supported")

    @classmethod
    def ins_JMP(cls, system:_System, addr:int, ins:assutil.AsmIns):
        if ins.type.mode.mode == assutil.AsmInsAddrMode.ABSOLUTE_INDIRECT:
            raise cliutil.CommandError("JMP ($nnnn) is not yet supported")
        system.memory.goto(ins.type.mode.absaddr(addr, ins.input))

    @classmethod
    def ins_JSR(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.stack.push((system.memory.pos & 0xFF00) >> 8)
        system.cpu.stack.push(system.memory.pos & 0x00FF)
        system.memory.goto(ins.type.mode.absaddr(addr, ins.input))

    @classmethod
    def ins_RTI(cls, system:_System, addr:int, ins:assutil.AsmIns):
        raise cliutil.CommandError("RTI is not yet supported")

    @classmethod
    def ins_RTS(cls, system:_System, addr:int, ins:assutil.AsmIns):
        dest_lo = system.cpu.stack.pull()
        dest_hi = system.cpu.stack.pull()
        system.memory.goto((dest_hi << 8) | dest_lo)
    
    #endregion
    
    #region branch

    @classmethod
    def ins_BCC(cls, system:_System, addr:int, ins:assutil.AsmIns):
        if system.cpu.flags.isset(_CPUFlags.CARRY): return
        system.memory.goto(ins.type.mode.absaddr(addr, ins.input))

    @classmethod
    def ins_BCS(cls, system:_System, addr:int, ins:assutil.AsmIns):
        if not system.cpu.flags.isset(_CPUFlags.CARRY): return
        system.memory.goto(ins.type.mode.absaddr(addr, ins.input))

    @classmethod
    def ins_BEQ(cls, system:_System, addr:int, ins:assutil.AsmIns):
        if not system.cpu.flags.isset(_CPUFlags.ZERO): return
        system.memory.goto(ins.type.mode.absaddr(addr, ins.input))

    @classmethod
    def ins_BMI(cls, system:_System, addr:int, ins:assutil.AsmIns):
        if not system.cpu.flags.isset(_CPUFlags.NEGATIVE): return
        system.memory.goto(ins.type.mode.absaddr(addr, ins.input))

    @classmethod
    def ins_BNE(cls, system:_System, addr:int, ins:assutil.AsmIns):
        if system.cpu.flags.isset(_CPUFlags.ZERO): return
        system.memory.goto(ins.type.mode.absaddr(addr, ins.input))

    @classmethod
    def ins_BPL(cls, system:_System, addr:int, ins:assutil.AsmIns):
        if system.cpu.flags.isset(_CPUFlags.NEGATIVE): return
        system.memory.goto(ins.type.mode.absaddr(addr, ins.input))

    @classmethod
    def ins_BVC(cls, system:_System, addr:int, ins:assutil.AsmIns):
        if system.cpu.flags.isset(_CPUFlags.OVERFLOW): return
        system.memory.goto(ins.type.mode.absaddr(addr, ins.input))

    @classmethod
    def ins_BVS(cls, system:_System, addr:int, ins:assutil.AsmIns):
        if not system.cpu.flags.isset(_CPUFlags.OVERFLOW): return
        system.memory.goto(ins.type.mode.absaddr(addr, ins.input))

    #endregion

    #region flags
    
    @classmethod
    def ins_CLC(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.flags.set(_CPUFlags.CARRY, False)
    
    @classmethod
    def ins_CLD(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.flags.set(_CPUFlags.DECIMAL, False)
    
    @classmethod
    def ins_CLI(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.flags.set(_CPUFlags.INTDIS, False)
    
    @classmethod
    def ins_CLV(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.flags.set(_CPUFlags.OVERFLOW, False)
    
    @classmethod
    def ins_SEC(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.flags.set(_CPUFlags.CARRY, True)
    
    @classmethod
    def ins_SED(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.flags.set(_CPUFlags.DECIMAL, True)
    
    @classmethod
    def ins_SEI(cls, system:_System, addr:int, ins:assutil.AsmIns):
        system.cpu.flags.set(_CPUFlags.INTDIS, True)

    #endregion

    #region nop
    
    @classmethod
    def ins_NOP(cls, system:_System, addr:int, ins:assutil.AsmIns):
        pass

    #endregion

    #endregion

_INSFUNCS = InsFunc.get()

#endregion

class cmd_dbt(cli.CLICommand):

    #region cli

    @property
    def _desc(self) -> None|str:
        return "Disassembles a ROM (NOTE: Bank switching not currently supported)"
    
    __rom = cli.CLIRequiredDef(\
        name = "rom",\
        desc = "ROM file (*.a26;*.bin)",\
        parse = cliutil.ParseUtil.to_path)
    
    __peek = cli.CLIOptionWArgDef(\
        name = "peek",\
        desc = "Peek address; any data stored here will be printed to the screen",\
        parse = cli.CLIParseUtil.to_uint16)
    
    __nogarb = cli.CLIOptionFlagDef(\
        name = "nogarb",\
        desc = "If true, garbage memory will not be simulated")
    
    __stackwrap = cli.CLIOptionFlagDef(\
        name = "stackwrap",\
        desc = "If true, stack pointer will \"wrap around\" in cases of overflow/underflow")

    #endregion

    #region helper methods

    @classmethod
    def __get_dest_addr(cls, ins_addr:int, ins:assutil.AsmIns):
        return ins.type.mode.absaddr(ins_addr, ins.input)
    
    @classmethod
    def __ins_input(cls, ins:assutil.AsmIns, input:str):
        # Prefix
        beg = 0
        while beg < len(ins.type.syntax):
            if ins.type.syntax[beg] == '$': break
            beg += 1
        if beg == len(ins.type.syntax): return ins.type.syntax
        # Suffix
        end = beg + 1
        while end < len(ins.type.syntax):
            if ins.type.syntax[end].lower() != 'n': break
            end += 1
        return ins.type.syntax[:beg] + input + ins.type.syntax[end:]

    #endregion

    #region methods

    def _main(self):
        rom = cast(Path, self.rom) # type: ignore
        peek = cast(None|int, self.peek) # type: ignore
        nogarb = cast(bool, self.nogarb) # type: ignore
        stackwrap = cast(bool, self.stackwrap) # type: ignore
        try:
            VECTOR = assutil.ROM_VECTOR - assutil.ROM_BEG
            addr_nmi = 0
            addr_entry = 0
            addr_break = 0
            system = _System(self)
            # Read ROM
            with cliutil.FileUtil.open_rb(rom) as _f:
                # Check size
                size = help.IOUtil.get_size(_f)
                if size < assutil.ROM_SIZE: raise cliutil.CommandError(\
                    f"ROM must have a size of {assutil.ROM_SIZE} bytes.")
                if size > assutil.ROM_SIZE: print(\
                    "ROMs with bank switching are not supported.")
                # NMI, entry, break
                _f.seek(VECTOR)
                addr_nmi:int = struct.unpack('<H', _f.read(2))[0]
                addr_entry:int = struct.unpack('<H', _f.read(2))[0]
                addr_break:int = struct.unpack('<H', _f.read(2))[0]
                if addr_entry < assutil.ROM_BEG: raise cliutil.CommandError(\
                    f"Entry-point address ${addr_entry:04X} is out of range.")
                # Create memory
                _f.seek(0)
                system.memory.populate(assutil.ROM_BEG, _f.read(VECTOR))
            # Begin execution
            system.memory.goto(addr_entry)
            while (True):
                _pos = system.memory.pos
                # Read opcode
                _ins_opcode =  system.memory.read_8()
                # Get instruction type
                if not (_ins_opcode in assutil.ASMINSTYPES):
                    raise cliutil.CommandError(f"${_pos:04X}: Invalid opcode ${_ins_opcode:02X}")
                _ins_type = assutil.ASMINSTYPES[_ins_opcode]
                # Read instruction
                _ins_data = bytes([_ins_opcode]) + system.memory.read(max(0, _ins_type.mode.size - 1))
                _ins = assutil.AsmIns(data = _ins_data)
                # Perform instruction
                _INSFUNCS[_ins.type.prefix.name](system, _pos, _ins)
                # Should we stop?
                if system.stop: break
            # End of execution
            print(f"End at ${system.memory.pos:04X}")
            # Success!!!
            return 0
        except cliutil.CommandError as _e:
            print("ERROR", file = sys.stderr)
            print(_e, file = sys.stderr)
            return 1

    #endregion