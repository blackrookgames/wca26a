__all__ = ['CPU']

import random as _random

from .c_CPUFlags import\
    CPUFlags as _CPUFlags
from .c_CPUStack import\
    CPUStack as _CPUStack

class CPU:
    """ (Loosely) represents a MOS 6502 Microprocessor """

    #region init

    def __init__(self, nogarb:bool, allowwrap:bool):
        """
        Initializer for CPUStack

        :param nogarb: If true, initial garbage data will not be emulated
        :param allowwrap: If true, stack pointer will wrap upon overflow/underflow; otherwise an EmuError is raised
        """
        self.__nogarb = nogarb
        self.__stack = _CPUStack(nogarb, allowwrap)
        self.__reset_regs()
    
    #endregion

    #region fields

    __nogarb:bool
    __stack:_CPUStack
    __a:int
    __x:int
    __y:int
    __flags:_CPUFlags
    
    #endregion

    #region properties

    @property
    def a(self):
        """ Accumulator """
        return self.__a
    @a.setter
    def a(self, value:int):
        self.__a = 0xFF & value
    
    @property
    def x(self):
        """ X Index Register """
        return self.__x
    @x.setter
    def x(self, value:int):
        self.__x = 0xFF & value
        
    @property
    def y(self):
        """ Y Index Register """
        return self.__y
    @y.setter
    def y(self, value:int):
        self.__y = 0xFF & value
    
    @property
    def stack(self):
        """ Stack """
        return self.__stack
    
    @property
    def flags(self):
        """ Processor status flags """
        return self.__flags
    @flags.setter
    def flags(self, value:'_CPUFlags'):
        self.__flags = value

    #endregion

    #region helper methods

    def __reset_regs(self):
        self.__a = 0 if self.__nogarb else _random.randint(0x00, 0xFF) 
        self.__x = 0 if self.__nogarb else _random.randint(0x00, 0xFF) 
        self.__y = 0 if self.__nogarb else _random.randint(0x00, 0xFF)
        self.__flags = _CPUFlags.NONE if self.__nogarb else _CPUFlags(_random.randint(0x00, 0xFF))

    #endregion

    #region methods

    def reset(self):
        """ Resets the CPU """
        self.__stack.reset()
        self.__reset_regs()

    #endregion
