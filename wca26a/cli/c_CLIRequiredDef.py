__all__ = [\
    'CLIRequiredDef',]

from typing import\
    Any as _Any,\
    Callable as _Callable

from .c_CLIParamDef import\
    CLIParamDef as _CLIParamDef
from .c_CLIParseCall import\
    CLIParseCall as _CLIParseCall
from .c_CLIParseDef import\
    CLIParseDef as _CLIParseDef

class CLIRequiredDef(_CLIParamDef, _CLIParseDef):
    """
    Represents a definition for a command-line required parameter
    """

    #region init

    def __init__(self,\
            name:None|str = None,\
            desc:None|str = None,\
            parse:None|_CLIParseCall = None,\
            arg:None|tuple = None):
        """
        Initializer for CLIRequiredDef
        
        :param name:
            Explicit name
        :param desc:
            Description
        :param parse:
            Function to use for parsing command-line input
        :param arg:
            Additional argument for parse call
        """
        _CLIParamDef.__init__(self, name, desc)
        _CLIParseDef.__init__(self, parse, arg)

    #endregion