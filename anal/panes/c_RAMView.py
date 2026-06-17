__all__ = ['RAMView']

import boacon as _boacon

from dataclasses import\
    dataclass as _dataclass

import emu as _emu

from .c_SurfacePaneBase import\
    SurfacePaneBase as _SurfacePaneBase

class RAMView(_SurfacePaneBase):
    """ Represents a view of system RAM """

    #region const

    __COL_SIZE = 3
    __ROW_SIZE = 1

    __COL_COUNT = 17
    __ROW_COUNT = 10

    __OFF_COL = 1
    __OFF_ROW = 2

    #endregion

    #region init

    def __init__(self, memory:_emu.Memory):
        """
        Initializer for RAMView

        :param memory: Memory
        """
        super().__init__()
        self.__memory = memory
        # Create table
        self._surface.resize(self.__COL_COUNT * self.__COL_SIZE, self.__ROW_COUNT * self.__ROW_SIZE)
        self.__print(0, 0, "RAM")
        for _i in range(16):
            self.__print((self.__OFF_COL + _i) * self.__COL_SIZE, self.__OFF_ROW - 1, f"_{_i:X}")
        for _i in range(8):
            self.__print(0, (self.__OFF_ROW + _i) * self.__ROW_SIZE, f"{(_i + 8):X}_")

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
        Refreshes the RAM view.\n
        A manual refresh is neccessary as the RAM view can't detect when the RAM is updated.
        """
        BEG = 0x80
        END = 0x100
        for _i in range(END - BEG):
            _x = (self.__OFF_COL + _i % 16) * self.__COL_SIZE
            _y = (self.__OFF_ROW + _i // 16) * self.__ROW_SIZE
            self.__print(_x, _y, f"{self.__memory[BEG + _i]:02X}")

    #endregion