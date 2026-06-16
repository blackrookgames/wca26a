__all__ = ['BufferedPane']

import boacon as _boacon

from .c_BufferedPaneBuffer import\
    BufferedPaneBuffer as _BufferedPaneBuffer

class BufferedPane(_boacon.BCPane):
    """ Represents pane with a character buffer """

    #region const

    __SPACE = _boacon.BCChar(0x20)

    #endregion

    #region init

    def __init__(self):
        """ Initializer for BufferedPane """
        super().__init__()
        self.__buffer = _BufferedPaneBuffer(self)

    #endregion

    #region overridden methods

    def _resolved(self):
        super()._resolved()
        if self.__buffer.width == self.x.pntlen and self.__buffer.height == self.y.pntlen:
            return
        self.__buffer._update_size()
        self._buffer(self.__buffer)
    
    def _draw(self, setchr:_boacon.BCSetChrFunc):
        super()._draw(setchr)
        # Copy to screen
        iy = self.y.clipoff
        oy = self.y.clip0
        while oy < self.y.clip1:
            # Loop thru columns
            ix = self.x.clipoff
            ox = self.x.clip0
            while ox < self.x.clip1:
                # Get character 
                try: _chr = self.__buffer.get(ix, iy)
                except: _chr = self.__SPACE # Assume coordinates were out of range (just in case)
                # Place on screen
                setchr(ox, oy, _chr)
                # Next column
                ix += 1
                ox += 1
            # Next row
            iy += 1
            oy += 1

    #endregion

    #region virtual methods

    def _buffer(self, buffer:_BufferedPaneBuffer):
        """ Called when the character buffer needs to be redrawn """
        pass

    #endregion

    #region protected methods

    def _redraw(self):
        """ Forces a redraw of the character buffer """
        self._buffer(self.__buffer)
        self.set_dirty()

    #endregion

    #region methods

    #endregion