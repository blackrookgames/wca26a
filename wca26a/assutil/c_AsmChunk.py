__all__ = ['AsmChunk']

from typing import\
    TYPE_CHECKING as _TYPE_CHECKING

import help as _help

if _TYPE_CHECKING: from .c_Asm import Asm as _Asm
from .c_AsmItem import AsmItem as _AsmItem

class AsmChunk:
    """ Represents a chunk of assembly data """

    #region init

    def __init__(self):
        """ Initializer for AsmChunk """
        self.__f__src:_help.Ptr['_Asm'] = _help.Ptr['_Asm']()
        self.__f_src:_help.RoPtr['_Asm'] = _help.RoPtr['_Asm'](self.__f__src)
        self.__f_offset:int = -1
        self.__f_data:list[_AsmItem] = []

    #endregion

    #region properties

    @property
    def src(self):
        """ Assembly source """
        return self.__f_src
    
    @property
    def offset(self):
        """ Offset address (useless unless src.hasvalue == True) """
        return self.__f_offset
    
    @property
    def data(self):
        """ Assembly data; could be assembly instructions or chunks of raw byte data """
        return self.__f_data

    #endregion

    #region helper methods

    def _src_set(self, src:'_Asm', offset:int):
        """
        Assume:
        - self.__f__src.hasvalue == False

        Also accessed by AsmChunks
        """
        self.__f__src.value = src
        self.__f_offset = offset
    
    def _src_clr(self):
        """
        Assume:
        - self.__f__src.hasvalue == True

        Also accessed by AsmChunks
        """
        self.__f__src.value = None
        self.__f_offset = -1

    #endregion