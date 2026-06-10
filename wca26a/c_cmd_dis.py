__all__ = ['cmd_dis']

import struct
import sys

from dataclasses import dataclass
from typing import Callable, cast
from pathlib import Path

import assutil
import cli
import cliutil
import col
import help

import random

#region Reader

class _Reader:

    #region init

    def __init__(self, input:Path):
        self.__input = None
        self.__beg = 0
        self.__end = 0
        self.__size = 0
        self.__address = 0
        # Open file
        try:
            self.__input = cliutil.FileUtil.open_rb(input)
            self.__beg = assutil.ROM_BEG
            self.__size = help.IOUtil.get_size(self.__input)
            self.__end = self.__beg + self.__size
            self.__address = self.__beg
        except:
            self.close()
            raise
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    #endregion

    #region properties

    @property
    def beg(self):
        """ Beginning address """
        return self.__beg
    
    @property
    def end(self):
        """ End address """
        return self.__end

    @property
    def size(self):
        """ Size of file """
        return self.__size

    @property
    def address(self):
        """ Current address of reader """
        return self.__address

    #endregion

    #region helper methods

    def __raise_if_disposed(self):
        if self.__input is not None: return
        raise help.BadOpError("Object has already been disposed.")
    
    def __read(self, size:int) -> bytes:
        self.__raise_if_disposed()
        newaddr = self.__address + size
        if newaddr <= self.__end:
            self.__address = newaddr
            return self.__input.read(size) # type: ignore
        raise cliutil.CommandError("ROM limit exceeded")
    
    #endregion

    #region methods

    def close(self):
        if self.__input is None: return
        self.__input.close()
        self.__input = None

    def goto(self, address:int):
        """ :raises help.BadOpError: Object has already been disposed """
        self.__raise_if_disposed()
        if address < self.__beg or address > self.__end:
            raise cliutil.CommandError("Address is out of range.")
        self.__address = address
        self.__input.seek(self.__address - self.__beg) # type: ignore
    
    def read(self, size:int):
        """ :raises help.BadOpError: Object has already been disposed """
        return self.__read(max(0, size))
    
    def read_8(self):
        """ :raises help.BadOpError: Object has already been disposed """
        return self.__read(1)[0]
    
    def read_16(self) -> int:
        """ :raises help.BadOpError: Object has already been disposed """
        return struct.unpack('<H', self.__read(2))[0]

    #endregion

#endregion

#region Addr

class _Addr:

    #region init

    def __init__(self, zp:bool, value:int):
        self.__zp = zp
        self.__value = value

    #endregion

    #region operators

    def __str__(self):
        return f"${self.__value:02X}" if self.__zp else f"${self.__value:04X}"
    
    def __eq__(self, other):
        return self.__eq(other)
    def __ne__(self, other):
        return not self.__eq(other)
    def __hash__(self):
        return self.__value
    def __lt__(self, other:'_Addr|int'):
        if isinstance(other, int): return self.__value < other
        if self.__zp != other.__zp: return self.__zp # Zero-page addresses precede non zero-page addresses
        return self.__value < other.__value
    def __le__(self, other:'_Addr|int'):
        if isinstance(other, int): return self.__value <= other
        if self.__zp != other.__zp: return self.__zp # Zero-page addresses precede non zero-page addresses
        return self.__value <= other.__value
    def __gt__(self, other:'_Addr|int'):
        if isinstance(other, int): return self.__value > other
        if self.__zp != other.__zp: return other.__zp # Zero-page addresses precede non zero-page addresses
        return self.__value > other.__value
    def __ge__(self, other:'_Addr|int'):
        if isinstance(other, int): return self.__value >= other
        if self.__zp != other.__zp: return other.__zp # Zero-page addresses precede non zero-page addresses
        return self.__value >= other.__value

    #endregion

    #region properties

    @property
    def zp(self): return self.__zp

    @property
    def value(self): return self.__value

    #endregion

    #region helper methods

    def __eq(self, other):
        if not isinstance(other, _Addr): return False
        return self.__zp == other.__zp and self.__value == other.__value

    #endregion


#endregion

#region NameAddr

@dataclass(frozen = True)
class _NameAddr:
    name:str
    addr:_Addr

#endregion

#region common

@dataclass(frozen = True)
class _CommonDef:
    name:str
    value:int
    comment:str

