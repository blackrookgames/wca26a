__all__ = ['StackView']

import boacon as _boacon

from dataclasses import\
    dataclass as _dataclass

import assutil as _assutil
import emu as _emu
import help as _help

from .c_BufferedPane import\
    BufferedPane as _BufferedPane
from .c_BufferedPaneBuffer import\
    BufferedPaneBuffer as _BufferedPaneBuffer

class StackView(_BufferedPane):
    """ Represents a view of a CPU stack """

    #region const

    __SPACE = _boacon.BCChar(0x20)

    __HEAD = "STACK"
    
    #endregion

    #region init

    def __init__(self, stack:_emu.CPUStack):
        """
        Initializer for StackView

        :param stack: CPU Stack
        """
        super().__init__()
        self.__stack = stack

    #endregion

    #region properties

    @property
    def stack(self):
        """ CPU Stack """
        return self.__stack

    #endregion

    #region overridden methods
    
    def _buffer(self, buffer:_BufferedPaneBuffer):
        super()._buffer(buffer)
        pos = 0
        # Make sure there's room
        if buffer.height < 1: return
        # Compute view bounds
        view_height = buffer.height - 1
        if len(self.__stack) > view_height:
            view_min = self.__stack.pos - view_height // 2
            view_max = view_min + view_height
            if view_min < 0:
                view_min = 0
                view_max = view_height
            elif view_max > len(self.__stack):
                view_min = len(self.__stack) - view_height
                view_max = len(self.__stack)
        else:
            view_min = 0
            view_max = len(self.__stack)
        # Print header
        for _c in _help.StrUtil.cjusttrun(self.__HEAD, buffer.width):
            buffer[pos] = _boacon.BCChar(ord(_c))
            pos += 1
        # Print data
        for _i in range(view_min, view_max):
            _attr = _boacon.attr_create(emp = _i == self.__stack.pos)
            _s_index = f"${_i:02X}:"
            _s_value = f"${self.__stack[_i]:02X}"
            _l_index = len(_s_index)
            _l_value = buffer.width - _l_index
            if _l_value >= 0:
                _row = _s_index + _help.StrUtil.rjusttrun(_s_value, _l_value)
            else:
                _row = _s_index[:buffer.width]
            for _c in _row:
                buffer[pos] = _boacon.BCChar(ord(_c), _attr)
                pos += 1
        # Pad
        while pos < len(buffer):
            buffer[pos] = self.__SPACE
            pos += 1

    #endregion

    #region methods

    def refresh(self):
        """
        Refreshes the stack view.\n
        A manual refresh is neccessary as the stack view can't detect when the stack changes state.
        """
        self._redraw()

    #endregion