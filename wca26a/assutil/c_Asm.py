__all__ = ['Asm']

from .c_AsmChunks import AsmChunks as _AsmChunks

class Asm:
    """ Represents an assembly source """

    # region init

    # edregion

    #region init

    def __init__(self):
        """ Initializer for Asm """
        self.__f_chunks:_AsmChunks = _AsmChunks(self)
        self.__f_addr_entry:int = 0
        self.__f_addr_break:int = 0

    #endregion

    #region properties

    @property
    def chunks(self):
        """ Chunks """
        return self.__f_chunks
    
    @property
    def addr_entry(self):
        """ Entry address """
        return self.__f_addr_entry
    @addr_entry.setter
    def addr_entry(self, value:int):
        self.__f_addr_entry = value
    
    @property
    def addr_break(self):
        """ Break address """
        return self.__f_addr_break
    @addr_break.setter
    def addr_break(self, value:int):
        self.__f_addr_break = value

    #endregion