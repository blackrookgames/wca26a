__all__ = [\
    'CLIParse',]

import inspect as _inspect

from typing import\
    Any as _Any

from .c_CLIParseDef import\
    CLIParseDef as _CLIParseDef

class CLIParse:
    """
    Represents a handler for parsing input
    """

    #region init

    def __init__(self,\
            parsedef:_CLIParseDef):
        """
        Initializer for CLIParse
        
        :param parsedef:
            Parse handler definition
        """
        self.__parse = parsedef.parse
        self.__arg = parsedef.arg

    #endregion

    #region methods

    def parse(self, input:str) -> tuple[bool, _Any]:
        """
        Attempts to parse some input
        
        :param input:
            Input to parse
        :return:
            tuple[bool, Any]\n
            bool: Whether or not the input was successfully parsed\n
            Any: Parsed value
        """
        if self.__parse is not None:
            _sig = _inspect.signature(self.__parse)
            _cnt = len(_sig.parameters.items())
            # (str)
            if _cnt == 1: return self.__parse(input)
            # (str, tuple)
            else: return self.__parse(input, tuple() if (self.__arg is None) else self.__arg)
        else:
            return True, input

    #endregion