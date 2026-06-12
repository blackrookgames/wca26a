__all__ = [ 'ParseUtilResult' ]

from typing import\
    Generic as _Generic,\
    TypeVar as _TypeVar

from .c_ParseUtilStatus import\
    ParseUtilStatus as _ParseUtilStatus

T = _TypeVar("T")
class ParseUtilResult(_Generic[T]):
    """
    Represents the result of a parse operation
    """

    #region init

    def __init__(self,\
            status:_ParseUtilStatus,\
            value:None|T):
        """
        Initializer for ParseUtilResult

        :param status:
            Return status
        :param value:
            Parsed value
        """
        self.__status = status
        self.__value = value

    @classmethod
    def passs(cls,\
            value:T):
        """
        Create a result indicating input parsed successfully

        :param value:
            Parsed value
        :return:
            Created result
        """
        return cls(_ParseUtilStatus.PASS, value)

    @classmethod
    def fail(cls):
        """
        Create a result indicating input failed to parse

        :return:
            Created result
        """
        return cls(_ParseUtilStatus.FAIL, None)
    
    @classmethod
    def tolo(cls):
        """
        Create a result indicating the parse value is too low

        :return:
            Created result
        """
        return cls(_ParseUtilStatus.TOLO, None)
    
    @classmethod
    def tohi(cls):
        """
        Create a result indicating the parse value is too high

        :return:
            Created result
        """
        return cls(_ParseUtilStatus.TOHI, None)

    #endregion

    #region operators

    def __repr__(self):
        return f"ParseUtilResult[{T}]({self.__status}, {self.__value})"
    
    def __str__(self):
        return f"{self.__status} {self.__value}"

    #endregion

    #region properties

    @property
    def status(self) -> _ParseUtilStatus:
        """
        Return status
        """
        return self.__status

    @property
    def value(self) -> None|T:
        """
        Return value
        """
        return self.__value

    #endregion