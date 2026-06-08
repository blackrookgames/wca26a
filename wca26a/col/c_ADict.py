__all__ = ['ADict']

from collections.abc import\
    Iterable as _Iterable
from typing import\
    Callable as _Callable,\
    Generic as _Generic,\
    TypeVar as _TypeVar

TKey = _TypeVar('TKey')
TItem = _TypeVar('TItem')

class ADict(_Generic[TKey, TItem]):
    """"""

    #region init

    def __init__(self, items:_Iterable[TItem], keyextractor:_Callable[[TItem], TKey]):
        """
        Initializer for ADict

        :param items: Items
        :param keyextractor: Function for extracting key value for each item
        :raise KeyError: One or more items contain the same key
        """
        self.__items:dict[TKey, TItem] = {}
        for _item in items:
            _key = keyextractor(_item)
            if _key in self.__items: raise KeyError("One or more items contain the same key.")
            self.__items[_key] = _item

    #endregion

    #region operators

    def __len__(self):
        return len(self.__items)

    def __getitem__(self, key:TKey):
        try:
            return self.__items[key]
        except:
            if key in self.__items: raise
        raise KeyError("No item exists with the specified key.")
    
    def __iter__(self):
        for _chunk in self.__items.values():
            yield _chunk

    def __contains__(self, key:TKey):
        return key in self.__items

    #endregion

    #region methods

    def keys(self):
        """
        Generates a list of dictionary keys

        :return: List of dictionary keys
        """
        return [_i for _i in self.__items.keys()]

    def iter_keys(self):
        """ Iterates thru the dictionary keys """
        for _i in self.__items.keys(): yield _i

    #endregion