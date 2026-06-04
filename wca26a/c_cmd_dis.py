__all__ = ['cmd_dis']

import sys

from typing import cast
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
        def _raise_if_oor(insaddr:int, destaddr:int):
            if (destaddr & 0xF000) == 0xF000: return
            raise cliutil.CommandError(f"${insaddr:04X} Address ${destaddr:04X} out of range.")
        try: 
            rom = cast(Path, self.rom) # type: ignore
            output = cast(None|Path, self.output) # type: ignore
            if output is None: output = rom.with_suffix('.asm')
            # Read rom
            rom_bytes = cliutil.FileUtil.read_all_bytes(rom)
            if len(rom_bytes) < 0x1000: raise cliutil.CommandError("ROM is invalid")
            # Create assembly
            asm = assutil.Asm()
            asm.addr_entry = rom_bytes[0xFFC] | (rom_bytes[0xFFD] << 8)
            asm.addr_break = rom_bytes[0xFFE] | (rom_bytes[0xFFF] << 8)
            _raise_if_oor(0xFFC, asm.addr_entry)
            # Disassemble
            _instructions:list[None|assutil.AsmIns] = [None for _ in range(0xFFC)]
            _branches = [asm.addr_entry]
            while len(_branches) > 0:
                _insbeg = _branches.pop() & 0xFFF
                while _insbeg < 0xFFC and _instructions[_insbeg] is None:
                    # Get opcode
                    _opcode = rom_bytes[_insbeg]
                    if not (_opcode in assutil.ASMINSTYPES):
                        raise cliutil.CommandError(f"${_insbeg:04X} Invalid opcode ${_opcode:02X}.")
                    # Get instruction
                    _instype = assutil.ASMINSTYPES[_opcode]
                    _insend = _insbeg + _instype.mode.size
                    _ins = assutil.AsmIns(data = rom_bytes[_insbeg:_insend])
                    # Make sure there's no overlap
                    _overlap = False
                    for _i in range(_insbeg + 1, _insend):
                        if _instructions[_i] is None: continue
                        _overlap = True
                        break
                    if _overlap: break
                    # Add instruction
                    for _i in range(_insbeg, _insend):
                        _instructions[_i] = _ins
                    # Next
                    if _instype.prefix == assutil.AsmInsPrefix.JMP:
                        _branches.append(_ins.input)
                        break
                    if _instype.prefix == assutil.AsmInsPrefix.JSR:
                        _branches.append(_ins.input)
                    elif _instype.mode.mode == assutil.AsmInsAddrMode.RELATIVE:
                        _branches.append(_instype.mode.absaddr(0xF000 | _insbeg, _ins.input))
                    _insbeg = _insend
            # Print to file
            out_lines:list[str] = []
            out_lines.append(f"!ENTRY ${asm.addr_entry:04X}")
            out_lines.append(f"!BREAK ${asm.addr_break:04X}")
            _offset = 0
            while _offset < 0xFFC:
                _instruction = _instructions[_offset]
                # Byte data
                if _instruction is None:
                    _bytes:list[int] = []
                    while _offset < 0xFFC and _instructions[_offset] is None:
                        _bytes.append(rom_bytes[_offset])
                        _offset += 1
                    while len(_bytes) > 16:
                        out_lines.append(assutil.AsmByteString(bytes(_bytes[:16])).gen_str(0))
                        for _ in range(16): _bytes.pop(0)
                    out_lines.append(assutil.AsmByteString(bytes(_bytes)).gen_str(0))
                    continue
                # Actual instruction
                out_lines.append(_instruction.gen_str(0xF000 | _offset))
                _offset += _instruction.type.mode.size
            assutil.FileUtil.write_all_lines(output, out_lines)
            # Success!!!
            return 0
        except cliutil.CommandError as _e:
            print("ERROR", file = sys.stderr)
            print(_e, file = sys.stderr)
            return 1

    #endregion