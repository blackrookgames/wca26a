__all__ = ['ParseUtil']

from pathlib import\
    Path as _Path
from sys import \
    stderr as _stderr

class ParseUtil:
    """ Utility for parsing input """
    
    @classmethod
    def to_path(cls, input:str):
        """
        Attempts to parse input as a path
        
        :param input: Input
        :return: Parse result
        """
        try: path = _Path(input)
        except:
            print(f"\"{input}\" is not a valid path.", file = _stderr)
            return False, None
        return True, path
    
    @classmethod
    def to_set(cls, input:str):
        """
        Attempts to parse input as a set of strings
        
        :param input: Input
        :return: Parse result
        """
        newset:set[str] = set()
        for _item in input.split(','):
            __item = _item.strip()
            if len(__item) == 0: continue
            if __item in newset: continue
            newset.add(__item)
        return True, newset
