from sfdfont._layout import LayoutReader
from sfdfont._reader import Reader
from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.gasp import SfdGaspRange, SfdGaspTable
from sfdfont.record import SfdRecord


def decode_gasp(item):
    if item.keyword != 'GaspTable:':
        raise SfdParseError('unexpected gasp record kind')
    reader = Reader(item.value)
    stream = LayoutReader(reader)
    count = stream.integer(maximum=32767)
    ranges = []
    previous = -1
    for _ in range(count):
        entry = SfdGaspRange(stream.integer(), stream.integer())
        if entry.ppem <= previous:
            reader.fail('gasp ppem limits must be strictly increasing')
        previous = entry.ppem
        ranges.append(entry)
    version = stream.integer(maximum=32767)
    if stream.peek():
        reader.fail('trailing gasp data')
    return SfdGaspTable(ranges, version)


def encode_gasp(value):
    from sfdfont._validation import number

    number(len(value.ranges), 'gasp range count', 0, 32767)
    number(value.version, 'gasp version', 0, 32767)
    data = [str(len(value.ranges)).encode()]
    for entry in value.ranges:
        number(entry.ppem, 'gasp ppem limit', 0, 65535)
        number(entry.flags, 'gasp flags', 0, 65535)
        data.extend([str(entry.ppem).encode(), str(entry.flags).encode()])
    data.append(str(value.version).encode())
    result = SfdRecord('GaspTable:', b' '.join(data))
    try:
        if decode_gasp(result) != value:
            raise SfdValidationError('gasp fields would change interpretation when written')
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
    return result
