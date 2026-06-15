__all__ = ['CPUFlags']

from collections.abc import\
    Iterable as _Iterable
from enum import\
    Flag as _Flag
    
class CPUFlags(_Flag):
    """ Represents CPU flags """

    #region values

    NONE = 0
    """ No flag is set """

    NEGATIVE = 1 << 7
    """ Negative """

    OVERFLOW = 1 << 6
    """ Overflow """

    EXPANSION = 1 << 5
    """ Expansion; this is essentially unused """

    BREAK = 1 << 4
    """ Break Command """

    DECIMAL = 1 << 3
    """ Decimal """

    INTDIS = 1 << 2
    """ Interrupt Disable """

    ZERO = 1 << 1
    """ Zero """

    CARRY = 1 << 0
    """ Carry """

    #endregion

    #region methods

    def isset(self, flag:'CPUFlags'):
        """
        Checks whether or not the specified flag is set

        :param flag: Flag to check
        :return: Whether or not the specified flag is set
        """
        return (self.value & flag.value) != 0

    def set(self, flag:'CPUFlags', value:bool):
        """
        Sets or resets the specified flag

        :param flag: Flag to modify
        :param value: Flag state
        :return: Modified value
        """
        if value: return CPUFlags(self.value | flag.value)
        return CPUFlags(self.value & (0xFF ^ flag.value))
    
    def set_multi(self, flagconds:_Iterable[tuple['CPUFlags', bool]]) -> 'CPUFlags':
        """
        Modifies the states multiple flags

        :param flagconds: Pairs of flags/states
        :return: Modified value
        """
        flags = self
        for flag, value in flagconds:
            flags = flags.set(flag, value)
        return flags
    
    def modify(self,\
            set:'None|CPUFlags|_Iterable[CPUFlags]' = None,\
            reset:'None|CPUFlags|_Iterable[CPUFlags]' = None):
        """
        Creates a modified version of the current flag states

        :param set: Flags to set
        :param reset: Flags to reset
        :return: Modified value
        """
        value = self.value
        if set is not None:
            if isinstance(set, _Iterable):
                for _flag in set: value |= _flag.value
            else:
                value |= set.value
        if reset is not None:
            if isinstance(reset, _Iterable):
                for _flag in reset: value &= _flag.value
            else:
                value &= reset.value
        return CPUFlags(value)

    #endregion
