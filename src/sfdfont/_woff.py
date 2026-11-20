from sfdfont._layout import LayoutReader
from sfdfont._reader import Reader
from sfdfont._strings import quote
from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.record import SfdRecord
from sfdfont.woff import SfdWoffMetadata


def decode_woff_metadata(item):
    if item.keyword != 'woffMetadata:':
        raise SfdParseError('unexpected WOFF metadata record kind')
    reader = Reader(item.value)
    stream = LayoutReader(reader)
    result = SfdWoffMetadata(stream.quoted())
    if stream.peek():
        reader.fail('trailing WOFF metadata data')
    return result


def encode_woff_metadata(value):
    if not isinstance(value.text, str):
        raise SfdValidationError('WOFF metadata must be text')
    return SfdRecord('woffMetadata:', quote(value.text))
