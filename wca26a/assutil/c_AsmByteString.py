__all__ = ['AsmByteString']

from io import\
    StringIO as _StringIO

from .c_AsmItem import AsmItem as _AsmItem

class AsmByteString(_AsmItem):
    """ Represents a string of bytes """
    
    #region init

    def __init__(self, data:bytes):
        """
        Initializer for AsmByteString

        :param data: Byte data
        """
        self.__data = data

    #endregion

    #region methods

    def gen_str(self, addr:int):
        with _StringIO() as _s:
            _s.write("!BYTE ")
            if len(self.__data) > 0:
                _s.write(f"${self.__data[0]:02X}")
                for _i in range(1, len(self.__data)):
                    _s.write(f", ${self.__data[_i]:02X}")
            return _s.getvalue()

    def gen_bytes(self):
        return self.__data

    #endregion