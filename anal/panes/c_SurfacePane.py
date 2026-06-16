__all__ = ['SurfacePane']

from .c_SurfacePaneBase import\
    SurfacePaneBase as _SurfacePaneBase

class SurfacePane(_SurfacePaneBase):
    """ Represents a pane with a "drawing" surface """

    #region init

    def __init__(self):
        """ Initializer for SurfacePane """
        super().__init__()

    #endregion

    #region properties

    @property
    def surface(self):
        """ Drawing surface """
        return self._surface

    #endregion