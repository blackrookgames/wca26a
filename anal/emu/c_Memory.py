__all__ = ['Memory']

import struct as _struct

from collections.abc import\
    Iterable as _Iterable

import assutil as _assutil

from .c_ByteArray import\
    ByteArray as _ByteArray
from .c_EmuError import\
    EmuError as _EmuError

class Memory:
    """ Represents system memory. """

    #region init

    def __init__(self, nogarb:bool):
        """
        Initializer for Memory

        :param nogarb: If true, initial garbage data will not be emulated
        """
        self.__content = _ByteArray(self.SIZE, nogarb)
        self.__ptr_mni:int = _assutil.ROM_BEG
        self.__ptr_entry:int = _assutil.ROM_BEG
        self.__ptr_break:int = _assutil.ROM_BEG
        # Update pointers (to ensure they match randomized content)
        self.__update()

    #endregion

    #region operations

    def __len__(self):
        return len(self.__content)
    
    def __getitem__(self, address:int):
        try: return int(self.__content[address])
        except Exception as _e: e = _e
        self.__raise_if_oor(address)
        raise e
    
    def __setitem__(self, address:int, value:int):
        try:
            self.__content[address] = value
            self.__update()
            return
        except Exception as _e: e = _e
        self.__raise_if_oor(address)
        raise e
    
    def __iter__(self):
        for _b in self.__content: yield _b
    
    #endregion

    #region const

    SIZE = 1 << 16
    """
    Memory size\n
    For the sake of simplicity, this is 64KB in size (since the memory addresses are 16-bit).\n
    However, the actual memory size of the Atari VCS is far, far smaller.
    """

    #endregion

    #region properties

    @property
    def pos(self):
        """ Program Counter position """
        return self.__pos
    
    @property
    def ptr_mni(self):
        """ MNI pointer """
        return self.__ptr_mni
    
    @property
    def ptr_entry(self):
        """ Entry pointer """
        return self.__ptr_entry
    
    @property
    def ptr_break(self):
        """ Break pointer """
        return self.__ptr_break

    #endregion

    #region helper methods

    def __raise_if_oor(self, address:int):
        if address >= 0 and address < len(self.__content): return
        raise IndexError("Address is out of range.")
    
    def __read(self, offset:int, size:int) -> bytes:
        end = offset + size
        if end > len(self.__content): raise _EmuError("Memory overflow")
        return bytes(self.__content[_i] for _i in range(offset, end))
    
    def __read_inc(self, size:int) -> bytes:
        data = self.__read(self.__pos, size)
        self.__pos += size
        return data
    
    def __update(self):
        # Update pointers
        self.__ptr_mni:int = _struct.unpack('<H', self.__read(_assutil.ADDR_NMI, 2))[0]
        self.__ptr_entry:int = _struct.unpack('<H', self.__read(_assutil.ADDR_ENTRY, 2))[0]
        self.__ptr_break:int = _struct.unpack('<H', self.__read(_assutil.ADDR_BREAK, 2))[0]
    
    #endregion

    #region methods

    def goto(self, address:int):
        self.__raise_if_oor(address)
        self.__pos = address
    
    def read(self, size:int):
        """
        Reads a specified number of bytes and increments the cursor by the same amount

        :param size: Number of bytes to read
        :return: Read bytes
        :raise EmuError: Memory overflow
        """
        return self.__read_inc(max(0, size))
    
    def read_8(self):
        """
        Reads an 8-bit value and increments the cursor by 1

        :return: 8-bit unsigned integer
        :raise EmuError: Memory overflow
        """
        return self.__read_inc(1)[0]
    
    def read_16(self) -> int:
        """
        Reads a 16-bit value and increments the cursor by 2

        :return: 16-bit unsigned integer
        :raise EmuError: Memory overflow
        """
        return _struct.unpack('<H', self.__read_inc(2))[0]
    
    def populate(self, offset:int, data:_Iterable[int]):
        """
        Populates with the specified data

        :param offset: Destination offset
        :param data: Source data
        :raise IndexError: offset is out of range
        :raise _EmuError: Memory overflow
        """
        # Check range
        if offset < 0 or offset >= len(self.__content):
            raise IndexError("Offset is out of range.")
        # Get data
        temp = [_item for _item in data]
        if (offset + len(temp)) > len(self.__content): 
            raise _EmuError("Memory overflow")
        # Populate
        _pos = offset + len(temp) - 1
        while len(temp) > 0:
            self.__content[_pos] = temp.pop()
            _pos -= 1
        # Update
        self.__update()

    #endregion

#endregion