COMMON_URL = "https://problemkaputt.de/2k6specs.htm"

COMMON_ZP = col.ADict([\
    _CommonDef("VSYNC", 0x00, "......1.  vertical sync set-clear"),\
    _CommonDef("VBLANK", 0x01, "11....1.  vertical blank set-clear"),\
    _CommonDef("WSYNC", 0x02, "<strobe>  wait for leading edge of horizontal blank"),\
    _CommonDef("RSYNC", 0x03, "<strobe>  reset horizontal sync counter"),\
    _CommonDef("NUSIZ0", 0x04, "..111111  number-size player-missile 0"),\
    _CommonDef("NUSIZ1", 0x05, "..111111  number-size player-missile 1"),\
    _CommonDef("COLUP0", 0x06, "1111111.  color-lum player 0 and missile 0"),\
    _CommonDef("COLUP1", 0x07, "1111111.  color-lum player 1 and missile 1"),\
    _CommonDef("COLUPF", 0x08, "1111111.  color-lum playfield and ball"),\
    _CommonDef("COLUBK", 0x09, "1111111.  color-lum background"),\
    _CommonDef("CTRLPF", 0x0A, "..11.111  control playfield ball size & collisions"),\
    _CommonDef("REFP0", 0x0B, "....1...  reflect player 0"),\
    _CommonDef("REFP1", 0x0C, "....1...  reflect player 1"),\
    _CommonDef("PF0", 0x0D, "1111....  playfield register byte 0"),\
    _CommonDef("PF1", 0x0E, "11111111  playfield register byte 1"),\
    _CommonDef("PF2", 0x0F, "11111111  playfield register byte 2"),\
    _CommonDef("RESP0", 0x10, "<strobe>  reset player 0"),\
    _CommonDef("RESP1", 0x11, "<strobe>  reset player 1"),\
    _CommonDef("RESM0", 0x12, "<strobe>  reset missile 0"),\
    _CommonDef("RESM1", 0x13, "<strobe>  reset missile 1"),\
    _CommonDef("RESBL", 0x14, "<strobe>  reset ball"),\
    _CommonDef("AUDC0", 0x15, "....1111  audio control 0"),\
    _CommonDef("AUDC1", 0x16, "....1111  audio control 1"),\
    _CommonDef("AUDF0", 0x17, "...11111  audio frequency 0"),\
    _CommonDef("AUDF1", 0x18, "...11111  audio frequency 1"),\
    _CommonDef("AUDV0", 0x19, "....1111  audio volume 0"),\
    _CommonDef("AUDV1", 0x1A, "....1111  audio volume 1"),\
    _CommonDef("GRP0", 0x1B, "11111111  graphics player 0"),\
    _CommonDef("GRP1", 0x1C, "11111111  graphics player 1"),\
    _CommonDef("ENAM0", 0x1D, "......1.  graphics (enable) missile 0"),\
    _CommonDef("ENAM1", 0x1E, "......1.  graphics (enable) missile 1"),\
    _CommonDef("ENABL", 0x1F, "......1.  graphics (enable) ball"),\
    _CommonDef("HMP0", 0x20, "1111....  horizontal motion player 0"),\
    _CommonDef("HMP1", 0x21, "1111....  horizontal motion player 1"),\
    _CommonDef("HMM0", 0x22, "1111....  horizontal motion missile 0"),\
    _CommonDef("HMM1", 0x23, "1111....  horizontal motion missile 1"),\
    _CommonDef("HMBL", 0x24, "1111....  horizontal motion ball"),\
    _CommonDef("VDELP0", 0x25, ".......1  vertical delay player 0"),\
    _CommonDef("VDELP1", 0x26, ".......1  vertical delay player 1"),\
    _CommonDef("VDELBL", 0x27, ".......1  vertical delay ball"),\
    _CommonDef("RESMP0", 0x28, "......1.  reset missile 0 to player 0"),\
    _CommonDef("RESMP1", 0x29, "......1.  reset missile 1 to player 1"),\
    _CommonDef("HMOVE", 0x2A, "<strobe>  apply horizontal motion"),\
    _CommonDef("HMCLR", 0x2B, "<strobe>  clear horizontal motion registers"),\
    _CommonDef("CXCLR", 0x2C, "<strobe>  clear collision latches"),\
    _CommonDef("CXM0P", 0x30, "11......  read collision M0-P1, M0-P0 (Bit 7,6)"),\
    _CommonDef("CXM1P", 0x31, "11......  read collision M1-P0, M1-P1"),\
    _CommonDef("CXP0FB", 0x32, "11......  read collision P0-PF, P0-BL"),\
    _CommonDef("CXP1FB", 0x33, "11......  read collision P1-PF, P1-BL"),\
    _CommonDef("CXM0FB", 0x34, "11......  read collision M0-PF, M0-BL"),\
    _CommonDef("CXM1FB", 0x35, "11......  read collision M1-PF, M1-BL"),\
    _CommonDef("CXBLPF", 0x36, "1.......  read collision BL-PF, unused"),\
    _CommonDef("CXPPMM", 0x37, "11......  read collision P0-P1, M0-M1"),\
    _CommonDef("INPT0", 0x38, "1.......  read pot port"),\
    _CommonDef("INPT1", 0x39, "1.......  read pot port"),\
    _CommonDef("INPT2", 0x3A, "1.......  read pot port"),\
    _CommonDef("INPT3", 0x3B, "1.......  read pot port"),\
    _CommonDef("INPT4", 0x3C, "1.......  read input"),\
    _CommonDef("INPT5", 0x3D, "1.......  read input"),\
    ], lambda _item: _item.value)

