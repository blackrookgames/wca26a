__all__ = ['IOUtil']

import io as _io

from os import\
    SEEK_END as _SEEK_END

class IOUtil:
    """ Utility for I/O related operations """

    #region get_size

    @classmethod
    def get_size(cls, f:_io.IOBase):
        """
        Gets the size of the I/O object

        :param f: I/O object
        :return: Size of the I/O object
        """
        current = f.tell() # Get current position
        f.seek(0, _SEEK_END) # Move to end
        size = f.tell() # Get end position
        f.seek(current) # Return to previous position
        return size

    #endregion