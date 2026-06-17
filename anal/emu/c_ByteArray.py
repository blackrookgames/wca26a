__all__ = ['ByteArray']
    
import numpy as _np
import numpy.typing as _npt
import random as _random

class ByteArray:
    """ Represents an array of bytes """

    #region init

    def __init__(self, len:int, nogarb:bool):
        """
        Initializer for ByteArray

        :param len: Array length
        :param nogarb: If true, initial garbage data will not be emulated
        :raise ValueError: len is less than zero
        """
        if len < 0: raise ValueError("len must be greater than or equal to zero.")
        self.__nogarb = nogarb
        self.__len = len
        self.reset()

    #endregion

    #region operations

    def __len__(self):
        return self.__len
    
    def __getitem__(self, index:int):
        try: return int(self.__content[index])
        except Exception as _e: e = _e
        self.__raise_if_oor(index)
        raise e
    
    def __setitem__(self, index:int, value:int):
        try:
            self.__content[index] = value & 0xFF
            return
        except Exception as _e: e = _e
        self.__raise_if_oor(index)
        raise e
    
    def __iter__(self):
        for _b in self.__content: yield _b
    
    #endregion

    #region fields

    __nogarb:bool
    __len:int
    __content:_npt.NDArray[_np.uint8]
    
    #endregion

    #region helper methods

    def __raise_if_oor(self, index:int):
        if index >= 0 and index < len(self.__content): return
        raise IndexError("Index is out of range.")
    
    #endregion

    #region methods

    def reset(self):
        """ Resets the array """
        if self.__nogarb:
            self.__content = _np.zeros(self.__len, _np.uint8)
        else:
            self.__content = _np.fromiter(_random.randbytes(self.__len), _np.uint8)

    #endregion

#endregion
