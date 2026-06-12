__all__ = [ 'RoList' ]

from typing import\
    Generic as _Generic,\
    TypeVar as _TypeVar

import help as _help

T = _TypeVar("T")
class RoList(_Generic[T]):
    """ Represents read-only access to a list """

    #region init

    def __init__(self, src:list[T]):
        """
        Initializer for RoList

        :param src: Source list
        """
        self.__src = src

    #endregion

    #region operators

    def __len__(self):
        return len(self.__src)

    def __getitem__(self, index):
        # Cast as integer
        _index = _help.ErrorUtil.valid_int(index, param = 'index')
        if _index < 0 or _index >= len(self.__src):
            raise IndexError(f"index is out of range")
        # Return
        return self.__src[_index]

    def __contains__(self, item):
        return item in self.__src

    def __iter__(self):
        i = 0
        l = len(self.__src)
        while i < l:
            yield self.__src[i]
            i += 1

    #endregion