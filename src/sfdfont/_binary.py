from sfdfont._parser import integer, real
from sfdfont._reader import Reader
from sfdfont.error import SfdLimitError
from sfdfont.payload import SfdPayload


def payload(reader: Reader, key: str) -> SfdPayload:
    if key == 'BeginSubrs:':
        count = integer(reader.word())
        if count < 0:
            reader.fail('negative Type 1 subroutine count')
        if count > reader.limits.max_bytes:
            reader.fail('Type 1 subroutine count exceeds document budget', SfdLimitError)
        lengths = []
        for _ in range(count):
            length = integer(reader.word())
            if length < 0:
                reader.fail('negative Type 1 subroutine length')
            lengths.append(length)
        parameters = b' '.join(str(value).encode() for value in [count, *lengths])
        return SfdPayload(key, parameters, reader.ascii85(sum(lengths)), '')
    parameters = reader.line()
    fields = parameters.split()
    if key in ('TtfInstrs:', 'OrigType1:'):
        if len(fields) != 1:
            reader.fail(f'invalid {key} header')
        length = integer(fields[0])
        terminator = 'EndTtf' if key == 'TtfInstrs:' else ''
    elif key == 'TtfTable:':
        # Tags are four literal bytes and can include spaces, e.g. "cvt ".
        if len(parameters) < 5:
            reader.fail('invalid TtfTable header')
        length = integer(parameters[4:].strip())
        terminator = 'EndTtf'
    elif key == 'Image2:':
        if len(fields) != 6 or fields[0] != b'image/png':
            reader.fail('unsupported Image2 header')
        length = integer(fields[1])
        for value in fields[2:]:
            real(value)
        terminator = 'EndImage2'
    elif key == 'Image:':
        if len(fields) != 11:
            reader.fail('invalid Image header')
        width, height, kind, stride, palette = (integer(value) for value in fields[:5])
        rle = integer(fields[10])
        for value in fields[6:10]:
            real(value)
        if min(width, height, stride, palette, rle) < 0 or kind not in (0, 1, 2, 3):
            reader.fail('invalid Image dimensions or type')
        length = palette * 3 + (rle if rle else stride * height)
        terminator = 'EndImage'
    else:
        reader.fail('unknown binary payload')
    data = reader.ascii85(length)
    if terminator and reader.word() != terminator:
        reader.fail(f'missing {terminator}')
    return SfdPayload(key, parameters, data, terminator)
