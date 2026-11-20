import math
import re

from sfdfont._layout import PST_KEYS, SUBSTITUTION_KEYS, LayoutReader
from sfdfont._math import device_table
from sfdfont._reader import Reader
from sfdfont._strings import decode_text, quote
from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.glyph_layout import (
    SfdAnchor,
    SfdAnchorClass,
    SfdAnchorClasses,
    SfdKerningPair,
    SfdKerningPairs,
    SfdLigatureCarets,
    SfdPairPosition,
    SfdPosition,
    SfdPositionValue,
    SfdSubstitution,
)
from sfdfont.record import SfdRecord

KERN_PAIR_KEYS = {'Kerns2:', 'VKerns2:'}
GLYPH_LAYOUT_KEYS = PST_KEYS | KERN_PAIR_KEYS | {'AnchorPoint:'}
ROOT_LAYOUT_KEYS = {'AnchorClass2:'}
ANCHOR_KINDS = {'mark', 'basechar', 'baselig', 'basemark', 'entry', 'exit'}
VALUE_FIELDS = ('x_offset', 'y_offset', 'x_advance', 'y_advance')
ADJUSTMENT_FIELDS = ('x_adjustments', 'y_adjustments', 'x_advance_adjustments', 'y_advance_adjustments')


def parse_value(stream: LayoutReader) -> SfdPositionValue:
    value = SfdPositionValue()
    for label, field in zip(('dx=', 'dy=', 'dh=', 'dv='), VALUE_FIELDS, strict=True):
        stream.expect(label.encode())
        setattr(value, field, stream.integer(-32768, 32767))
    if stream.peek() == b'[':
        stream.expect(b'[')
        seen = set()
        fields = dict(zip((b'ddx=', b'ddy=', b'ddh=', b'ddv='), ADJUSTMENT_FIELDS, strict=True))
        while stream.peek() != b']':
            stream.reader.whitespace()
            label = stream.reader.data[stream.reader.pos : stream.reader.pos + 4]
            if label not in fields or label in seen:
                stream.reader.fail('invalid or duplicate positioning device field')
            seen.add(label)
            stream.expect(label)
            if stream.peek() != b'{':
                stream.reader.fail('expected positioning device table')
            setattr(value, fields[label], stream.device_table())
        stream.expect(b']')
    return value


def raw_token(reader: Reader) -> str:
    reader.whitespace()
    match = re.match(rb'[^\s\x00]+', reader.data[reader.pos :])
    if match is None:
        reader.fail('expected glyph name')
    reader.pos += len(match[0])
    return decode_text(match[0])


def parse_layout(reader: Reader, key: str):
    from sfdfont._parser import real

    stream = LayoutReader(reader)
    if key == 'Position2:':
        return SfdPosition(stream.quoted(), parse_value(stream))
    if key == 'PairPos2:':
        subtable, glyph = stream.quoted(), raw_token(reader)
        return SfdPairPosition(subtable, glyph, parse_value(stream), parse_value(stream))
    if key in SUBSTITUTION_KEYS:
        subtable = stream.quoted()
        glyphs = decode_text(reader.line()).split()
        if (key == 'Substitution2:' and len(glyphs) != 1) or (key in ('AlternateSubs2:', 'Ligature2:') and not glyphs):
            reader.fail('invalid substitution glyph count')
        return SfdSubstitution(key, subtable, glyphs)
    if key in KERN_PAIR_KEYS:
        result = SfdKerningPairs(key)
        while stream.peek():
            target = stream.integer(maximum=0x7FFFFFFF)
            offset = stream.integer(-32768, 32767)
            subtable = stream.quoted()
            result.pairs.append(SfdKerningPair(target, offset, subtable, stream.device_table()))
        return result
    if key == 'LCarets2:':
        return SfdLigatureCarets([stream.integer(-32768, 32767) for _ in range(stream.count())])
    if key == 'AnchorPoint:':
        name = stream.quoted()
        x, y, kind = real(reader.word()), real(reader.word()), reader.word()
        if kind not in ANCHOR_KINDS:
            reader.fail('invalid anchor kind')
        index = stream.integer(-32768, 32767)
        xadj = stream.device_table()
        yadj = stream.device_table()
        ttf = stream.integer() if stream.peek() else None
        return SfdAnchor(name, x, y, kind, index, xadj, yadj, ttf)
    if key == 'AnchorClass2:':
        classes = []
        names = set()
        while stream.peek():
            name = stream.quoted()
            if not name or name in names:
                reader.fail('empty or duplicate anchor class name')
            names.add(name)
            subtable = (stream.quoted() or None) if stream.peek() == b'"' else None
            kind = stream.integer() if stream.peek() not in (b'', b'"') else None
            classes.append(SfdAnchorClass(name, subtable, kind))
        return SfdAnchorClasses(classes)
    reader.fail(f'not a glyph layout record: {key}')


def decode(record, keys):
    if record.keyword not in keys:
        raise SfdParseError('unexpected glyph layout record kind')
    reader = Reader(record.value)
    result = parse_layout(reader, record.keyword)
    if reader.word():
        reader.fail('trailing glyph layout data')
    return result


