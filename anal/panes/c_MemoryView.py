__all__ = ['MemoryView']

import boacon as _boacon

from dataclasses import\
    dataclass as _dataclass

import emu as _emu

from .c_SurfacePaneBase import\
    SurfacePaneBase as _SurfacePaneBase

class MemoryView(_SurfacePaneBase):
    """ Represents a view of entire system memory """

    #region init

    def __init__(self, memory:_emu.Memory):
        """
        Initializer for MemoryView

        :param memory: Memory
        """
        super().__init__()
        self.__memory = memory
        self.__page = 0
        # Create table
        self._surface.resize(self.__OFF_X + 256 * self.__COL_SIZE, self.__OFF_Y + 256 * self.__ROW_SIZE)
        self.__print(0, 0, "All Memory")
        for _i in range(16):
            self.__print(self.__OFF_X + _i * self.__COL_SIZE, 1, f"_{_i:X}")
        for _i in range(16):
            self.__print(2, self.__OFF_Y + _i * self.__ROW_SIZE, f"{_i:X}_")

    #endregion

    #region const

    __COL_SIZE = 3
    __ROW_SIZE = 1

    __OFF_X = 5
    __OFF_Y = 2

    NUM_PAGES = 0x100
    """ Total number of pages """

    #endregion

    #region properties

    @property
    def page(self):
        """ Current page """
        return self.__page
    @page.setter
    def page(self, value:int):
        """
        Current page
        
        :raise ValueError: value is out of range
        """
        if self.__page == value:
            return
        if value < 0 or value >= self.NUM_PAGES:
            raise ValueError("value is out of range.")
        self.__page = value
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
        Refreshes the memory view.\n
        A manual refresh is neccessary as the memory view can't detect when the memory is updated.
        """
        # Update row headers
        _page_str = f"{self.__page:02X}"
        for _i in range(16):
            self.__print(0, self.__OFF_Y + _i * self.__ROW_SIZE, _page_str)
        # Update cells
        _hi = self.__page << 8
        for _i in range(0x00, 0x100):
            _x = self.__OFF_X + (_i % 16) * self.__COL_SIZE
            _y = self.__OFF_Y + (_i // 16) * self.__ROW_SIZE
            self.__print(_x, _y, f"{self.__memory[_hi | _i]:02X}")

    #endregion