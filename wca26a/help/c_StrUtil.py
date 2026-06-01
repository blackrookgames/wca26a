all = ['StrUtil']

class StrUtil:
    """
    Utility for string-related operations
    """
    
    @classmethod
    def ljusttrun(cls, s:str, length:int, fillchar:str = ' '):
        """
        Creates either a justified or truncated version of the input string depending on it's length:
        - If the length of the input string is less than the specified length, a justification is performed.
        - If the length of the input string is greater than the specified length, a truncation is performed.
        \n
        Examples:
        - ljustrun("Four", 2) -> "Fo"
        - ljustrun("Four", 6) -> "Four  "
        
        :param s:
            Input string
        :param length:
            Exact length of output string
        :param fillchar:
            Fille character
        :return:
            Created string
        :raise ValueError:
            length is less than zero
        """
        if length < 0: raise ValueError("length must be greater than or equal to zero.")
        return s.ljust(length) if (len(s) < length) else s[:length]
    
    @classmethod
    def rjusttrun(cls, s:str, length:int, fillchar:str = ' '):
        """
        Creates either a justified or truncated version of the input string depending on it's length:
        - If the length of the input string is less than the specified length, a justification is performed.
        - If the length of the input string is greater than the specified length, a truncation is performed.
        \n
        Examples:
        - ljustrun("Four", 2) -> "ur"
        - ljustrun("Four", 6) -> "  Four"
        
        :param s:
            Input string
        :param length:
            Exact length of output string
        :param fillchar:
            Fille character
        :return:
            Created string
        :raise ValueError:
            length is less than zero
        """
        if length < 0: raise ValueError("length must be greater than or equal to zero.")
        return s.rjust(length) if (len(s) < length) else s[(-length):]
        