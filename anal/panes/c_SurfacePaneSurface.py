__all__ = ['SurfacePaneSurface']

import boacon as _boacon
import numpy as _np
import numpy.typing as _npt

from typing import\
    TYPE_CHECKING as _TYPE_CHECKING

if _TYPE_CHECKING:
    from .c_SurfacePaneBase import\
        SurfacePaneBase as _SurfacePaneBase

class SurfacePaneSurface:
    """ Represents a "drawing" surface """

    #region init

    def __init__(self, pane:'_SurfacePaneBase'):
        """ Initializer for SurfacePaneSurface """
        super().__init__()
        self.__pane = pane
        self.__offset_x = 0
        self.__offset_y = 0
        self.__width = 0
        self.__height = 0
        self.__data = _np.zeros(0, _np.uint32)

    #endregion

    #region operators

    def __len__(self):
        return len(self.__data)
    
    def __getitem__(self, index:int):
        return self.__getitem(index)
    
    def __setitem__(self, index:int, value:_boacon.BCChar):
        return self.__setitem(index, value)
    
    def __iter__(self):
        for _item in self.__data:
            yield self.__from_int(_item)

    #endregion

    #region fields

    __pane:'_SurfacePaneBase'

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
    def offset_x(self):
        """ X-offset """
        return self.__offset_x
    @offset_x.setter
    def offset_x(self, value:int):
        if self.__offset_x == value: return
        self.__offset_x = value
        self.__pane.set_dirty()

    @property
    def offset_y(self):
        """ Y-offset """
        return self.__offset_y
    @offset_y.setter
    def offset_y(self, value:int):
        if self.__offset_y == value: return
        self.__offset_y = value
        self.__pane.set_dirty()

    @property
    def width(self):
        """ Surface width """
        return self.__width
    
    @property
    def height(self):
        """ Surface height """
        return self.__height

    #endregion

    #region helper methods

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
    
    def __getitem(self, index:int):
        try:
            return self.__from_int(self.__data[index])
        except:
            if index >= 0 and index < len(self.__data): raise
        raise IndexError("Index is out of range.")
    
    def __setitem(self, index:int, value:_boacon.BCChar):
        try:
            prev = self.__data[index]
            curr = self.__to_int(value)
            # Make sure value changes
            if prev == curr: return
            # Change value
            self.__data[index] = curr
            # Mark dirty
            self.__pane.set_dirty()
            # Success!!!
            return
        except:
            if index >= 0 and index < len(self.__data): raise
        raise IndexError("Index is out of range.")

    #endregion

    #region methods

    def resize(self, width:int, height:int, anchor_x:int = -1, anchor_y:int = -1):
        """
        Resizes the surface

        :param width: Surface width
        :param height: Surface height
        :param anchor_x: X-anchor (-1 = left; 0 = center; 1 = right)
        :param anchor_y: Y-anchor (-1 = top; 0 = middle; 1 = bottom)
        :raises ValueError:
            width is less than zero\n
            or\n
            height is less than zero
        """
        if width < 0: raise ValueError("width must be greater than or equal to zero.")
        if height < 0: raise ValueError("height must be greater than or equal to zero.")
        # Note previous
        prev_width = self.__width
        prev_height = self.__height
        prev_data = self.__data
        # Create new
        self.__width = width
        self.__height = height
        self.__data = _np.full(self.__width * self.__height, 0x20, _np.uint32)
        # Copy data
        copy_out_x0 = 0 if (anchor_x < 0) else ((self.__width - prev_width) // (1 if (anchor_x > 0) else 2))
        copy_out_y0 = 0 if (anchor_y < 0) else ((self.__height - prev_height) // (1 if (anchor_y > 0) else 2))
        copy_out_x1 = copy_out_x0 + prev_width
        copy_out_y1 = copy_out_y0 + prev_height
        copy_in_x0 = 0
        copy_in_y0 = 0
        copy_in_x1 = prev_width
        copy_in_y1 = prev_height
        if copy_out_x0 < 0:
            copy_in_x0 -= copy_out_x0
            copy_out_x0 = 0
        if copy_out_y0 < 0:
            copy_in_y0 -= copy_out_y0
            copy_out_y0 = 0
        if copy_out_x1 > self.__width:
            copy_in_x1 -= copy_out_x1 - self.__width
            copy_out_x1 = self.__width
        if copy_out_y1 > self.__height:
            copy_in_y1 -= copy_out_y1 - self.__height
            copy_out_y1 = self.__height
        copy_width = copy_in_x1 - copy_in_x0
        copy_height = copy_in_y1 - copy_in_y0
        for _y in range(copy_height):
            _in_y = copy_in_y0 + _y
            _out_y = copy_out_y0 + _y
            for _x in range(copy_width):
                _in_x = copy_in_x0 + _x
                _out_x = copy_out_x0 + _x
                self.__data[_out_x + _out_y * self.__width] = prev_data[_in_x + _in_y * prev_width]
        # Mark dirty
        self.__pane.set_dirty()

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
        return self.__getitem(self.__get_index(x, y))

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
        self.__setitem(self.__get_index(x, y), value)

    #endregion