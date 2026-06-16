__all__ = ['SurfacePaneBase']

import boacon as _boacon

from dataclasses import\
    dataclass as _dataclass

import assutil as _assutil
import emu as _emu

from .c_BufferedPane import\
    BufferedPane as _BufferedPane
from .c_SurfacePaneSurface import\
    SurfacePaneSurface as _SurfacePaneSurface

class SurfacePaneBase(_boacon.BCPane):
    """ BASE: Represents a pane with a "drawing" surface """

    #region const

    __SPACE = _boacon.BCChar(0x20)

    #endregion

    #region init

    def __init__(self):
        """ Initializer for SurfacePaneBase """
        super().__init__()
        self.__surface = _SurfacePaneSurface(self)

    #endregion

    #region protected properties

    @property
    def _surface(self):
        return self.__surface

    #endregion

    #region overridden methods
    
    def _draw(self, setchr:_boacon.BCSetChrFunc):
        super()._draw(setchr)
        in_x = -self.__surface.offset_x + self.x.clipoff
        in_y = -self.__surface.offset_y + self.y.clipoff
        iy = in_y
        oy = self.y.clip0
        while oy < self.y.clip1:
            # Loop thru columns
            ix = in_x
            ox = self.x.clip0
            while ox < self.x.clip1:
                # Get character 
                try: _chr = self.__surface.get(ix, iy)
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