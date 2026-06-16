__all__ = ['StatusView']

import boacon as _boacon

from dataclasses import\
    dataclass as _dataclass

import assutil as _assutil
import emu as _emu

from .c_SurfacePaneBase import\
    SurfacePaneBase as _SurfacePaneBase

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
        :raises ValueError: maxsize is less than zero
        """
        super().__init__()
        self.__system = system
        self._surface.resize(10, 14)
        # Registers
        self._surface.set(0, 5, self.__REG_N)
        self._surface.set(0, 6, self.__REG_V)
        self._surface.set(0, 7, self.__REG_E)
        self._surface.set(0, 8, self.__REG_B)
        self._surface.set(0, 9, self.__REG_D)
        self._surface.set(0, 10, self.__REG_I)
        self._surface.set(0, 11, self.__REG_Z)
        self._surface.set(0, 12, self.__REG_C)
        # Program counter
        self.__print(0, 0, "PC")
        self.__print(0, 1, "A")
        self.__print(0, 2, "X")
        self.__print(0, 3, "Y")

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
        self._surface.set(4, 5, self.__REG_1 if self.__system.cpu.flags.isset(_emu.CPUFlags.NEGATIVE) else self.__REG_0)
        self._surface.set(4, 6, self.__REG_1 if self.__system.cpu.flags.isset(_emu.CPUFlags.OVERFLOW) else self.__REG_0)
        self._surface.set(4, 7, self.__REG_1 if self.__system.cpu.flags.isset(_emu.CPUFlags.EXPANSION) else self.__REG_0)
        self._surface.set(4, 8, self.__REG_1 if self.__system.cpu.flags.isset(_emu.CPUFlags.BREAK) else self.__REG_0)
        self._surface.set(4, 9, self.__REG_1 if self.__system.cpu.flags.isset(_emu.CPUFlags.DECIMAL) else self.__REG_0)
        self._surface.set(4, 10, self.__REG_1 if self.__system.cpu.flags.isset(_emu.CPUFlags.INTDIS) else self.__REG_0)
        self._surface.set(4, 11, self.__REG_1 if self.__system.cpu.flags.isset(_emu.CPUFlags.ZERO) else self.__REG_0)
        self._surface.set(4, 12, self.__REG_1 if self.__system.cpu.flags.isset(_emu.CPUFlags.CARRY) else self.__REG_0)
        # Program counter
        self.__print(4, 0, f"${self.__system.memory.pos:04X}")
        self.__print(4, 1, f"${self.__system.cpu.a:02X}")
        self.__print(4, 2, f"${self.__system.cpu.x:02X}")
        self.__print(4, 3, f"${self.__system.cpu.y:02X}")

    #endregion