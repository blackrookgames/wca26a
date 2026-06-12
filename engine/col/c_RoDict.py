__all__ = ['RoDict']

from typing import\
    Generic as _Generic,\
    TypeVar as _TypeVar

TKey = _TypeVar('TKey')
TValue = _TypeVar('TValue')

class RoDict(_Generic[TKey, TValue]):
    """ Represents read-only access to a dictionary """

    #region init

    def __init__(self, src:dict[TKey, TValue]):
        """
        Initializer for RoDict

        :param src: Source dictionary
        """
        self.__src = src

    #endregion

    #region operators

    def __len__(self):
        return len(self.__src)

    def __getitem__(self, key:TKey):
        try:
            return self.__src[key]
        except:
            if key in self.__src: raise
        raise KeyError("No item exists with the specified key.")
    
    def __iter__(self):
        for _chunk in self.__src:
            yield _chunk

    def __contains__(self, key:TKey):
        return key in self.__src

    #endregion

    #region methods

    def keys(self):
        """
        Generates a list of dictionary keys

        :return: List of dictionary keys
        """
        return [_i for _i in self.__src.keys()]

    def values(self):
        """
        Generates a list of dictionary values

        :return: List of dictionary values
        """
        return [_i for _i in self.__src.values()]

    def items(self):
        """
        Generates a list of dictionary items

        :return: List of dictionary items
        """
        return [_i for _i in self.__src.items()]

    def iter_keys(self):
        """ Iterates thru the dictionary keys """
        for _i in self.__src.keys(): yield _i

    def iter_values(self):
        """ Iterates thru the dictionary values """
        for _i in self.__src.values(): yield _i

    def iter_items(self):
        """ Iterates thru the dictionary items """
        for _i in self.__src.items(): yield _i

    #endregion