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

    #region operators

    def __repr__(self):
        return f"{SrcChunk.__name__}({self.__path}, {self.__linenumber}, {self.__content})"
    
    def __str__(self):
        return f"{self.__path} {self.__linenumber} {self.__content}"

    #endregion

    #region methods

    def sub(self, beg:None|int = None, end:None|int = None):
        """
        Creates a subchunk

        :param beg: Beginning index
        :param end: Ending index
        :return: Created subchunk
        :raises IndexError:
            beg is less than 0\n
            or\n
            end is greater than len(content)\n
            or\n
            beg is greater than end
        """
        if beg is None: beg = 0
        elif beg < 0: raise IndexError("beg must be greater than or equal to 0.")
        if end is None: end = len(self.__content)
        elif end > len(self.__content): raise IndexError("end less than or equal to len(content).")
        if beg > end: raise IndexError("beg must be less than or equal to end.")
        return SrcChunk(self.path, self.linenumber, self.content[beg:end])

    #endregion
