import re

from sfdfont._layout import LayoutReader
from sfdfont._reader import Reader
from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.os2 import SfdOs2Mask, SfdOs2Vendor, SfdPanose
from sfdfont.record import SfdRecord

MASK_COUNTS = {'OS2CodePages:': 2, 'OS2UnicodeRanges:': 4}
OS2_KEYS = set(MASK_COUNTS) | {'Panose:', 'OS2Vendor:'}


def decode_panose(item):
    if item.keyword != 'Panose:':
        raise SfdParseError('unexpected PANOSE record kind')
    reader = Reader(item.value)
    stream = LayoutReader(reader)
    # Some FontForge builds print C char values as signed decimal bytes.
    result = SfdPanose([stream.integer(-128, 255) & 255 for _ in range(10)])
    if stream.peek():
        reader.fail('trailing PANOSE data')
    return result


def encode_panose(value):
    from sfdfont._validation import check, number

    check(len(value.values) == 10, 'PANOSE requires ten bytes')
    for entry in value.values:
        number(entry, 'PANOSE byte', 0, 255)
    return SfdRecord('Panose:', b' '.join(str(entry).encode() for entry in value.values))


def decode_os2_mask(item):
    if item.keyword not in MASK_COUNTS:
        raise SfdParseError('unexpected OS/2 mask record kind')
    data = item.value.strip()
    words = data.split(b'.') if b'.' in data else data.split()
    if len(words) != MASK_COUNTS[item.keyword]:
        raise SfdParseError('OS/2 mask word count mismatch')
    result = 0
    for index, data in enumerate(words):
        data = data.strip()
        if not re.fullmatch(rb'#?[+-]?(?:0[xX])?[0-9a-fA-F]{1,8}', data):
            raise SfdParseError('invalid OS/2 mask hexadecimal word')
        value = int(data.lstrip(b'#'), 16)
        if not -0x80000000 <= value <= 0xFFFFFFFF:
            raise SfdParseError('OS/2 mask word exceeds 32 bits')
        result |= (value & 0xFFFFFFFF) << (index * 32)
    return SfdOs2Mask(item.keyword, result)


def encode_os2_mask(value):
    from sfdfont._validation import check, number

    check(value.keyword in MASK_COUNTS, 'invalid OS/2 mask keyword')
    count = MASK_COUNTS[value.keyword]
    number(value.value, 'OS/2 mask', 0, (1 << (32 * count)) - 1)
    data = b'.'.join(f'{(value.value >> (index * 32)) & 0xFFFFFFFF:08x}'.encode() for index in range(count))
    return SfdRecord(value.keyword, data)


def decode_os2_vendor(item):
    if item.keyword != 'OS2Vendor:':
        raise SfdParseError('unexpected OS/2 vendor record kind')
    reader = Reader(item.value)
    result = read_vendor(reader)
    if LayoutReader(reader).peek():
        reader.fail('trailing OS/2 vendor data')
    return result


def read_vendor(reader):
    stream = LayoutReader(reader)
    stream.expect(b"'")
    value = b''.join(reader.char() for _ in range(4))
    if len(value) != 4 or reader.char() != b"'":
        reader.fail('OS/2 vendor must contain exactly four bytes')
    return SfdOs2Vendor(value)


def vendor_record(reader, key):
    start = reader.pos
    read_vendor(reader)
    end = reader.pos
    if reader.line():
        reader.fail('trailing OS/2 vendor data')
    return SfdRecord(key, reader.data[start:end].strip())


def encode_os2_vendor(value):
    if not isinstance(value.vendor, bytes) or len(value.vendor) != 4:
        raise SfdValidationError('OS/2 vendor must contain exactly four bytes')
    result = SfdRecord('OS2Vendor:', b"'" + value.vendor + b"'")
    try:
        if decode_os2_vendor(result) != value:
            raise SfdValidationError('OS/2 vendor bytes would change interpretation when written')
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
    return result


def decode_os2(item):
    if item.keyword == 'Panose:':
        return decode_panose(item)
    if item.keyword == 'OS2Vendor:':
        return decode_os2_vendor(item)
    return decode_os2_mask(item)
