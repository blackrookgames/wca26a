__all__ = ['StatusView', 'StatusViewState']

import boacon as _boacon

from dataclasses import\
    dataclass as _dataclass
from enum import\
    auto as _auto,\
    Enum as _Enum

import emu as _emu
import help as _help

from .c_SurfacePaneBase import\
    SurfacePaneBase as _SurfacePaneBase

class StatusViewState(_Enum):
    NOTRUNNING = _auto()
    RUNNING = _auto()
    PAUSED = _auto()
    ERROR = _auto()

class StatusView(_SurfacePaneBase):
    """ Represents a view of system status """

    #region const

    __SPACE = _boacon.BCChar(0x20)

    __REG_N = _boacon.BCChar(ord('N'))
    __REG_V = _boacon.BCChar(ord('V'))
    __REG_E = _boacon.BCChar(ord('-'))
    __REG_B = _boacon.BCChar(ord('B'))
    __REG_D = _boacon.BCChar(ord('D'))
    __REG_I = _boacon.BCChar(ord('I'))
    __REG_Z = _boacon.BCChar(ord('Z'))
    __REG_C = _boacon.BCChar(ord('C'))
    __REG_0 = _boacon.BCChar(ord('0'))
    __REG_1 = _boacon.BCChar(ord('1'))

    __HEAD_PC       = "PC     "
    __HEAD_FLAGS    = "NV-BDIZC "
    __HEAD_A        = "A   "
    __HEAD_X        = "X   "
    __HEAD_Y        = "Y   "
    __HEAD =\
        __HEAD_PC +\
        __HEAD_FLAGS +\
        __HEAD_A +\
        __HEAD_X +\
        __HEAD_Y

    #endregion

    #region init

    def __init__(self, system:_emu.System):
        """
        Initializer for StatusView

        :param system: System
        """
        super().__init__()
        self.__system = system
        self._surface.resize(35, 3)
        # Registers
        self._surface.set(22, 0, self.__REG_N)
        self._surface.set(23, 0, self.__REG_V)
        self._surface.set(24, 0, self.__REG_E)
        self._surface.set(25, 0, self.__REG_B)
        self._surface.set(26, 0, self.__REG_D)
        self._surface.set(27, 0, self.__REG_I)
        self._surface.set(28, 0, self.__REG_Z)
        self._surface.set(29, 0, self.__REG_C)
        # Program counter
        self.__print(0, 0, "PC")
        self.__print(7, 0, "A")
        self.__print(12, 0, "X")
        self.__print(17, 0, "Y")
        # State
        self.__state:StatusViewState = StatusViewState.NOTRUNNING

    #endregion

    #region properties

    @property
    def state(self):
        """
        Program state\n
        This has to be manually modified
        """
        return self.__state
    @state.setter
    def state(self, value:StatusViewState):
        if self.__state == value: return
        self.__state = value
        self.refresh()

    #endregion

    #region helper methods

    def __print(self, x:int, y:int, s:str):
        for _c in s:
            self._surface.set(x, y, _boacon.BCChar(ord(_c)))
            x += 1

    #endregion

    #region methods

    def refresh(self):
        """
        Refreshes the register view.\n
        A manual refresh is neccessary as the register view can't detect when the system changes state.
        """
        # Registers
        self._surface.set(22, 1, self.__REG_1 if self.__system.cpu.flags.isset(_emu.CPUFlags.NEGATIVE) else self.__REG_0)
        self._surface.set(23, 1, self.__REG_1 if self.__system.cpu.flags.isset(_emu.CPUFlags.OVERFLOW) else self.__REG_0)
        self._surface.set(24, 1, self.__REG_1 if self.__system.cpu.flags.isset(_emu.CPUFlags.EXPANSION) else self.__REG_0)
        self._surface.set(25, 1, self.__REG_1 if self.__system.cpu.flags.isset(_emu.CPUFlags.BREAK) else self.__REG_0)
        self._surface.set(26, 1, self.__REG_1 if self.__system.cpu.flags.isset(_emu.CPUFlags.DECIMAL) else self.__REG_0)
        self._surface.set(27, 1, self.__REG_1 if self.__system.cpu.flags.isset(_emu.CPUFlags.INTDIS) else self.__REG_0)
        self._surface.set(28, 1, self.__REG_1 if self.__system.cpu.flags.isset(_emu.CPUFlags.ZERO) else self.__REG_0)
        self._surface.set(29, 1, self.__REG_1 if self.__system.cpu.flags.isset(_emu.CPUFlags.CARRY) else self.__REG_0)
        # Program counter
        self.__print(0, 1, f"${self.__system.memory.pos:04X}")
        self.__print(7, 1, f"${self.__system.cpu.a:02X}")
        self.__print(12, 1, f"${self.__system.cpu.x:02X}")
        self.__print(17, 1, f"${self.__system.cpu.y:02X}")
        # Status
        self.__print(0, 2, _help.StrUtil.ljusttrun(self.__state.name, self._surface.width))

    #endregion