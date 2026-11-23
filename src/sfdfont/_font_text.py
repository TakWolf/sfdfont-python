from sfdfont._strings import decode_text
from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.font_text import SfdFontText
from sfdfont.record import SfdRecord

FONT_TEXT_KEYS = {'FONDName:', 'DefaultBaseFilename:', 'XUID:'}


def decode_font_text(item):
    if item.keyword not in FONT_TEXT_KEYS:
        raise SfdParseError('unexpected font text record kind')
    if not isinstance(item.value, bytes) or any(c in item.value for c in (b'\0', b'\r', b'\n')):
        raise SfdParseError('invalid font text value')
    return SfdFontText(item.keyword, decode_text(item.value.strip(b' \t')))


def encode_font_text(value):
    from sfdfont._writer import plain

    if value.keyword not in FONT_TEXT_KEYS or not isinstance(value.text, str):
        raise SfdValidationError('invalid font text model')
    data = plain(value.text)
    if data.endswith(b'\\'):
        raise SfdValidationError('font text ends with a continuation escape')
    result = SfdRecord(value.keyword, data)
    if decode_font_text(result) != value:
        raise SfdValidationError('font text would change interpretation when written')
    return result
