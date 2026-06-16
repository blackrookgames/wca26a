__all__ = [\
    'InsHisViewEntry',\
    'InsHisViewEntryRegState',\
    'InsHisView']

import boacon as _boacon

from dataclasses import\
    dataclass as _dataclass

import assutil as _assutil
import emu as _emu

from .c_BufferedPane import\
    BufferedPane as _BufferedPane
from .c_BufferedPaneBuffer import\
    BufferedPaneBuffer as _BufferedPaneBuffer

@_dataclass(frozen = True)
class InsHisViewEntry:
    """ Represents an entry in the instruction history view """

    addr:int
    """ Address of instruction """

    ins:_assutil.AsmIns
    """ Instrstruction """

    before:'InsHisViewEntryRegState'
    """ State of CPU registers before the instruction was executed """

    after:'InsHisViewEntryRegState'
    """ State of CPU registers after the instruction was executed """

@_dataclass(frozen = True)
class InsHisViewEntryRegState:
    """ Represents a "snapshot" of the state of CPU registers """

    a:int
    """ Accumulator """
    
    x:int
    """ X Index Register """
    
    y:int
    """ Y Index Register """

    flags:_emu.CPUFlags
    """ Processor status flags """

class InsHisView(_BufferedPane):
    """ Represents a view of recent instruction history """

    #region const

    __SPACE = _boacon.BCChar(0x20)

    __HEAD_PC       = "PC     "
    __HEAD_INS      = "Instruction         "
    __HEAD_FLAGS    = "NV-BDIZC "
    __HEAD_A        = "A   "
    __HEAD_X        = "X   "
    __HEAD_Y        = "Y   "
    __HEAD_ARROW    = "   "
    __HEAD =\
        __HEAD_PC +\
        __HEAD_INS +\
        __HEAD_FLAGS +\
        __HEAD_A +\
        __HEAD_X +\
        __HEAD_Y +\
        __HEAD_ARROW +\
        __HEAD_FLAGS +\
        __HEAD_A +\
        __HEAD_X +\
        __HEAD_Y

    #endregion

    #region init

    def __init__(self, maxsize = 100):
        """
        Initializer for InsHisView

        :param maxsize: Maximum size of the entry buffer
        :raises ValueError: maxsize is less than zero
        """
        super().__init__()
        self.__entries = []
        self.set_maxsize(maxsize)
        self.__maxsize:int = maxsize

    #endregion

    #region fields
    
    __entries:list[InsHisViewEntry]
    __maxsize:int

    #endregion

    #region properties

    @property
    def maxsize(self):
        """ Maximum size of the entry buffer """
        return self.__maxsize

    #endregion

    #region helper methods

    def _clip_excess(self):
        while len(self.__entries) > self.__maxsize:
            self.__entries.pop(0)

    #endregion

    #region overridden methods
    
    def _buffer(self, buffer:_BufferedPaneBuffer):
        super()._buffer(buffer)
        pos = 0
        # Make sure we have enough room
        if buffer.height < 1: return
        # Print header
        for _c in self.__HEAD.ljust(buffer.width)[:buffer.width]:
            buffer[pos] = _boacon.BCChar(ord(_c))
            pos += 1
        # Print most recent entries
        _entries_rowcount = buffer.height - 1
        _entries_offset = max(0, len(self.__entries) - _entries_rowcount)
        for _i in range(_entries_offset, len(self.__entries)):
            _entry = self.__entries[_i]
            _row = \
                f"${_entry.addr:04X}".ljust(len(self.__HEAD_PC)) +\
                _entry.ins.gen_str(_entry.addr).ljust(len(self.__HEAD_INS)) +\
                f"{(_entry.before.flags.value & 0xFF):08b}".ljust(len(self.__HEAD_FLAGS)) +\
                f"${_entry.before.a:02X}".ljust(len(self.__HEAD_A)) +\
                f"${_entry.before.x:02X}".ljust(len(self.__HEAD_X)) +\
                f"${_entry.before.y:02X}".ljust(len(self.__HEAD_Y)) +\
                "->".ljust(len(self.__HEAD_ARROW)) +\
                f"{(_entry.after.flags.value & 0xFF):08b}".ljust(len(self.__HEAD_FLAGS)) +\
                f"${_entry.after.a:02X}".ljust(len(self.__HEAD_A)) +\
                f"${_entry.after.x:02X}".ljust(len(self.__HEAD_X)) +\
                f"${_entry.after.y:02X}".ljust(len(self.__HEAD_Y))
            for _c in _row.ljust(buffer.width)[:buffer.width]:
                buffer[pos] = _boacon.BCChar(ord(_c))
                pos += 1
        # Pad
        while pos < len(buffer):
            buffer[pos] = self.__SPACE
            pos += 1

    #endregion

    #region methods

    def log(self, entry:InsHisViewEntry):
        # Add entry
        self.__entries.append(entry)
        # Clip excess entries
        self._clip_excess()
        # Redraw
        self._redraw()

    def set_maxsize(self, maxsize:int):
        """
        Sets the maximum size of the entry buffer

        :param maxsize: Maximum size of the entry buffer
        :raises ValueError: maxsize is less than zero
        """
        if maxsize < 0: raise ValueError("maxsize must be greater than or equal to zero.")
        # Set max size
        self.__maxsize = maxsize
        # Clip excess entries
        self._clip_excess()

    #endregion