def layout_record(reader: Reader, key: str) -> SfdRecord:
    result = SfdRecord(key, reader.line())
    decode(result, GLYPH_LAYOUT_KEYS | ROOT_LAYOUT_KEYS)
    return result


def decode_position(record):
    return decode(record, {'Position2:'})


def decode_pair(record):
    return decode(record, {'PairPos2:'})


def decode_substitution(record):
    return decode(record, SUBSTITUTION_KEYS)


def decode_carets(record):
    return decode(record, {'LCarets2:'})


def decode_anchor(record):
    return decode(record, {'AnchorPoint:'})


def decode_anchor_classes(record):
    return decode(record, ROOT_LAYOUT_KEYS)


def checked(key, data, keys):
    result = SfdRecord(key, data)
    try:
        decode(result, keys)
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
    return result


def token(value: str) -> bytes:
    from sfdfont._writer import plain

    if not isinstance(value, str) or not re.fullmatch(r'[^\s\x00]+', value):
        raise SfdValidationError('invalid positioning glyph name')
    return plain(value)


def subtable_name(name):
    if not name:
        raise SfdValidationError('empty glyph layout subtable')
    return quote(name)


def encode_value(value: SfdPositionValue) -> bytes:
    from sfdfont._validation import number

    result = []
    for label, field in zip(('dx', 'dy', 'dh', 'dv'), VALUE_FIELDS, strict=True):
        metric = getattr(value, field)
        number(metric, 'positioning value', -32768, 32767)
        result.append(f'{label}={metric}'.encode())
    data = b' '.join(result)
    if any(getattr(value, field) for field in ADJUSTMENT_FIELDS):
        data += b' ['
        data += b' '.join(
            label.encode() + b'=' + (device_table(getattr(value, field)).strip() or b'{}')
            for label, field in zip(('ddx', 'ddy', 'ddh', 'ddv'), ADJUSTMENT_FIELDS, strict=True)
        )
        data += b']'
    return data


def encode_position(value):
    return checked('Position2:', subtable_name(value.subtable) + b' ' + encode_value(value.value), {'Position2:'})


def encode_pair(value):
    data = (
        subtable_name(value.subtable)
        + b' '
        + token(value.glyph)
        + b' '
        + encode_value(value.first)
        + b' '
        + encode_value(value.second)
    )
    return checked('PairPos2:', data, {'PairPos2:'})


def encode_substitution(value):
    return checked(
        value.keyword,
        subtable_name(value.subtable) + b' ' + b' '.join(token(g) for g in value.glyphs),
        SUBSTITUTION_KEYS,
    )


def encode_carets(value):
    from sfdfont._validation import number

    for caret in value.carets:
        number(caret, 'ligature caret', -32768, 32767)
    return checked('LCarets2:', b' '.join(str(v).encode() for v in [len(value.carets), *value.carets]), {'LCarets2:'})


def encode_anchor(value):
    from sfdfont._validation import check, number
    from sfdfont._writer import scalar

    check(bool(value.name), 'empty anchor class name')
    check(value.kind in ANCHOR_KINDS, 'invalid anchor kind')
    check(math.isfinite(value.x) and math.isfinite(value.y), 'nonfinite anchor coordinate')
    number(value.ligature_index, 'anchor ligature index', -32768, 32767)
    data = quote(value.name) + b' ' + scalar(value.x) + b' ' + scalar(value.y)
    data += b' ' + value.kind.encode() + f' {value.ligature_index}'.encode()
    if value.x_adjustments or value.y_adjustments:
        data += (device_table(value.x_adjustments) or b' {}') + (device_table(value.y_adjustments) or b' {}')
    if value.ttf_index is not None:
        number(value.ttf_index, 'anchor TTF point index', 0, 65535)
        data += f' {value.ttf_index}'.encode()
    return checked('AnchorPoint:', data, {'AnchorPoint:'})


def encode_anchor_classes(value):
    from sfdfont._validation import number

    parts = []
    for item in value.classes:
        if item.subtable == '':
            raise SfdValidationError('use None for an unassociated anchor class')
        data = quote(item.name) + b' ' + quote(item.subtable or '')
        if item.kind is not None:
            number(item.kind, 'anchor class type', 0, 65535)
            data += f' {item.kind}'.encode()
        parts.append(data)
    return checked('AnchorClass2:', b' '.join(parts), ROOT_LAYOUT_KEYS)


def decode_kerning_pairs(record):
    return decode(record, KERN_PAIR_KEYS)


def encode_kerning_pairs(value):
    from sfdfont._validation import number

    parts = []
    for pair in value.pairs:
        number(pair.target, 'kerning glyph ID', 0)
        number(pair.offset, 'pair kerning offset', -32768, 32767)
        parts.append(
            f'{pair.target} {pair.offset} '.encode() + subtable_name(pair.subtable) + device_table(pair.adjustments)
        )
    return checked(value.keyword, b' '.join(parts), KERN_PAIR_KEYS)
