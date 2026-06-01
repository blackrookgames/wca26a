__all__ = ['FileUtil']

from io import\
    StringIO as _StringIO
from pathlib import\
    Path as _Path

import cliutil as _cliutil

from .c_SrcChunk import SrcChunk as _SrcChunk

class FileUtil:
    """ Utility for file-related operations """

    #region read_all_lines, write_all_lines

    @classmethod
    def read_all_lines(cls, path:str|_Path):
        """
        Reads all lines in a file

        :param path: File path
        :return: Read lines
        :raise CLICommandError: An error occurred
        """
        data = _cliutil.FileUtil.read_all_bytes(path)
        # Determine line ending sequence
        line_end = 0x0A
        line_end_both = False
        for _i in range(len(data)):
            _c = data[_i]
            # Line feed?
            if _c == 0x0A: break
            # Carriage return?
            if _c == 0x0D:
                line_end = _c
                line_end_both = (_i + 1) < len(data) and data[_i + 1] == 0x0A
                break
        # Extract lines
        lines:list[_SrcChunk] = []
        _start = 0
        _line_pos = 0
        _line_number = 1
        def _nextline():
            nonlocal path
            nonlocal data, lines
            nonlocal _start, _line_pos, _line_number
            with _StringIO() as __str:
                for __i in range(_start, _line_pos):
                    __str.write(chr(data[__i]))
                lines.append(_SrcChunk(_Path(path), _line_number, __str.getvalue()))
                _line_number += 1
        while _line_pos < len(data):
            _c = data[_line_pos]
            # New line?
            if _c == line_end:
                if line_end_both:
                    if (_line_pos + 1) < len(data) and data[_line_pos + 1] == 0x0A:
                        _nextline()
                        _start = _line_pos + 2
                        _line_pos += 1
                else:
                    _nextline()
                    _start = _line_pos + 1
            # Next
            _line_pos += 1
        _nextline()
        # Success!!!
        return lines
    
    @classmethod
    def write_all_lines(cls, path:str|_Path, lines:list[_SrcChunk]):
        """
        Writes a list of lines to a file

        :param path: File path
        :param lines: Lines of text (line number is ignored)
        :raise CLICommandError: An error occurred
        """
        data = bytearray()
        for _line in lines:
            for _char in _line.content: data.append(ord(_char))
            data.append(0x0A)
        _cliutil.FileUtil.write_all_bytes(path, data)
        
    #endregion