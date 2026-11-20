from sfdfont._layout import LayoutReader
from sfdfont._reader import Reader
from sfdfont._strings import decode_text, quote
from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.legacy_names import SfdStyleMapName
from sfdfont.record import SfdRecord

LEGACY_NAME_KEYS = {'OS2StyleName:', 'StyleMapFamilyName:', 'OS2FamilyName:'}


def decode_style_map_name(item):
    if item.keyword not in LEGACY_NAME_KEYS:
        raise SfdParseError('unexpected style mapping name kind')
    if not item.value.lstrip().startswith(b'"'):
        if b'\0' in item.value:
            raise SfdParseError('NUL in plain style mapping name')
        return SfdStyleMapName(item.keyword, decode_text(item.value.strip()), False)
    reader = Reader(item.value)
    stream = LayoutReader(reader)
    result = SfdStyleMapName(item.keyword, stream.quoted())
    if stream.peek():
        reader.fail('trailing style mapping name data')
    return result


def encode_style_map_name(value):
    from sfdfont._writer import plain

    if value.keyword not in LEGACY_NAME_KEYS or not isinstance(value.name, str) or not isinstance(value.quoted, bool):
        raise SfdValidationError('invalid style mapping name')
    data = quote(value.name) if value.quoted else plain(value.name)
    if not value.quoted and data.endswith(b'\\'):
        raise SfdValidationError('plain style mapping name ends with a continuation escape')
    result = SfdRecord(value.keyword, data)
    try:
        if decode_style_map_name(result) != value:
            raise SfdValidationError('style mapping name would change interpretation when written')
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
    return result


def restore_pending_names(records, pending):
    """Merge trailing prefixes back into metadata in linear time."""
    result = []
    cursor = 0
    for position, item in pending:
        result.extend(records[cursor:position])
        result.append(item)
        cursor = position
    result.extend(records[cursor:])
    return result
