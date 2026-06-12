__all__ = ['Ptr']

from typing import\
    cast as _cast,\
    Generic as _Generic,\
    TypeVar as _TypeVar

from .c_BadOpError import\
    BadOpError as _BadOpError

T = _TypeVar('T')

class Ptr(_Generic[T]):
    """ Represents a "pointer" to a value """

    #region init

    def __init__(self, value:None|T = None):
        """
        Initializer for Ptr

        :param value: Value to "point" to
        """
        self.__value = value
        self.__hasvalue = value is not None
        
    #endregion

    #region operators
    
    def __bool__(self):
        return self.__hasvalue
    
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
        if self.__hasvalue: return _cast(T, self.__value)
        raise _BadOpError("Pointer is not pointing to a value.")
    @value.setter
    def value(self, value:None|T):
        self.__value = value
        self.__hasvalue = value is not None
    
    def hasvalue(self):
        """ Whether or not "pointer" is "pointing" to a value """
        return self.__hasvalue
        
    #endregion

    #region helper methods

    def __eq(self, other):
        if not isinstance(other, Ptr): return False
        return self.value is other.value

    #endregion