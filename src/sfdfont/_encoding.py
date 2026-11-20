import re

from sfdfont._layout import LayoutReader
from sfdfont._reader import Reader
from sfdfont.encoding import SfdEncodingRange, SfdEncodingRemap
from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.record import SfdRecord

REMAP_KEYS = {'RemapN:', 'Remap:'}


def remap_count(item, limits=None):
    reader = Reader(item.value, limits)
    count = LayoutReader(reader).count()
    if reader.word():
        reader.fail('trailing encoding remap count data')
    return count


def decode_encoding_range(item):
    from sfdfont._parser import integer

    if item.keyword != 'Remap:':
        raise SfdParseError('unexpected encoding remap record kind')
    parts = item.value.split()
    if len(parts) != 3:
        raise SfdParseError('encoding remap requires first, last and base')
    if any(not re.fullmatch(rb'#?[+-]?(?:0[xX])?[0-9a-fA-F]{1,8}', part) for part in parts[:2]):
        raise SfdParseError('invalid encoding remap hexadecimal range')
    values = [int(part.lstrip(b'#'), 16) for part in parts[:2]]
    if any(not -0x80000000 <= value <= 0xFFFFFFFF for value in values):
        raise SfdParseError('encoding remap endpoint exceeds 32 bits')
    first, last = (value & 0xFFFFFFFF for value in values)
    base = integer(parts[2])
    if first > last or base < 0 or base + last - first > 0x7FFFFFFF:
        raise SfdParseError('encoding remap range or destination out of bounds')
    return SfdEncodingRange(first, last, base)


def encode_encoding_range(value):
    from sfdfont._validation import number

    number(value.first, 'encoding remap first', 0, 0xFFFFFFFF)
    number(value.last, 'encoding remap last', value.first, 0xFFFFFFFF)
    number(value.base, 'encoding remap base', 0, 0x7FFFFFFF - value.last + value.first)
    return SfdRecord('Remap:', f'{value.first:x} {value.last:x} {value.base}'.encode())


def remap_record(reader, key):
    item = SfdRecord(key, reader.line())
    if key == 'RemapN:':
        remap_count(item, reader.limits)
    else:
        decode_encoding_range(item)
    return item


def decode_encoding_remap(records):
    count = None
    result = SfdEncodingRemap()
    for item in records:
        if item.keyword == 'RemapN:':
            if count is not None:
                raise SfdParseError('duplicate RemapN declaration')
            count = remap_count(item)
        elif item.keyword == 'Remap:':
            if count is None:
                raise SfdParseError('Remap requires a preceding RemapN declaration')
            result.ranges.append(decode_encoding_range(item))
    if count is None:
        raise SfdParseError('missing RemapN declaration')
    if count != len(result.ranges):
        raise SfdParseError('encoding remap count mismatch')
    return result


def encode_encoding_remap(value):
    from sfdfont._validation import number

    number(len(value.ranges), 'encoding remap count', 0)
    return [SfdRecord('RemapN:', str(len(value.ranges)).encode()), *(entry.to_record() for entry in value.ranges)]


def remap_identity(records):
    if not any(item.keyword in REMAP_KEYS for item in records):
        return None
    return decode_encoding_remap(records)


def validate_remap(records):
    try:
        remap_identity(records)
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
