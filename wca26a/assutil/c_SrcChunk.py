__all__ = ['SrcChunk']

from pathlib import\
    Path as _Path

class SrcChunk:
    """ Represents a chunk of content from a source file """

    #region init

    def __init__(self, path:_Path, linenumber:int, content:str):
        """
        Initializer for SrcChunk

        :param path: Path of source file
        :param linenumber: Line number (1 is the first line)
        :param content: Chunk content
        """
        self.__path = path
        self.__linenumber = linenumber
        self.__content = content

    #endregion

    #region properties

    @property
    def path(self):
        """ Path of source file """
        return self.__path

    @property
    def linenumber(self):
        """ Line number (1 is the first line) """
        return self.__linenumber

    @property
    def content(self):
        """ Chunk content """
        return self.__content

    #endregion
