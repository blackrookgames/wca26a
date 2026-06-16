__all__ = ['System']

from .c_CPU import\
    CPU as _CPU
from .c_Memory import\
    Memory as _Memory

class System:
    """ Represents a system with CPU and memory """

    #region init

    def __init__(self, nogarb:bool, stackwrap:bool):
        """
        Initializer for System

        :param nogarb: If true, initial garbage data will not be emulated
        :param stackwrap: If true, stack pointer will wrap upon overflow/underflow; otherwise an EmuError is raised
        """
        self.__cpu = _CPU(nogarb, stackwrap)
        self.__memory = _Memory(nogarb)

    #endregion

    #region properties

    @property
    def cpu(self): return self.__cpu

    @property
    def memory(self): return self.__memory

    #endregion
