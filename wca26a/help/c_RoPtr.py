__all__ = ['RoPtr']

from typing import\
    Generic as _Generic,\
    TypeVar as _TypeVar

from .c_Ptr import Ptr as _Ptr

T = _TypeVar('T')

class RoPtr(_Generic[T]):
    """ Represents a read-only "pointer" to a value """

    #region init

    def __init__(self, src:_Ptr[T]):
        """
        Initializer for RoPtr

        :param src: Source
        """
        self.__src = src
        
    #endregion

    #region operators
    
    def __bool__(self): return self.__src.hasvalue()
    
    def __eq__(self, other): return self.__eq(other)
    def __ne__(self, other): return not self.__eq(other)
        
    #endregion

    #region properties

    @property
    def value(self):
        """
        Value being to "pointed" to

        :raise _BadOpError: Pointer is not pointing to a value
        """
        return self.__src.value
    
    def hasvalue(self):
        """ Whether or not "pointer" is "pointing" to a value """
        return self.__src.hasvalue
        
    #endregion

    #region helper methods

    def __eq(self, other):
        if isinstance(other, RoPtr): return self.__src == other.__src
        if isinstance(other, _Ptr): return self.__src == other
        return False
    
    #endregion