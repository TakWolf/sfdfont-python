from sfdfont._glyph_layout import encode_value, parse_value, raw_token, token
from sfdfont._layout import LEGACY_KERN_KEYS, LayoutReader
from sfdfont._layout_models import tag as encode_tag
from sfdfont._math import device_table
from sfdfont._reader import Reader
from sfdfont._strings import decode_text, quote
from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.legacy_layout import (
    SfdLegacyAnchorClass,
    SfdLegacyAnchorClasses,
    SfdLegacyBinding,
    SfdLegacyKerningPair,
    SfdLegacyKerningPairs,
    SfdLegacyPst,
)
from sfdfont.record import SfdRecord

LEGACY_SUBSTITUTIONS = {'Substitution:', 'MultipleSubs:', 'AlternateSubs:', 'Ligature:'}
LEGACY_PST_KEYS = LEGACY_SUBSTITUTIONS | {'Position:', 'PairPos:', 'LCarets:'}

LEGACY_GLYPH_KEYS = LEGACY_PST_KEYS | LEGACY_KERN_KEYS
LEGACY_KEYS = LEGACY_GLYPH_KEYS | {'AnchorClass:'}


def numeric(stream: LayoutReader) -> bool:
    return stream.peek() in b'0123456789' and bool(stream.peek())


def binding(stream: LayoutReader) -> SfdLegacyBinding:
    result = SfdLegacyBinding()
    if numeric(stream):
        result.flags = stream.integer()
    if numeric(stream):
        result.script_language_index = stream.integer()
    if stream.peek() == b"'":
        result.tag = stream.tag()
    elif stream.peek() == b'<':
        stream.expect(b'<')
        first = stream.integer()
        stream.expect(b',')
        result.tag = (first, stream.integer())
        stream.expect(b'>')
    return result


def parse_legacy(reader: Reader, key: str):
    stream = LayoutReader(reader)
    if key in LEGACY_PST_KEYS:
        result = SfdLegacyPst(key, binding(stream))
        if key == 'Position:':
            result.positions = [parse_value(stream)]
        elif key == 'PairPos:':
            result.glyphs = [raw_token(reader)]
            first = parse_value(stream)
            if stream.peek() == b'|':
                stream.expect(b'|')
                result.pair_separator = True
            result.positions = [first, parse_value(stream)]
        elif key == 'LCarets:':
            result.carets = [stream.integer(-32768, 32767) for _ in range(stream.count())]
        else:
            result.glyphs = decode_text(reader.line()).split()
            if key == 'Substitution:' and len(result.glyphs) != 1:
                reader.fail('single substitution requires one glyph')
            if key in ('Ligature:', 'AlternateSubs:') and not result.glyphs:
                reader.fail('empty legacy substitution glyph list')
        return result
    if key in LEGACY_KERN_KEYS:
        result = SfdLegacyKerningPairs(key)
        while stream.peek():
            pair = SfdLegacyKerningPair(stream.integer(maximum=0x7FFFFFFF), stream.integer(-32768, 32767))
            if key != 'Kerns:':
                pair.script_language_index = stream.integer()
            if key not in ('Kerns:', 'KernsSLI:'):
                pair.flags = stream.integer()
            pair.adjustments = stream.device_table()
            result.pairs.append(pair)
        return result
    if key == 'AnchorClass:':
        result = SfdLegacyAnchorClasses()
        seen = set()
        while stream.peek():
            name = stream.quoted()
            if not name or name in seen:
                reader.fail('empty or duplicate legacy anchor class')
            seen.add(name)
            feature = raw_token(reader)
            if not feature.isascii() or not 1 <= len(feature) <= 4:
                reader.fail('invalid legacy anchor feature tag')
            values = []
            for _ in range(4):
                values.append(stream.integer() if numeric(stream) else None)
            result.classes.append(SfdLegacyAnchorClass(name, feature, *values))
        return result
    reader.fail('unexpected legacy layout record kind')


def decode(record, keys):
    if record.keyword not in keys:
        raise SfdParseError('unexpected legacy layout record kind')
    reader = Reader(record.value)
    value = parse_legacy(reader, record.keyword)
    if reader.word():
        reader.fail('trailing legacy layout data')
    return value


def legacy_record(reader: Reader, key: str) -> SfdRecord:
    result = SfdRecord(key, reader.line())
    decode(result, LEGACY_KEYS)
    return result


def decode_pst(record):
    return decode(record, LEGACY_PST_KEYS)


def decode_pairs(record):
    return decode(record, LEGACY_KERN_KEYS)


def decode_anchor_classes(record):
    return decode(record, {'AnchorClass:'})


