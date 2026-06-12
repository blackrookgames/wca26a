__all__ = [\
    'CLIParseCall1',
    'CLIParseCall2',
    'CLIParseCall',]

from typing import\
    Any as _Any,\
    Callable as _Callable

type CLIParseCall1 = _Callable[[str], tuple[bool, _Any]]
"""
Represents a parse function that takes 1 argument
- input:
  - str: command-line input
- output:
  - bool: whether or not successful
  - _Any: parsed value
"""

type CLIParseCall2 = _Callable[[str, tuple], tuple[bool, _Any]]
"""
Represents a parse function that takes 2 arguments
- input:
  - str: command-line input
  - tuple: additional argument
- output:
  - bool: whether or not successful
  - _Any: parsed value
"""

type CLIParseCall = CLIParseCall1 | CLIParseCall2
"""
Represents a function that parses command-line input
"""
    