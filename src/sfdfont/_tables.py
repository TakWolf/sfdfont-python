from sfdfont._layout import LayoutReader
from sfdfont._reader import Reader
from sfdfont.error import SfdLimitError
from sfdfont.record import SfdRecord


def private_record(reader: Reader, key: str) -> SfdRecord:
    start = reader.pos
    stream = LayoutReader(reader)
    count = stream.count()
    for _ in range(count):
        name = reader.word()
        if not name or '\0' in name:
            reader.fail('invalid Private dictionary key')
        length = stream.count()
        if reader.char() not in (b' ', b'\t'):
            reader.fail('missing Private value separator')
        # FontForge counts logical characters after removing continuations.
        # Preserve the original bytes, including spaces and embedded newlines.
        for _ in range(length):
            char = reader.char()
            if not char:
                reader.fail('truncated Private dictionary value')
            if char == b'\0':
                reader.fail('NUL in Private dictionary value')
    stream.keyword('EndPrivate')
    return SfdRecord(key, reader.data[start : reader.pos].strip())


def short_table_record(reader: Reader, key: str) -> SfdRecord:
    from sfdfont._parser import integer

    start = reader.pos
    parameters = reader.line()
    if len(parameters) < 5 or len(parameters[:4]) != 4 or not parameters[4:5].isspace():
        reader.fail('invalid ShortTable header')
    count = integer(parameters[4:].strip())
    if count < 0:
        reader.fail('negative ShortTable count')
    if count > reader.limits.max_bytes:
        reader.fail('ShortTable count exceeds document budget', SfdLimitError)
    stream = LayoutReader(reader)
    for _ in range(count):
        stream.integer(-32768, 65535)
        saved = reader.pos
        while reader.data[reader.pos : reader.pos + 1] in (b' ', b'\t'):
            reader.pos += 1
        if parameters[:4] == b'cvt ' and reader.data[reader.pos : reader.pos + 1] == b'"':
            stream.quoted()
        else:
            reader.pos = saved
    stream.keyword('EndShort')
    return SfdRecord(key, reader.data[start : reader.pos].strip())
