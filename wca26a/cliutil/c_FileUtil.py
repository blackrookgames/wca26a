__all__ = ['FileUtil']

from pathlib import\
    Path as _Path

from .c_CommandError import \
    CommandError as _CLICommandError

class FileUtil:
    """ Utility for file-related operations """

    #region read_all_bytes, write_all_bytes

    @classmethod
    def read_all_bytes(cls, path:str|_Path):
        """
        Reads all byte data in a file

        :param path: File path
        :return: Byte data in file
        :raise CLICommandError: An error occurred
        """
        try:
            with open(path, 'rb') as f:
                return f.read()
        except Exception as _e:
            e = _CLICommandError(_e)
        raise e
    
    @classmethod
    def write_all_bytes(cls, path:str|_Path, data:bytes):
        """
        Writes bytes data to a file

        :param path: File path
        :param data: Byte data
        :raise CLICommandError: An error occurred
        """
        try:
            with open(path, 'wb') as f:
                f.write(data)
            return
        except Exception as _e:
            e = _CLICommandError(_e)
        raise e
        
    #endregion