import re

from sfdfont.error import SfdParseError
from sfdfont.record import SfdRecord
from sfdfont.revision import SfdSfntRevision


def decode_revision(item):
    if item.keyword != 'sfntRevision:':
        raise SfdParseError('unexpected sfnt revision record kind')
    data = item.value.strip()
    if not re.fullmatch(rb'#?[+-]?(?:0[xX])?[0-9a-fA-F]{1,8}', data):
        raise SfdParseError('invalid sfnt revision hexadecimal word')
    value = int(data.lstrip(b'#'), 16)
    if not -0x80000000 <= value <= 0xFFFFFFFF:
        raise SfdParseError('sfnt revision exceeds 32 bits')
    return SfdSfntRevision(value & 0xFFFFFFFF)


def encode_revision(value):
    from sfdfont._validation import number

    number(value.value, 'sfnt revision bits', 0, 0xFFFFFFFF)
    return SfdRecord('sfntRevision:', f'0x{value.value:08x}'.encode())
