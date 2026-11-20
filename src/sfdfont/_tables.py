from sfdfont._layout import LayoutReader
from sfdfont._reader import Reader
from sfdfont.error import SfdLimitError, SfdParseError, SfdValidationError
from sfdfont.record import SfdRecord
from sfdfont.tables import SfdPrivateDict, SfdPrivateEntry, SfdShortTable, SfdShortTableWord

TABLE_KEYS = {'BeginPrivate:', 'ShortTable:'}


def private_record(reader: Reader, key: str) -> SfdRecord:
    start = reader.pos
    read_private(reader)
    return SfdRecord(key, reader.data[start : reader.pos].strip())


def read_private(reader: Reader) -> SfdPrivateDict:
    stream = LayoutReader(reader)
    count = stream.count()
    result = SfdPrivateDict()
    for _ in range(count):
        name = reader.word()
        if not name or '\0' in name:
            reader.fail('invalid Private dictionary key')
        length = stream.count()
        if reader.char() not in (b' ', b'\t'):
            reader.fail('missing Private value separator')
        # FontForge counts logical characters after removing continuations.
        # Preserve the original bytes, including spaces and embedded newlines.
        value = bytearray()
        for _ in range(length):
            char = reader.char()
            if not char:
                reader.fail('truncated Private dictionary value')
            if char == b'\0':
                reader.fail('NUL in Private dictionary value')
            value.extend(char)
        result.entries.append(SfdPrivateEntry(name, bytes(value)))
    stream.keyword('EndPrivate')
    return result


def short_table_record(reader: Reader, key: str) -> SfdRecord:
    start = reader.pos
    read_short_table(reader)
    return SfdRecord(key, reader.data[start : reader.pos].strip())


def read_short_table(reader: Reader) -> SfdShortTable:
    from sfdfont._parser import integer

    parameters = reader.line()
    if len(parameters) < 5 or len(parameters[:4]) != 4 or not parameters[4:5].isspace():
        reader.fail('invalid ShortTable header')
    count = integer(parameters[4:].strip())
    if count < 0:
        reader.fail('negative ShortTable count')
    if count > reader.limits.max_bytes:
        reader.fail('ShortTable count exceeds document budget', SfdLimitError)
    try:
        tag = parameters[:4].decode('ascii')
    except UnicodeDecodeError:
        reader.fail('non-ASCII ShortTable tag')
    if any(ord(char) < 32 or ord(char) > 126 for char in tag):
        reader.fail('invalid ShortTable tag')
    result = SfdShortTable(tag)
    stream = LayoutReader(reader)
    for _ in range(count):
        value = stream.integer(-32768, 65535)
        name = None
        saved = reader.pos
        while reader.data[reader.pos : reader.pos + 1] in (b' ', b'\t'):
            reader.pos += 1
        if parameters[:4] == b'cvt ' and reader.data[reader.pos : reader.pos + 1] == b'"':
            name = stream.quoted()
        else:
            reader.pos = saved
        result.words.append(SfdShortTableWord(value, name))
    stream.keyword('EndShort')
    return result


def decode_table(item, key, parse):
    if item.keyword != key:
        raise SfdParseError('unexpected text table kind')
    reader = Reader(item.value)
    result = parse(reader)
    if reader.word():
        reader.fail('trailing text table data')
    return result


def decode_private(item):
    return decode_table(item, 'BeginPrivate:', read_private)


def decode_short_table(item):
    return decode_table(item, 'ShortTable:', read_short_table)


def checked(key, data, value, decode):
    item = SfdRecord(key, data)
    try:
        parsed = decode(item)
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
    if parsed != value:
        raise SfdValidationError('text table fields would change interpretation when written')
    return item


def encode_private(value):
    parts = [str(len(value.entries)).encode()]
    for entry in value.entries:
        if (
            not isinstance(entry.key, str)
            or not entry.key
            or not entry.key.isascii()
            or any(char.isspace() or char == '\0' for char in entry.key)
            or not isinstance(entry.value, bytes)
            or b'\0' in entry.value
        ):
            raise SfdValidationError('invalid Private dictionary entry')
        parts.append(entry.key.encode() + b' ' + str(len(entry.value)).encode() + b' ' + entry.value)
    parts.append(b'EndPrivate')
    return checked('BeginPrivate:', b'\n'.join(parts), value, decode_private)


def encode_short_table(value):
    from sfdfont._strings import quote
    from sfdfont._validation import number

    if not isinstance(value.tag, str) or len(value.tag) != 4 or not all(32 <= ord(c) <= 126 for c in value.tag):
        raise SfdValidationError('ShortTable tag must contain four printable ASCII characters')
    if value.tag[0].isspace():
        raise SfdValidationError('ShortTable tag cannot begin with whitespace')
    parts = [value.tag.encode() + b' ' + str(len(value.words)).encode()]
    for word in value.words:
        number(word.value, 'ShortTable word', -32768, 65535)
        data = str(word.value).encode()
        if word.name is not None:
            if value.tag != 'cvt ' or not isinstance(word.name, str):
                raise SfdValidationError('only cvt ShortTable words can have names')
            data += b' ' + quote(word.name)
        parts.append(data)
    parts.append(b'EndShort')
    return checked('ShortTable:', b'\n'.join(parts), value, decode_short_table)


def table_identity(records):
    result = []
    for item in records:
        if item.keyword == 'BeginPrivate:':
            result.append((item.keyword, [entry.key for entry in decode_private(item).entries]))
        elif item.keyword == 'ShortTable:':
            value = decode_short_table(item)
            result.append((item.keyword, value.tag, len(value.words)))
    return result