COMMON_A = col.ADict([\
    _CommonDef("SWCHA", 0x0280, "11111111  Port A; input or output  (read or write)"),\
    _CommonDef("SWACNT", 0x0281, "11111111  Port A DDR, 0= input, 1=output"),\
    _CommonDef("SWCHB", 0x0282, "11111111  Port B; console switches (read only)"),\
    _CommonDef("SWBCNT", 0x0283, "11111111  Port B DDR (hardwired as input)"),\
    _CommonDef("INTIM", 0x0284, "11111111  Timer output (read only)"),\
    _CommonDef("INSTAT", 0x0285, "11......  Timer Status (read only, undocumented)"),\
    _CommonDef("TIM1T", 0x0294, "11111111  set 1 clock interval (838 nsec/interval)"),\
    _CommonDef("TIM8T", 0x0295, "11111111  set 8 clock interval (6.7 usec/interval)"),\
    _CommonDef("TIM64T", 0x0296, "11111111  set 64 clock interval (53.6 usec/interval)"),\
    _CommonDef("T1024T", 0x0297, "11111111  set 1024 clock interval (858.2 usec/interval)"),\
    ], lambda _item: _item.value)

#endregion

class cmd_dis(cli.CLICommand):

    #region cli

    @property
    def _desc(self) -> None|str:
        return "Disassembles a ROM (NOTE: Bank switching not currently supported)"
    
    __rom = cli.CLIRequiredDef(\
        name = "rom",\
        desc = "ROM file (*.a26;*.bin)",\
        parse = cliutil.ParseUtil.to_path)
    
    __output = cli.CLIOptionWArgDef(\
        name = "output",\
        short = 'o',\
        desc = "Output file (*.asm)",\
        parse = cliutil.ParseUtil.to_path)

    __nocmn = cli.CLIOptionFlagDef(\
        name = "nocmn",\
        desc = "If specified, common definitions will not be used")

    #endregion

    #region helper methods

    @classmethod
    def __get_dest_addr(cls, ins_addr:int, ins:assutil.AsmIns):
        zp = ins.type.mode.input_type.type == assutil.AsmInsInputType.BIT8
        value = ins.type.mode.absaddr(ins_addr, ins.input)
        return _Addr(zp, value)
    
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
        output = cast(None|Path, self.output) # type: ignore
        nocmn = cast(bool, self.nocmn) # type: ignore
        if output is None: output = rom.with_suffix('.asm')
        try:
            # Read ROM
            addr_nmi = 0
            addr_entry = 0
            addr_break = 0
            rom_data:dict[int, bytes|assutil.AsmIns] = {}
            rom_bytes_read:set[int] = set()
            rom_address:set[_Addr] = set()
            with _Reader(rom) as _f:
                # Check size
                if _f.size < assutil.ROM_SIZE: raise cliutil.CommandError(\
                    f"ROM must have a size of {assutil.ROM_SIZE} bytes.")
                if _f.size > assutil.ROM_SIZE: raise cliutil.CommandError(\
                    "ROMs with bank switching are not supported. Output may be inaccurate.")
                # Entry, break
                _f.goto(assutil.ROM_VECTOR)
                addr_nmi = _Addr(False, _f.read_16())
                rom_address.add(addr_nmi)
                addr_entry = _Addr(False, _f.read_16())
                rom_address.add(addr_entry)
                addr_break = _Addr(False, _f.read_16())
                rom_address.add(addr_break)
                if addr_entry.value < assutil.ROM_BEG: raise cliutil.CommandError(\
                    f"Entry-point address ${addr_entry:04X} is out of range.")
                # Read instructions
                _branches:list[int] = [addr_entry.value]
                while len(_branches) > 0:
                    _f.goto(_branches.pop(0))
                    while not (_f.address in rom_bytes_read):
                        _ins_beg = _f.address
                        # Read opcode
                        _opcode = _f.read_8()
                        # Make sure opcode is valid
                        if not (_opcode in assutil.ASMINSTYPES): break
                        # Get instruction type
                        _ins_type = assutil.ASMINSTYPES[_opcode]
                        _ins_end = _ins_beg + _ins_type.mode.size
                        # Make sure there's no overlap
                        _overlapping = False
                        for _i in range(_ins_beg, _ins_end):
                            if not (_i in rom_bytes_read): continue
                            _overlapping = True
                            break
                        if _overlapping: break
                        # Read instruction
                        _ins_data = bytes([_opcode]) + _f.read(max(0, _ins_type.mode.size - 1))
                        _ins = assutil.AsmIns(data = _ins_data)
                        rom_data[_ins_beg] = _ins
                        # Mark as read
                        for _i in range(_ins_beg, _ins_end):
                            rom_bytes_read.add(_i)
                        # Copy destination address (if relevant)
                        if _ins_type.mode.input_is_addr:
                            _dest_addr = self.__get_dest_addr(_ins_beg, _ins)
                            rom_address.add(_dest_addr)
                            # Add "branch" (if relevant)
                            if _ins_type.prefix in [assutil.AsmInsPrefix.JMP, assutil.AsmInsPrefix.JSR]:
                                _branches.append(_dest_addr.value)
                            elif _ins_type.category == assutil.AsmInsTypeCat.BRANCH:
                                _branches.append(_dest_addr.value)
                        # Should we stop?
                        if _ins_type.category == assutil.AsmInsTypeCat.CTRL:
                            if _ins_type.prefix != assutil.AsmInsPrefix.JSR:
                                break
                # Gather non-instructional data
                _f.goto(_f.beg)
                while _f.address < assutil.ROM_VECTOR:
                    # Skip over instructional data
                    if _f.address in rom_bytes_read:
                        _addr = _f.address + 1
                        while _addr < assutil.ROM_VECTOR:
                            if not (_addr in rom_bytes_read): break
                            _addr += 1
                        _f.goto(_addr)
                        continue
                    # Get byte data; make sure important addresses are considered
                    _beg = _f.address
                    _bytes:list[int] = [_f.read_8()]
                    while _f.address < assutil.ROM_VECTOR:
                        if _f.address in rom_bytes_read: break
                        if _Addr(False, _f.address) in rom_address: break
                        if _Addr(True, _f.address) in rom_address: break
                        rom_bytes_read.add(_f.address)
                        _bytes.append(_f.read_8())
                    rom_data[_beg] = bytes(_bytes)
            # Go thru addresses
            nameaddrs:list[_NameAddr] = []
            addrs_labelled:dict[int, int] = {}
            addrs_unlabelled:dict[_Addr, int] = {}
            for _addr in rom_address:
                # Is it zero-page?
                if _addr.zp:
                    addrs_unlabelled[_addr] = len(nameaddrs)
                    nameaddrs.append(_NameAddr(f"ZP_{_addr.value:02X}", _addr))
                # No! Is it labelled?
                elif _addr.value in rom_data:
                    addrs_labelled[_addr.value] = len(nameaddrs)
                    nameaddrs.append(_NameAddr(f"L_{_addr.value:04X}", _addr))
                # No!
                else:
                    addrs_unlabelled[_addr] = len(nameaddrs)
                    nameaddrs.append(_NameAddr(f"A_{_addr.value:04X}", _addr))
            # Which addresses are common?
            cmnaddrs:dict[_Addr, None|str] = {}
            if not nocmn:
                for _i in range(len(nameaddrs)):
                    _item = nameaddrs[_i]
                    _newname = None
                    _comment = None
                    # Is this a zero-page address?
                    if _item.addr.zp:
                        if _item.addr.value in COMMON_ZP:
                            _newname = COMMON_ZP[_item.addr.value].name
                            _comment = COMMON_ZP[_item.addr.value].comment
                    # No!
                    else:
                        # Is this a common address?
                        if _item.addr.value in COMMON_A:
                            _newname = COMMON_A[_item.addr.value].name
                            _comment = COMMON_A[_item.addr.value].comment
                        # Is this a common zero-page address?
                        elif _item.addr.value in COMMON_ZP:
                            _newname = f"_{COMMON_ZP[_item.addr.value].name}"
                            _comment = None if (_Addr(True, _item.addr.value) in addrs_unlabelled)\
                                else COMMON_ZP[_item.addr.value].comment
                    # Update name
                    if _newname is not None:
                        nameaddrs[_i] = _NameAddr(_newname, _item.addr)
                        cmnaddrs[_item.addr] = _comment
            # Write output
            def get_addr_label(dest:_Addr):
                nonlocal nameaddrs, addrs_labelled, addrs_unlabelled
                # Is the address labelled?
                if (not dest.zp) and dest.value in addrs_labelled:
                    return nameaddrs[addrs_labelled[dest.value]].name
                # No! Is the address "macroed"?
                elif dest in addrs_unlabelled:
                    return nameaddrs[addrs_unlabelled[dest]].name
                # No!
                return str(dest)
            with cliutil.FileUtil.open_w(output) as _f:
                # Write entry and break
                _f.write(f"?NMI {get_addr_label(addr_nmi)}\n")
                _f.write(f"?ENTRY {get_addr_label(addr_entry)}\n")
                _f.write(f"?BREAK {get_addr_label(addr_break)}\n")
                _f.write('\n')
                # Write macros
                _macros_cmn = {_k: _v for _k, _v in addrs_unlabelled.items() if _k in cmnaddrs}
                if len(_macros_cmn) > 0:
                    _f.write(f"; Definitions shamelessly taken from {COMMON_URL}\n")
                    for _addr, _naindex in sorted(_macros_cmn.items(), key = lambda _item: _item[0]):
                        _comment = cmnaddrs[_addr]
                        _f.write(f"@DEFINE    {nameaddrs[_naindex].name!s:<11}")
                        if _comment is None: _f.write(f"{_addr!s:>5}\n")
                        else: _f.write(f"{_addr!s:>5}    ; {_comment}\n")
                    _f.write('\n')
                _macros_not = {_k: _v for _k, _v in addrs_unlabelled.items() if not (_k in cmnaddrs)}
                if len(_macros_not) > 0:
                    for _addr, _naindex in sorted(_macros_not.items(), key = lambda _item: _item[0]):
                        _f.write(f"@DEFINE    {nameaddrs[_naindex].name!s:<11}{_addr!s:>5}\n")
                    _f.write('\n')
                # Write data
                for _addr, _data in sorted(rom_data.items(), key = lambda item: item[0]):
                    # Write label (if one exists here)
                    if _addr in addrs_labelled:
                        _f.write('\n')
                        _f.write(f"{nameaddrs[addrs_labelled[_addr]].name}:\n")
                    # Is this a block of byte data?
                    if not isinstance(_data, assutil.AsmIns):
                        for _i in range(len(_data)):
                            if (_i % 16) == 0:
                                if _i > 0: _f.write('\n')
                                _f.write("!BYTE ")
                            else:
                                _f.write(", ")
                            _f.write(f"${_data[_i]:02X}")
                        _f.write('\n')
                    # No! 
                    else:
                        # Is the input an address?
                        if _data.type.mode.input_is_addr:
                            _name = get_addr_label(self.__get_dest_addr(_addr, _data))
                            _f.write(f"{self.__ins_input(_data, _name)}\n")
                        # No!
                        else: _f.write(f"{_data.gen_str(_addr)}\n")
                    # Next
            # Success!!!
            return 0
        except cliutil.CommandError as _e:
            print("ERROR", file = sys.stderr)
            print(_e, file = sys.stderr)
            return 1

    #endregion