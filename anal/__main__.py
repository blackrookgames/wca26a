import sys
from pathlib import Path

SRC_FILE = Path(__file__).resolve()
SRC_DIR = SRC_FILE.parent
PRJ_DIR = SRC_DIR.parent
sys.path.insert(0, str(PRJ_DIR.joinpath("engine")))

import boacon
import sys
import time

from dataclasses import dataclass
from io import StringIO
from typing import Callable, cast
from pathlib import Path

import assutil
import cli
import cliutil
import col

import emu
import panes

#region Instruction

@dataclass(frozen = True)
class Instruction:
    """ Represents an executed instruction """
    addr:int
    """ Address of instruction """
    ins:assutil.AsmIns
    """ Actual instruction """

#endregion

#region Program

class Program:
    """ Represents a program """

    #region init

    def __init__(self, rom:bytes, nogarb:bool, stackwrap:bool):
        """
        Initializer for Program

        :param rom: ROM data
        :param nogarb: If true, initial garbage data will not be emulated
        :param stackwrap: If true, stack pointer will wrap upon overflow/underflow; otherwise an EmuError is raised
        :raise ValueError: rom does not have a length of 4096
        """
        if len(rom): ValueError(f"rom must have a length of {assutil.ROM_SIZE}")
        self.__instructions = self.__get_instructions()
        self.__rom = rom
        self.__nogarb = nogarb
        self.__stackwrap = stackwrap
        self.reset()

    #endregion

    #region fields

    __rom:bytes
    __nogarb:bool
    __stackwrap:bool

    __system:emu.System
    __error:None|str
    __previous:None|Instruction

    #endregion

    #region properties

    @property
    def system(self):
        """ System data """
        return self.__system
    
    @property
    def error(self):
        """ If not None, it means an error occurred during the last step and the program will need to be reset. """
        return self.__error

    @property
    def previous(self):
        """ Previously executed instruction """
        return self.__previous

    #endregion

    #region methods

    def reset(self):
        """ Resets the program """
        # Recreate system
        self.__system = emu.System(self.__nogarb, self.__stackwrap)
        # Add ROM
        self.__system.memory.populate(assutil.ROM_BEG, self.__rom)
        # Goto entry point
        self.__system.memory.goto(self.__system.memory.ptr_entry)
        # Reset error state
        self.__error = None

    def step(self):
        """
        Steps thru the program.\n
        If an error occurred during the last step, nothing happens.
        """
        # Make sure there's no error
        if self.__error is not None: return
        # Make note of current position
        _pos = self.__system.memory.pos
        # Read and execute
        try:
            # Read opcode
            _ins_opcode = self.__system.memory.read_8()
            # Get instruction type
            if not (_ins_opcode in assutil.ASMINSTYPES):
                raise emu.EmuError(f"Invalid opcode ${_ins_opcode:02X}")
            _ins_type = assutil.ASMINSTYPES[_ins_opcode]
            # Read instruction
            _ins_data = bytes([_ins_opcode]) + self.__system.memory.read(max(0, _ins_type.mode.size - 1))
            _ins = Instruction(_pos, assutil.AsmIns(data = _ins_data))
            # Perform instruction
            self.__instructions[_ins_type.prefix.name](self, _ins) # type: ignore
            # Update previous
            self.__previous = _ins
        except emu.EmuError as _e:
            self.__error = f"${_pos:04X}: {_e}"

    #endregion

    #region instructions

    @classmethod
    def __get_instructions(cls):
        PREFIX = '__ins_'
        instructions:dict[str, Callable] = {}
        for _attrname in dir(cls):
            _attr = getattr(cls, _attrname)
            if not callable(_attr): continue
            if not _attr.__name__.startswith(PREFIX): continue
            instructions[_attr.__name__[len(PREFIX):]] = _attr.__call__
        return col.RoDict[str, Callable](instructions)

    #region helper

    @classmethod
    def __get_value(cls, system:emu.System, ins:Instruction):
        if ins.ins.type.mode.mode == assutil.AsmInsAddrMode.ACCUMULATOR:
            return system.cpu.a
        if ins.ins.type.mode.mode == assutil.AsmInsAddrMode.IMMEDIATE:
            return ins.ins.input
        if ins.ins.type.mode.input_is_addr:
            return system.memory[ins.ins.type.mode.absaddr(ins.addr, ins.ins.input)]
        return 0

    def __set_value(self, ins:Instruction, value:int):
        if ins.ins.type.mode.mode == assutil.AsmInsAddrMode.ACCUMULATOR:
            self.__system.cpu.a = value
        elif ins.ins.type.mode.input_is_addr:
            self.__system.memory[ins.ins.type.mode.absaddr(ins.addr, ins.ins.input)] = value
    
    def __update_nz(self, value:int):
        self.__system.cpu.flags = self.__system.cpu.flags.set_multi((\
            (emu.CPUFlags.NEGATIVE, (value & 0b10000000) != 0),\
            (emu.CPUFlags.ZERO, value == 0),))
        
    def __print_if_peek(self, dest:int):
        # if system.peek is None: return
        # if system.peek == dest: print(f"${system.memory[dest]:02X}")
        pass

    #endregion

    #region load/store
    
    def __ins_LDA(self, ins:Instruction):
        self.__system.cpu.a = self.__get_value(self.__system, ins)
        self.__update_nz(self.__system.cpu.a)

    def __ins_LDX(self, ins:Instruction):
        self.__system.cpu.x = self.__get_value(self.__system, ins)
        self.__update_nz(self.__system.cpu.x)

    def __ins_LDY(self, ins:Instruction):
        self.__system.cpu.y = self.__get_value(self.__system, ins)
        self.__update_nz(self.__system.cpu.y)
    
    def __ins_STA(self, ins:Instruction):
        dest = ins.ins.type.mode.absaddr(ins.addr, ins.ins.input)
        self.__system.memory[dest] = self.__system.cpu.a
        self.__print_if_peek(dest)
    
    def __ins_STX(self, ins:Instruction):
        dest = ins.ins.type.mode.absaddr(ins.addr, ins.ins.input)
        self.__system.memory[dest] = self.__system.cpu.x
        self.__print_if_peek(dest)
    
    def __ins_STY(self, ins:Instruction):
        dest = ins.ins.type.mode.absaddr(ins.addr, ins.ins.input)
        self.__system.memory[dest] = self.__system.cpu.y
        self.__print_if_peek(dest)

    #endregion

    #region transfer
    
    def __ins_TAX(self, ins:Instruction):
        self.__system.cpu.x = self.__system.cpu.a
        self.__update_nz(self.__system.cpu.x)
    
    def __ins_TAY(self, ins:Instruction):
        self.__system.cpu.y = self.__system.cpu.a
        self.__update_nz(self.__system.cpu.x)
    
    def __ins_TSX(self, ins:Instruction):
        self.__system.cpu.x = self.__system.cpu.stack.pos
        self.__update_nz(self.__system.cpu.x)
    
    def __ins_TXA(self, ins:Instruction):
        self.__system.cpu.a = self.__system.cpu.x
        self.__update_nz(self.__system.cpu.a)
    
    def __ins_TXS(self, ins:Instruction):
        self.__system.cpu.stack.pos = self.__system.cpu.x
    
    def __ins_TYA(self, ins:Instruction):
        self.__system.cpu.a = self.__system.cpu.y
        self.__update_nz(self.__system.cpu.a)

    #endregion

    #region stack
    
    def __ins_PHA(self, ins:Instruction):
        self.__system.cpu.stack.push(self.__system.cpu.a)
    
    def __ins_PHP(self, ins:Instruction):
        self.__system.cpu.stack.push(self.__system.cpu.flags.value)

    def __ins_PLA(self, ins:Instruction):
        self.__system.cpu.a = self.__system.cpu.stack.pull()
        self.__update_nz(self.__system.cpu.a)
    
    def __ins_PLP(self, ins:Instruction):
        self.__system.cpu.flags = emu.CPUFlags(self.__system.cpu.stack.pull())

    #endregion

    #region bit-shift
    
    def __ins_ASL(self, ins:Instruction):
        old = self.__get_value(self.__system, ins)
        new = (old << 1) & 0xFF
        self.__set_value(ins, new)
        self.__update_nz(new)
        self.__system.cpu.flags = self.__system.cpu.flags.set(emu.CPUFlags.CARRY, (old & 0x80) != 0)
    
    def __ins_LSR(self, ins:Instruction):
        old = self.__get_value(self.__system, ins)
        new = old >> 1
        self.__set_value(ins, new)
        self.__update_nz(new)
        self.__system.cpu.flags = self.__system.cpu.flags.set(emu.CPUFlags.CARRY, (old & 0x01) != 0)
    
    def __ins_ROL(self, ins:Instruction):
        old = self.__get_value(self.__system, ins)
        new = ((old << 1) & 0xFF) | (0x01 if self.__system.cpu.flags.isset(emu.CPUFlags.CARRY) else 0x00)
        self.__set_value(ins, new)
        self.__update_nz(new)
        self.__system.cpu.flags = self.__system.cpu.flags.set(emu.CPUFlags.CARRY, (old & 0x80) != 0)
    
    def __ins_ROR(self, ins:Instruction):
        old = self.__get_value(self.__system, ins)
        new = (old >> 1) | (0x80 if self.__system.cpu.flags.isset(emu.CPUFlags.CARRY) else 0x00)
        self.__set_value(ins, new)
        self.__update_nz(new)
        self.__system.cpu.flags = self.__system.cpu.flags.set(emu.CPUFlags.CARRY, (old & 0x01) != 0)
    
    #endregion

    #region logic

    def __ins_AND(self, ins:Instruction):
        self.__system.cpu.a &= self.__get_value(self.__system, ins)
        self.__update_nz(self.__system.cpu.a)
    
    def __ins_BIT(self, ins:Instruction):
        value = self.__get_value(self.__system, ins)
        self.__system.cpu.flags = self.__system.cpu.flags.set_multi((\
            (emu.CPUFlags.NEGATIVE, (value & 0b10000000) != 0),\
            (emu.CPUFlags.OVERFLOW, (value & 0b01000000) != 0),\
            (emu.CPUFlags.ZERO, (self.__system.cpu.a & value) == 0),))
    
    def __ins_EOR(self, ins:Instruction):
        self.__system.cpu.a ^= self.__get_value(self.__system, ins)
        self.__update_nz(self.__system.cpu.a)
    
    def __ins_ORA(self, ins:Instruction):
        self.__system.cpu.a |= self.__get_value(self.__system, ins)
        self.__update_nz(self.__system.cpu.a)
    
    #endregion

    #region arithmetic

    def __ins_ADC(self, ins:Instruction):
        # TODO: Ensure calculations are correct
        value = self.__system.cpu.a + self.__get_value(self.__system, ins) +\
            (1 if self.__system.cpu.flags.isset(emu.CPUFlags.CARRY) else 0)
        old = self.__system.cpu.a
        self.__system.cpu.a = value & 0xFF
        # Determine carry
        if self.__system.cpu.flags.isset(emu.CPUFlags.DECIMAL):
            carry = value > 99
        else:
            carry = value > 0xFF
        # Update flags
        self.__system.cpu.flags = self.__system.cpu.flags.set_multi((\
            (emu.CPUFlags.CARRY, carry),\
            (emu.CPUFlags.OVERFLOW, (old & 0x80) != (self.__system.cpu.a & 0x80))))
        self.__update_nz(self.__system.cpu.a)
    
    def __ins_CMP(self, ins:Instruction):
        value = self.__system.cpu.a - self.__get_value(self.__system, ins)
        self.__system.cpu.flags = self.__system.cpu.flags.set(emu.CPUFlags.CARRY, value >= 0)
        self.__update_nz(value)
    
    def __ins_CPX(self, ins:Instruction):
        value = self.__system.cpu.x - self.__get_value(self.__system, ins)
        self.__system.cpu.flags = self.__system.cpu.flags.set(emu.CPUFlags.CARRY, value >= 0)
        self.__update_nz(value)
    
    def __ins_CPY(self, ins:Instruction):
        value = self.__system.cpu.y - self.__get_value(self.__system, ins)
        self.__system.cpu.flags = self.__system.cpu.flags.set(emu.CPUFlags.CARRY, value >= 0)
        self.__update_nz(value)
    
    def __ins_SBC(self, ins:Instruction):
        # TODO: Ensure calculations are correct
        value = self.__system.cpu.a - self.__get_value(self.__system, ins) -\
            (0 if self.__system.cpu.flags.isset(emu.CPUFlags.CARRY) else 1)
        old = self.__system.cpu.a
        self.__system.cpu.a = (0x100 + value) & 0xFF
        # Update flags
        self.__system.cpu.flags = self.__system.cpu.flags.set_multi((\
            (emu.CPUFlags.CARRY, value >= 0 ),\
            (emu.CPUFlags.OVERFLOW, (old & 0x80) != (self.__system.cpu.a & 0x80))))
        self.__update_nz(self.__system.cpu.a)
    
    #endregion

    #region increment/decrement

    def __ins_DEC(self, ins:Instruction):
        value = (self.__get_value(self.__system, ins) + 0xFF) & 0xFF
        self.__set_value(ins, value)
        self.__update_nz(value)

    def __ins_DEX(self, ins:Instruction):
        self.__system.cpu.x = (self.__system.cpu.x + 0xFF) & 0xFF
        self.__update_nz(self.__system.cpu.x)
        
    def __ins_DEY(self, ins:Instruction):
        self.__system.cpu.y = (self.__system.cpu.y + 0xFF) & 0xFF
        self.__update_nz(self.__system.cpu.y)
    
    def __ins_INC(self, ins:Instruction):
        value = (self.__get_value(self.__system, ins) + 1) & 0xFF
        self.__set_value(ins, value)
        self.__update_nz(value)

    def __ins_INX(self, ins:Instruction):
        self.__system.cpu.x = (self.__system.cpu.x + 1) & 0xFF
        self.__update_nz(self.__system.cpu.x)
        
    def __ins_INY(self, ins:Instruction):
        self.__system.cpu.y = (self.__system.cpu.y + 1) & 0xFF
        self.__update_nz(self.__system.cpu.y)
    
    #endregion

    #region control

    def __ins_BRK(self, ins:Instruction):
        # Push return position onto stack
        pos = self.__system.memory.pos + 1
        self.__system.cpu.stack.push((pos & 0xFF00) >> 8)
        self.__system.cpu.stack.push(pos & 0x00FF)
        # Push flags onto stack
        self.__system.cpu.stack.push(self.__system.cpu.flags.value)
        # Disable interrupts
        self.__system.cpu.flags.set(emu.CPUFlags.INTDIS, True)
        # Goto break point
        self.__system.memory.goto(self.__system.memory.ptr_break)

    def __ins_JMP(self, ins:Instruction):
        if ins.ins.type.mode.mode == assutil.AsmInsAddrMode.ABSOLUTE_INDIRECT:
            raise emu.EmuError("JMP ($nnnn) is not yet supported")
        self.__system.memory.goto(ins.ins.type.mode.absaddr(ins.addr, ins.ins.input))

    def __ins_JSR(self, ins:Instruction):
        self.__system.cpu.stack.push((self.__system.memory.pos & 0xFF00) >> 8)
        self.__system.cpu.stack.push(self.__system.memory.pos & 0x00FF)
        self.__system.memory.goto(ins.ins.type.mode.absaddr(ins.addr, ins.ins.input))

    def __ins_RTI(self, ins:Instruction):
        # Restore flags
        self.__system.cpu.flags = emu.CPUFlags(self.__system.cpu.stack.pull())
        # Restore position
        dest_lo = self.__system.cpu.stack.pull()
        dest_hi = self.__system.cpu.stack.pull()
        self.__system.memory.goto((dest_hi << 8) | dest_lo)

    def __ins_RTS(self, ins:Instruction):
        dest_lo = self.__system.cpu.stack.pull()
        dest_hi = self.__system.cpu.stack.pull()
        self.__system.memory.goto((dest_hi << 8) | dest_lo)
    
    #endregion
    
    #region branch

    def __ins_BCC(self, ins:Instruction):
        if self.__system.cpu.flags.isset(emu.CPUFlags.CARRY): return
        self.__system.memory.goto(ins.ins.type.mode.absaddr(ins.addr, ins.ins.input))

    def __ins_BCS(self, ins:Instruction):
        if not self.__system.cpu.flags.isset(emu.CPUFlags.CARRY): return
        self.__system.memory.goto(ins.ins.type.mode.absaddr(ins.addr, ins.ins.input))

    def __ins_BEQ(self, ins:Instruction):
        if not self.__system.cpu.flags.isset(emu.CPUFlags.ZERO): return
        self.__system.memory.goto(ins.ins.type.mode.absaddr(ins.addr, ins.ins.input))

    def __ins_BMI(self, ins:Instruction):
        if not self.__system.cpu.flags.isset(emu.CPUFlags.NEGATIVE): return
        self.__system.memory.goto(ins.ins.type.mode.absaddr(ins.addr, ins.ins.input))

    def __ins_BNE(self, ins:Instruction):
        if self.__system.cpu.flags.isset(emu.CPUFlags.ZERO): return
        self.__system.memory.goto(ins.ins.type.mode.absaddr(ins.addr, ins.ins.input))

    def __ins_BPL(self, ins:Instruction):
        if self.__system.cpu.flags.isset(emu.CPUFlags.NEGATIVE): return
        self.__system.memory.goto(ins.ins.type.mode.absaddr(ins.addr, ins.ins.input))

    def __ins_BVC(self, ins:Instruction):
        if self.__system.cpu.flags.isset(emu.CPUFlags.OVERFLOW): return
        self.__system.memory.goto(ins.ins.type.mode.absaddr(ins.addr, ins.ins.input))

    def __ins_BVS(self, ins:Instruction):
        if not self.__system.cpu.flags.isset(emu.CPUFlags.OVERFLOW): return
        self.__system.memory.goto(ins.ins.type.mode.absaddr(ins.addr, ins.ins.input))

    #endregion

    #region flags
    
    def __ins_CLC(self, ins:Instruction):
        self.__system.cpu.flags.set(emu.CPUFlags.CARRY, False)
    
    def __ins_CLD(self, ins:Instruction):
        self.__system.cpu.flags.set(emu.CPUFlags.DECIMAL, False)
    
    def __ins_CLI(self, ins:Instruction):
        self.__system.cpu.flags.set(emu.CPUFlags.INTDIS, False)
    
    def __ins_CLV(self, ins:Instruction):
        self.__system.cpu.flags.set(emu.CPUFlags.OVERFLOW, False)
    
    def __ins_SEC(self, ins:Instruction):
        self.__system.cpu.flags.set(emu.CPUFlags.CARRY, True)
    
    def __ins_SED(self, ins:Instruction):
        self.__system.cpu.flags.set(emu.CPUFlags.DECIMAL, True)
    
    def __ins_SEI(self, ins:Instruction):
        self.__system.cpu.flags.set(emu.CPUFlags.INTDIS, True)

    #endregion

    #region nop
    
    def __ins_NOP(self, ins:Instruction):
        pass

    #endregion

    #endregion

