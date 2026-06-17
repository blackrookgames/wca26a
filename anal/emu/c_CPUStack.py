__all__ = ['CPUStack']

import random as _random

from .c_ByteArray import\
    ByteArray as _ByteArray
from .c_EmuError import\
    EmuError as _EmuError

class CPUStack:
    """ Represents the CPU stack """
    
    #region init

    def __init__(self, nogarb:bool, allowwrap:bool):
        """
        Initializer for CPUStack

        :param nogarb: If true, initial garbage data will not be emulated
        :param allowwrap: If true, stack pointer will wrap upon overflow/underflow; otherwise an EmuError is raised
        """
        self.__nogarb = nogarb
        self.__allowwrap = allowwrap
        self.__bytes = _ByteArray(self.SIZE, nogarb)
        self.__reset_pos()

    #endregion

    #region operations

    def __len__(self):
        return len(self.__bytes)
    
    def __getitem__(self, index:int):
        try: return self.__bytes[index]
        except Exception as _e: e = _e
        self.__raise_if_oor(index)
        raise e
    
    def __setitem__(self, index:int, value:int):
        try:
            self.__bytes[index] = value
            return
        except Exception as _e: e = _e
        self.__raise_if_oor(index)
        raise e
    
    def __iter__(self):
        for _b in self.__bytes: yield _b
    
    #endregion

    #region const

    SIZE = 0x100
    """ Stack size; for the sake of simplicity, this is 256 bytes """
    
    #endregion

    #region fields

    __nogarb:bool
    __allowwrap:bool
    __bytes:_ByteArray
    __pos:int
    
    #endregion

    #region properties

    @property
    def pos(self):
        """ Position of stack pointer """
        return self.__pos
    @pos.setter
    def pos(self, value:int):
        """
        Position of stack pointer
        
        :raise IndexError: Position is out of range
        """
        if value < 0 or value > len(self.__bytes):
            raise IndexError("Position is out of range.")
        self.__pos = value

    @property
    def allowwrap(self):
        """ If true, stack pointer will wrap upon overflow/underflow; otherwise an EmuError is raised """
        return self.__allowwrap

    #endregion

    #region helper methods

    def __raise_if_oor(self, index:int):
        if index >= 0 and index < len(self.__bytes): return
        raise IndexError("Index is out of range.")
    
    def __reset_pos(self):
        self.__pos = len(self.__bytes) if self.__nogarb else _random.randint(0, len(self.__bytes))
    
    #endregion

    #region methods

    def reset(self):
        """ Resets the stack """
        self.__bytes.reset()
        self.__reset_pos()

    def push(self, value:int):
        """
        Pushes a value onto the stack

        :raises _EmuError: Stack overflow occurs and allowwrap == False
        """
        # Fix if overflow
        if self.__pos == 0:
            if (not self.__allowwrap):
                raise _EmuError("Stack overflow")
            self.__pos = len(self.__bytes)
        # Decrement and set value
        self.__pos -= 1
        self.__bytes[self.__pos] = value & 0xFF
        
    def pull(self):
        """
        Pulls a value from the stack

        :raises _EmuError: Stack underflow occurs and allowwrap == False
        """
        # Fix if underflow
        if self.__pos == len(self.__bytes):
            if (not self.__allowwrap):
                raise _EmuError("Stack underflow")
            self.__pos = 0
        # Get value and increment
        value = self.__bytes[self.__pos]
        self.__pos += 1
        return value

    #endregion
