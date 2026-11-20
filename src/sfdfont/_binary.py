from sfdfont._parser import integer
from sfdfont._reader import Reader
from sfdfont.payload import SfdPayload


def payload(reader: Reader, key: str) -> SfdPayload:
    parameters = reader.line()
    fields = parameters.split()
    if key == 'TtfInstrs:':
        if len(fields) != 1:
            reader.fail('invalid TtfInstrs header')
        length = integer(fields[0])
        terminator = 'EndTtf'
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
        terminator = 'EndImage2'
    elif key == 'Image:':
        if len(fields) != 11:
            reader.fail('invalid Image header')
        width, height, kind, stride, palette = (integer(value) for value in fields[:5])
        rle = integer(fields[10])
        if min(width, height, stride, palette, rle) < 0 or kind not in (0, 1, 2, 3):
            reader.fail('invalid Image dimensions or type')
        length = palette * 3 + (rle if rle else stride * height)
        terminator = 'EndImage'
    else:
        reader.fail('unknown binary payload')
    data = reader.ascii85(length)
    if reader.word() != terminator:
        reader.fail(f'missing {terminator}')
    return SfdPayload(key, parameters, data, terminator)
