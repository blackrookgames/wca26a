__all__ = ['AsmChunks']

from typing import\
    TYPE_CHECKING as _TYPE_CHECKING

if _TYPE_CHECKING: from .c_Asm import Asm as _Asm
from .c_AsmChunk import AsmChunk as _AsmChunk

class AsmChunks:
    """ Represents the chunks within an assembly source """

    # region init

    # edregion

    #region init

    def __init__(self, src:'_Asm'):
        """ Initializer for AsmChunks """
        self.__src:'_Asm' = src
        self.__f_chunks:dict[int, _AsmChunk] = {}

    #endregion

    #region operators

    def __len__(self):
        return len(self.__f_chunks)

    def __getitem__(self, offset:int):
        try:
            return self.__f_chunks[offset]
        except:
            if offset in self.__f_chunks: raise
        raise self.__no_chunk_at_offset()
    
    def __iter__(self):
        for _chunk in self.__f_chunks.values():
            yield _chunk

    def __contains__(self, item:int|_AsmChunk):
        if isinstance(item, int):
            return item in self.__f_chunks
        return item.src and item.src.value is self.src
    
    #endregion

    #region properties

    @property
    def src(self):
        """ Assembly source """
        return self.__src
    
    #endregion

    #region helper methods

    @classmethod
    def __no_chunk_at_offset(cls):
        return KeyError(f"Assembly source does not contain a chunk that starts at the specified offset.")

    def __pop(self, offset:int):
        try:
            chunk = self.__f_chunks.pop(offset)
        except:
            if offset in self.__f_chunks: raise
            chunk = None
        if chunk is None:
            raise self.__no_chunk_at_offset()
        chunk._src_clr()
        return chunk
    
    #endregion

    #region methods

    def add(self, offset:int, chunk:_AsmChunk):
        """
        Adds the specified chunk to the assembly source

        :param offset: Offset address to give chunk
        :param chunk: Chunk to add
        :raises ValueError: Chunk is already part of another assembly source.
        :raises KeyError: Assembly source already contains a chunk the starts at the specified offset.
        """
        if chunk.src:
            raise ValueError("Chunk is already part of another assembly source.")
        if offset is self.__f_chunks:
            raise KeyError("Assembly source already contains a chunk the starts at the specified offset.")
        self.__f_chunks[offset] = chunk
        chunk._src_set(self.__src, offset)

    def remove(self, item:int|_AsmChunk):
        """
        Attempts to remove a chunk from the assembly source

        :param item: Either the chunk or the chunk offset
        :return: Whether or not successful
        """
        if isinstance(item, int):
            if not (item in self.__f_chunks): return False
            self.__pop(item)
        else:
            if not (item.__f_src and item.__f_src.value is self): return False
            self.__pop(item.offset)
        return True

    def pop(self, offset:int):
        """
        Removes the chunk that starts at the specified offset

        :param offset: Offset address of chunk
        :return: Removed chunk
        :raise KeyError: Assembly source does not contain a chunk that starts at the specified offset
        """
        return self.__pop(offset)
    
    def clear(self):
        """
        Removes all chunks in the assembly source
        """
        offsets = [_offset for _offset in self.__f_chunks]
        for _offset in offsets: self.__pop(_offset)

    #endregion
