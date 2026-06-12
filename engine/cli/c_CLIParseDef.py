__all__ = [\
    'CLIParseDef',]

from .c_CLIParseCall import\
    CLIParseCall as _CLIParseCall

class CLIParseDef:
    """
    Represents a definition for a handler for parsing input
    """

    #region init

    def __init__(self,\
            parse:None|_CLIParseCall,\
            arg:None|tuple):
        """
        Initializer for CLIParseDef
        
        :param parse:
            Function to use for parsing command-line input
        :param arg:
            Additional argument for parse call
        """
        self.__parse = parse
        self.__arg = arg

    #endregion

    #region properties

    @property
    def parse(self) -> None|_CLIParseCall:
        """
        Function to use for parsing command-line input
        """
        return self.__parse

    @property
    def arg(self) -> None|tuple:
        """
        Additional argument for parse call
        """
        return self.__arg

    #endregion