def checked(key, data, value):
    result = SfdRecord(key, data)
    try:
        decoded = decode(result, LEGACY_KEYS)
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
    if decoded != value:
        raise SfdValidationError('legacy fields would change interpretation when written')
    return result


def optional_numbers(values):
    from sfdfont._validation import number

    output = []
    omitted = False
    for value in values:
        if value is None:
            omitted = True
        else:
            if omitted:
                raise SfdValidationError('cannot omit a preceding legacy numeric field')
            number(value, 'legacy layout field', 0, 65535)
            output.append(str(value).encode())
    return output


def encode_binding(value: SfdLegacyBinding) -> bytes:
    values = optional_numbers((value.flags, value.script_language_index))
    if value.tag is not None:
        values.append(encode_tag(value.tag))
    return b' '.join(values)


def encode_pst(value: SfdLegacyPst) -> SfdRecord:
    from sfdfont._validation import check, number

    check(value.keyword in LEGACY_PST_KEYS, 'invalid legacy PST keyword')
    head = encode_binding(value.binding)
    if value.keyword in ('Position:', 'PairPos:'):
        check(not value.carets, 'unexpected legacy caret list')
        check(len(value.positions) == (2 if value.keyword == 'PairPos:' else 1), 'invalid legacy position value count')
        if value.keyword == 'PairPos:':
            check(len(value.glyphs) == 1, 'legacy pair requires a target glyph')
            body = token(value.glyphs[0]) + b' ' + encode_value(value.positions[0])
            body += (b' | ' if value.pair_separator else b' ') + encode_value(value.positions[1])
        else:
            check(not value.glyphs and not value.pair_separator, 'unexpected legacy position fields')
            body = encode_value(value.positions[0])
    elif value.keyword == 'LCarets:':
        check(not value.glyphs and not value.positions and not value.pair_separator, 'unexpected legacy caret fields')
        for caret in value.carets:
            number(caret, 'legacy ligature caret', -32768, 32767)
        body = b' '.join(str(v).encode() for v in [len(value.carets), *value.carets])
    else:
        check(
            not value.positions and not value.carets and not value.pair_separator,
            'unexpected legacy substitution fields',
        )
        body = b' '.join(token(name) for name in value.glyphs)
    return checked(value.keyword, b' '.join(part for part in [head, body] if part), value)


def encode_pairs(value: SfdLegacyKerningPairs) -> SfdRecord:
    from sfdfont._validation import check, number

    check(value.keyword in LEGACY_KERN_KEYS, 'invalid legacy kerning keyword')
    entries = []
    for pair in value.pairs:
        number(pair.target, 'legacy kerning target', 0)
        number(pair.offset, 'legacy kerning offset', -32768, 32767)
        check(
            (pair.script_language_index is not None) == (value.keyword != 'Kerns:'),
            'legacy kerning script field mismatch',
        )
        check(
            (pair.flags is not None) == (value.keyword not in ('Kerns:', 'KernsSLI:')),
            'legacy kerning flags field mismatch',
        )
        data = f'{pair.target} {pair.offset}'.encode()
        for field in (pair.script_language_index, pair.flags):
            if field is not None:
                number(field, 'legacy kerning field', 0, 65535)
                data += f' {field}'.encode()
        entries.append(data + device_table(pair.adjustments))
    return checked(value.keyword, b' '.join(entries), value)


def encode_anchor_classes(value: SfdLegacyAnchorClasses) -> SfdRecord:
    entries = []
    for entry in value.classes:
        if (
            not isinstance(entry.feature_tag, str)
            or not entry.feature_tag.isascii()
            or not 1 <= len(entry.feature_tag) <= 4
        ):
            raise SfdValidationError('invalid legacy anchor feature tag')
        data = quote(entry.name) + b' ' + token(entry.feature_tag)
        numbers = optional_numbers((entry.flags, entry.script_language_index, entry.merge_with, entry.kind))
        if numbers:
            data += b' ' + b' '.join(numbers)
        entries.append(data)
    return checked('AnchorClass:', b' '.join(entries), value)


def legacy_identity(records):
    result = []
    for record in records:
        if record.keyword in LEGACY_PST_KEYS:
            value = decode_pst(record)
            result.append((record.keyword, value.binding, tuple(value.glyphs)))
        elif record.keyword in LEGACY_KERN_KEYS:
            value = decode_pairs(record)
            result.append((record.keyword, tuple((p.target, p.script_language_index, p.flags) for p in value.pairs)))
        elif record.keyword == 'AnchorClass:':
            result.append((record.keyword, decode_anchor_classes(record).classes))
    return result
