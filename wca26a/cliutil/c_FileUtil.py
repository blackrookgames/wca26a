__all__ = ['FileUtil']

from pathlib import\
    Path as _Path

from .c_CommandError import \
    CommandError as _CLICommandError

class FileUtil:
    """ Utility for file-related operations """

    #region open_r, open_w, open_rb, open_wb

    @classmethod
    def open_r(cls, path:str|_Path, *args):
        """
        Opens a file for text reading
        
        :param path: File path
        :return: Created file stream
        :raise CLICommandError: An error occurred
        """
        try:
            return open(path, 'r', *args)
        except Exception as _e:
            e = _CLICommandError(_e)
        raise e

    @classmethod
    def open_rb(cls, path:str|_Path, *args):
        """
        Opens a file for binary reading
        
        :param path: File path
        :return: Created file stream
        :raise CLICommandError: An error occurred
        """
        try:
            return open(path, 'rb', *args)
        except Exception as _e:
            e = _CLICommandError(_e)
        raise e

    @classmethod
    def open_w(cls, path:str|_Path, *args):
        """
        Opens a file for text writing
        
        :param path: File path
        :return: Created file stream
        :raise CLICommandError: An error occurred
        """
        try:
            return open(path, 'w', *args)
        except Exception as _e:
            e = _CLICommandError(_e)
        raise e

    @classmethod
    def open_wb(cls, path:str|_Path, *args):
        """
        Opens a file for binary writing
        
        :param path: File path
        :return: Created file stream
        :raise CLICommandError: An error occurred
        """
        try:
            return open(path, 'wb', *args)
        except Exception as _e:
            e = _CLICommandError(_e)
        raise e

    #endregion

    #region read_all_bytes, write_all_bytes

    @classmethod
    def read_all_bytes(cls, path:str|_Path):
        """
        Reads all byte data in a file

        :param path: File path
        :return: Byte data in file
        :raise CLICommandError: An error occurred
        """
        with cls.open_rb(path) as f: return f.read()
    
    @classmethod
    def write_all_bytes(cls, path:str|_Path, data:bytes):
        """
        Writes bytes data to a file

        :param path: File path
        :param data: Byte data
        :raise CLICommandError: An error occurred
        """
        with cls.open_wb(path) as f: f.write(data)
        
    #endregion