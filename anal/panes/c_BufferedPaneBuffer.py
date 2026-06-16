__all__ = ['BufferedPaneBuffer']

import boacon as _boacon
import numpy as _np
import numpy.dtypes as _npd
import numpy.typing as _npt

from typing import\
    TYPE_CHECKING as _TYPE_CHECKING

if _TYPE_CHECKING:
    from .c_BufferedPane import\
        BufferedPane as _BufferedPane

class BufferedPaneBuffer:
    """ Represents a character buffer """

    #region init

    def __init__(self, pane:'_BufferedPane'):
        """ Initializer for BufferedPaneBuffer """
        super().__init__()
        self.__pane = pane
        self.__width = 0
        self.__height = 0
        self.__data = _np.zeros(0, _np.uint32)

    #endregion

    #region operators

    def __len__(self):
        return len(self.__data)
    
    def __getitem__(self, index:int):
        try:
            return self.__from_int(self.__data[index])
        except:
            if index >= 0 and index < len(self.__data): raise
        raise IndexError("Index is out of range.")
    
    def __setitem__(self, index:int, value:_boacon.BCChar):
        try:
            self.__data[index] = self.__to_int(value)
            return
        except:
            if index >= 0 and index < len(self.__data): raise
        raise IndexError("Index is out of range.")
    
    def __iter__(self):
        for _item in self.__data:
            yield self.__from_int(_item)

    #endregion

    #region fields

    __pane:'_BufferedPane'

    __data:_npt.NDArray[_np.uint32]
    __width:int
    __height:int

    #endregion

    #region properties

    @property
    def pane(self):
        """ Pane """
        return self.__pane

    @property
    def width(self):
        """ Buffer width """
        return self.__width
    
    @property
    def height(self):
        """ Buffer height """
        return self.__height

    #endregion

    #region helper methods

    def _update_size(self):
        """ Also accessed by BufferedPaneBuffer """
        self.__width = max(0, self.__pane.x.pntlen)
        self.__height = max(0, self.__pane.y.pntlen)
        self.__data = _np.full(self.__width * self.__height, 0x20, _np.uint32)

    @classmethod
    def __to_int(cls, value:_boacon.BCChar):
        return (value.ord & 0xFFFFFF) | ((value.attr & 0xFF) << 24)

    @classmethod
    def __from_int(cls, value:int):
        return _boacon.BCChar(value & 0xFFFFFF, (value >> 24) & 0xFF)

    def __get_index(self, x:int, y:int):
        if x < 0 or x >= self.__width:
            raise IndexError("X-coordinate is out of range.")
        if y < 0 or y >= self.__height:
            raise IndexError("Y-coordinate is out of range.")
        return x + y * self.__width

    #endregion

    #region methods

    def get(self, x:int, y:int):
        """
        Gets the character at the specified coordinates

        :param x: X-coordinate
        :param y: Y-coordinate
        :return: Character value
        :raises IndexError:
            X-coordinate is out of range\n
            or\n
            Y-coordinate is out of range
        """
        return self.__from_int(self.__data[self.__get_index(x, y)])

    def set(self, x:int, y:int, value:_boacon.BCChar):
        """
        Sets the character at the specified coordinates

        :param x: X-coordinate
        :param y: Y-coordinate
        :param value: Character value
        :raises IndexError:
            X-coordinate is out of range\n
            or\n
            Y-coordinate is out of range
        """
        self.__data[self.__get_index(x, y)] = self.__to_int(value)

    #endregion