__all__ = ['cmd_dis']

import struct
import sys

from typing import Callable, cast
from pathlib import Path

import assutil
import cli
import cliutil

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

    #endregion

    #region methods

    def _main(self):
        rom = cast(Path, self.rom) # type: ignore
        output = cast(None|Path, self.output) # type: ignore
        if output is None: output = rom.with_suffix('.asm')
        # ROM
        rom_data:bytes = b''
        rom_ins:list[None|assutil.AsmIns]
        def rom_data_get(beg:int, size:int):
            nonlocal rom_data
            beg -= assutil.ROM_BEG
            return rom_data[beg:(beg + size)]
        def rom_ins_get(beg:int):
            nonlocal rom_ins
            beg -= assutil.ROM_BEG
            return rom_ins[beg]
        def rom_ins_vacant(beg:int, size:int):
            nonlocal rom_ins
            beg -= assutil.ROM_BEG
            for _ in range(size):
                if rom_ins[beg] is not None:
                    return False
                beg += 1
            return True
        def rom_ins_set(beg:int, ins:assutil.AsmIns):
            nonlocal rom_ins
            beg -= assutil.ROM_BEG
            for _ in range(ins.type.mode.size):
                rom_ins[beg] = ins
                beg += 1
        # Addresses
        ADDR_ZERO_PREFIX = "ZP_"
        ADDR_LABEL_PREFIX = "LABEL_"
        ADDR_MISC_PREFIX = "MISC_"
        def addr_pre(addr:int, s:str):
            nonlocal addr_carts, addr_miscs
            if addr >= assutil.ROM_BEG and addr < assutil.ROM_END:
                return s.replace("$", ADDR_LABEL_PREFIX)
            return s.replace("$", ADDR_MISC_PREFIX)
        def addr_prezp(addr:int, s:str):
            nonlocal ADDR_ZERO_PREFIX
            return s.replace("$", ADDR_ZERO_PREFIX)
        addr_zeros:set[int] = set() # Zero-page addresses
        addr_carts:set[int] = set() # Cartridge addresses
        addr_miscs:set[int] = set() # Misc addresses
        def addr_add(addr:int):
            nonlocal addr_carts, addr_miscs
            if addr >= assutil.ROM_BEG and addr < assutil.ROM_END:
                addr_carts.add(addr)
            else:
                addr_miscs.add(addr)
            return
        def addr_addzp(addr:int):
            nonlocal addr_zeros
            addr_zeros.add(addr)
        # Instruction types
        instype_prefuncs:dict[int, None|Callable[[int, str], str]] = {}
        instype_addfuncs:dict[int, None|Callable[[int], None]] = {}
        for _instype in assutil.ASMINSTYPES:
            _instype_prefunc:None|Callable[[int, str], str] = None
            _instype_addfunc:None|Callable[[int], None] = None
            if _instype.mode.mode == assutil.AsmInsAddrMode.ABSOLUTE or \
                    _instype.mode.mode == assutil.AsmInsAddrMode.X_INDEXED_ABSOLUTE or \
                    _instype.mode.mode == assutil.AsmInsAddrMode.Y_INDEXED_ABSOLUTE or \
                    _instype.mode.mode == assutil.AsmInsAddrMode.ABSOLUTE_INDIRECT or \
                    _instype.mode.mode == assutil.AsmInsAddrMode.RELATIVE:
                _instype_prefunc = addr_pre
                _instype_addfunc = addr_add
            elif _instype.mode.mode == assutil.AsmInsAddrMode.ZERO_PAGE or \
                    _instype.mode.mode == assutil.AsmInsAddrMode.X_INDEXED_ZERO_PAGE or \
                    _instype.mode.mode == assutil.AsmInsAddrMode.Y_INDEXED_ZERO_PAGE or \
                    _instype.mode.mode == assutil.AsmInsAddrMode.X_INDEXED_ZERO_PAGE_INDIRECT or \
                    _instype.mode.mode == assutil.AsmInsAddrMode.ZERO_PAGE_INDIRECT_Y_INDEXED:
                _instype_prefunc = addr_prezp
                _instype_addfunc = addr_addzp
            instype_prefuncs[_instype.opcode] = _instype_prefunc
            instype_addfuncs[_instype.opcode] = _instype_addfunc
        # Main code
        try:
            rom_data = cliutil.FileUtil.read_all_bytes(rom)
            rom_ins = [None for _ in range(assutil.ROM_BEG, assutil.ADDR_ENTRY)]
            if len(rom_data) < assutil.ROM_SIZE: raise cliutil.CommandError("ROM size is invalid")
            # Create assembly
            asm = assutil.Asm()
            asm.addr_entry = struct.unpack('<H', rom_data_get(assutil.ADDR_ENTRY, 2))[0]
            asm.addr_break = struct.unpack('<H', rom_data_get(assutil.ADDR_BREAK, 2))[0]
            if asm.addr_entry < assutil.ROM_BEG or asm.addr_entry > assutil.ROM_END:
                raise cliutil.CommandError(f"${assutil.ADDR_ENTRY:04X} Address ${asm.addr_entry:04X} out of range.")
            # Disassemble
            _branches = [asm.addr_entry]
            while len(_branches) > 0:
                _address = _branches.pop()
                if _address < assutil.ROM_BEG or _address > assutil.ROM_END:
                    continue
                while _address < assutil.ADDR_ENTRY and rom_ins_get(_address) is None:
                    # Get opcode
                    _opcode = rom_data_get(_address, 1)[0]
                    if not (_opcode in assutil.ASMINSTYPES): break
                    # Get instruction
                    _instype = assutil.ASMINSTYPES[_opcode]
                    if not rom_ins_vacant(_address, _instype.mode.size): break
                    _ins = assutil.AsmIns(data = rom_data_get(_address, _instype.mode.size))
                    rom_ins_set(_address, _ins)
                    # Add address (if relevant)
                    _inputaddr = _instype.mode.absaddr(_address, _ins.input)
                    _addfunc = instype_addfuncs[_opcode]
                    if _addfunc is not None: _addfunc(_inputaddr)
                    # Add branch (if relevant)
                    if _instype.prefix == assutil.AsmInsPrefix.JMP:
                        _branches.append(_inputaddr)
                        break
                    if _instype.prefix == assutil.AsmInsPrefix.JSR or\
                            _instype.mode.mode == assutil.AsmInsAddrMode.RELATIVE:
                        _branches.append(_inputaddr)
                    # Next
                    _address += _instype.mode.size
            # Print to file
            with cliutil.FileUtil.open_w(output) as _f:
                # Entry-point, break-point
                _f.write(f"!ENTRY ${asm.addr_entry:04X}\n")
                _f.write(f"!BREAK ${asm.addr_break:04X}\n")
                # Zero-page addresses
                if len(addr_zeros) > 0:    
                    _f.write('\n')
                    for _addr in addr_zeros:
                        _f.write(f"@DEFINE {ADDR_ZERO_PREFIX}{_addr:02X} ${_addr:02X}\n")
                # Misc addresses
                if len(addr_miscs) > 0:
                    _f.write('\n')
                    for _addr in addr_miscs:
                        _f.write(f"@DEFINE {ADDR_MISC_PREFIX}{_addr:04X} ${_addr:04X}\n")
                # Instructions/data
                _lines:list[tuple[None|tuple[int, str], str]] = []
                _labelled:set[int] = set()
                _address = assutil.ROM_BEG
                while _address < assutil.ADDR_ENTRY:
                    _ins = rom_ins_get(_address)
                    # Is this a labelled address
                    if _address in addr_carts:
                        _lines.append((None, f"\n{ADDR_LABEL_PREFIX}{_address:04X}:"))
                        _labelled.add(_address)
                    # Is this byte data?
                    if _ins is None:
                        _bytes:list[int] = [rom_data_get(_address, 1)[0]]
                        _address += 1 # We already know this isn't an instruction
                        while True:
                            _stop = _address == assutil.ADDR_ENTRY or rom_ins_get(_address) is not None
                            if _stop or _address in addr_carts:
                                # Write bytes
                                if len(_bytes) > 0:
                                    while len(_bytes) > 16:
                                        _lines.append((None, assutil.AsmByteString(bytes(_bytes[:16])).gen_str(0)))
                                        for _ in range(16): _bytes.pop(0)
                                    _lines.append((None, assutil.AsmByteString(bytes(_bytes)).gen_str(0)))
                                    _bytes.clear()
                                if _stop: break
                                # Write label
                                _lines.append((None, f"\n{ADDR_LABEL_PREFIX}{_address:04X}:"))
                                _labelled.add(_address)
                            _bytes.append(rom_data_get(_address, 1)[0])
                            _address += 1
                        continue
                    # No!
                    _ins_str = _ins.gen_str(_address)
                    _ins_prefunc = instype_prefuncs[_ins.type.opcode]
                    if _ins_prefunc is not None:
                        _ins_absaddr = _ins.type.mode.absaddr(_address, _ins.input)
                        _ins_prefixed = _ins_prefunc(_ins_absaddr, _ins_str)
                        _lines.append(((_ins_absaddr, _ins_prefixed), _ins_str))
                    else:
                        _lines.append((None, _ins_str))
                    _address += _ins.type.mode.size
                _f.write('\n')
                for _pre, _str in _lines:
                    _sstr = _str
                    # Fix for declared labels and macros
                    if _pre is not None:
                        _adr, _pfx = _pre
                        if _adr in addr_zeros or _adr in addr_miscs or _adr in _labelled:
                            _sstr = _pfx
                    # Write line
                    _f.write(f"{_sstr}\n")
            # Success!!!
            return 0
        except cliutil.CommandError as _e:
            print("ERROR", file = sys.stderr)
            print(_e, file = sys.stderr)
            return 1

    #endregion