#endregion

class command(cli.CLICommand):

    #region cli

    @property
    def _desc(self) -> None|str:
        return "Crappy analyzer of ROM code"
    
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

    #region init

    def __init__(self):
        super().__init__()
        self.__time_alive = 0

    #endregion

    #region const

    __DELAY = 0.001

    #endregion

    #region receivers

    def __postdraw(self, args:boacon.BCPostDrawArgs):
        # args.win.addstr(0, 1, f"{self.__time_alive:.2f} sec")
        pass

    def __on_init(self):
        boacon.postdraw().connect(self.__postdraw)

    def __on_final(self):
        boacon.postdraw().disconnect(self.__postdraw)

    #endregion

    #region methods

    def _main(self):
        rom = cast(Path, self.rom) # type: ignore
        nogarb = cast(bool, self.nogarb) # type: ignore
        stackwrap = cast(bool, self.stackwrap) # type: ignore
        try:
            # Load ROM
            rom_data = cliutil.FileUtil.read_all_bytes(rom)
            if len(rom_data) < assutil.ROM_SIZE: raise cliutil.CommandError(\
                f"ROM must have a size of {assutil.ROM_SIZE} bytes.")
            # Run boacon
            boacon.on_init().connect(self.__on_init)
            boacon.on_final().connect(self.__on_final)
            boacon.init()
            try:
                # Create program
                program = Program(rom_data[:assutil.ROM_SIZE], nogarb, stackwrap)
                def program_step():
                    nonlocal program
                    nonlocal gencon, view_history, view_stack, view_status
                    if program.error is not None: return
                    # Get system info
                    _sys_pos = program.system.memory.pos
                    _sys_flags = program.system.cpu.flags
                    _sys_a = program.system.cpu.a
                    _sys_x = program.system.cpu.x
                    _sys_y = program.system.cpu.y
                    # Step thru program
                    program.step()
                    # Did everything go okay?
                    if program.error is None:
                        # Update history view
                        assert program.previous is not None
                        view_history.log(panes.InsHisViewEntry(\
                            program.previous.addr, program.previous.ins,\
                            panes.InsHisViewEntryRegState(\
                                _sys_a,\
                                _sys_x,\
                                _sys_y,\
                                _sys_flags),\
                            panes.InsHisViewEntryRegState(\
                                program.system.cpu.a,\
                                program.system.cpu.x,\
                                program.system.cpu.y,\
                                program.system.cpu.flags)\
                            ))
                        # Update stack view
                        view_stack.refresh()
                        # Update status view
                        view_status.refresh()
                    # No! An error occurred!
                    else:
                        gencon.print(program.error)
                # General console
                gencon = boacon.BCConsolePane()
                gencon.x.dis0 = 1
                gencon.x.len = 30
                gencon.y.dis1 = 1
                gencon.y.len = 10
                boacon.panes().append(gencon)
                # History view
                view_history = panes.InsHisView()
                view_history.x.dis0 = 32
                view_history.x.dis1 = 1
                view_history.y.dis1 = 1
                view_history.y.len = 10
                boacon.panes().append(view_history)
                # Stack view
                view_stack = panes.StackView(program.system.cpu.stack)
                view_stack.x.dis0 = 1
                view_stack.x.len = 9
                view_stack.y.dis0 = 1
                view_stack.y.dis1 = 12
                boacon.panes().append(view_stack)
                # Status view
                view_status = panes.StatusView(program.system)
                view_status.x.dis0 = 11
                view_status.x.len = 9
                view_status.y.dis0 = 1
                view_status.y.dis1 = 12
                boacon.panes().append(view_status)
                # Warn user if ROM requires bank switching
                if len(rom_data) > assutil.ROM_SIZE: gencon.print(\
                    "ROMs with bank switching are not supported.")
                # Run thru program
                gencon.print("Press Space to Step")
                gencon.print("Press Esc to Quit")
                while True:
                    # Check input
                    ch = boacon.getch()
                    if ch == 0x1B: break
                    if ch == 0x20: program_step()
                    # Refresh
                    boacon.refresh()
                    time.sleep(self.__DELAY)
            except emu.EmuError as _e:
                raise cliutil.CommandError(_e)
            finally:
                boacon.final()

            # Success!!!
            return 0
        except cliutil.CommandError as _e:
            print("ERROR", file = sys.stderr)
            print(_e, file = sys.stderr)
            return 1
        
    #endregion

if __name__ == '__main__':
    sys.exit(command().execute(sys.argv))