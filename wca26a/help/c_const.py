__all__ = [\
    'U8_MIN',\
    'U8_MAX',\
    'U8_SIZE',\
    'I8_NEG',\
    'I8_MIN',\
    'I8_MAX',\
    'I8_SIZE',\
    'U16_MIN',\
    'U16_MAX',\
    'U16_SIZE',\
    'I16_NEG',\
    'I16_MIN',\
    'I16_MAX',\
    'I16_SIZE',\
    'U32_MIN',\
    'U32_MAX',\
    'U32_SIZE',\
    'I32_NEG',\
    'I32_MIN',\
    'I32_MAX',\
    'I32_SIZE',\
    'U64_MIN',\
    'U64_MAX',\
    'U64_SIZE',\
    'I64_NEG',\
    'I64_MIN',\
    'I64_MAX',\
    'I64_SIZE',]

U8_MIN = 0
U8_MAX = 0xFF
U8_SIZE = 1

I8_NEG = 0x80
I8_MIN = -I8_NEG
I8_MAX = I8_NEG - 1
I8_SIZE = 1

U16_MIN = 0
U16_MAX = 0xFFFF
U16_SIZE = 2

I16_NEG = 0x8000
I16_MIN = -I16_NEG
I16_MAX = I16_NEG - 1
I16_SIZE = 2

U32_MIN = 0
U32_MAX = 0xFFFFFFFF
U32_SIZE = 4

I32_NEG = 0x80000000
I32_MIN = -I32_NEG
I32_MAX = I32_NEG - 1
I32_SIZE = 4

U64_MIN = 0
U64_MAX = 0xFFFFFFFFFFFFFFFF
U64_SIZE = 8

I64_NEG = 0x8000000000000000
I64_MIN = -I64_NEG
I64_MAX = I64_NEG - 1
I64_SIZE = 8