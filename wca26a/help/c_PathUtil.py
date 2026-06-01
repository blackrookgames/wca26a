__all__ = ['PathUtil']

from pathlib import\
    Path as _Path

class PathUtil:
    """ Utility for path-related operations """

    @classmethod
    def relative(cls, path:_Path, base:_Path):
        """
        If path is relative to base, a relative path is returned.\n
        Otherwise an absolute path is returned.

        :param path: Path to check
        :param base: Base path
        """
        try: return path.relative_to(base.resolve())
        except: pass
        return path.resolve()

    @classmethod
    def absolute(cls, path:_Path, base:_Path):
        """
        Returns an absolute version of the path. If the given path is relative, 
        it is combined with the base path.

        :param path: Path to check
        :param base: Base path
        """
        if path.is_absolute(): return path.resolve()
        return base.resolve().joinpath(path)