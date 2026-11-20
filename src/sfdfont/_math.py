import re

from sfdfont._layout import LayoutReader
from sfdfont._reader import Reader
from sfdfont._strings import decode_text
from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.math import SfdGlyphAssembly, SfdGlyphPart, SfdGlyphVariants, SfdMathKern, SfdMathKernEntry, SfdMathValue
from sfdfont.record import SfdRecord

MATH_VALUE_KEYS = {
    'ItalicCorrection:',
    'TopAccentHorizontal:',
    'GlyphCompositionVerticalIC:',
    'GlyphCompositionHorizontalIC:',
}
ASSEMBLY_KEYS = {'GlyphCompositionVertical:', 'GlyphCompositionHorizontal:'}
VARIANT_KEYS = {'GlyphVariantsVertical:', 'GlyphVariantsHorizontal:'}
MATH_KERN_KEYS = {'TopRightVertex:', 'TopLeftVertex:', 'BottomRightVertex:', 'BottomLeftVertex:'}
GLYPH_MATH_KEYS = MATH_VALUE_KEYS | ASSEMBLY_KEYS | VARIANT_KEYS | MATH_KERN_KEYS | {'IsExtendedShape:'}


def math_constant(key: str) -> bool:
    return bool(re.fullmatch(r'MATH:[A-Za-z][A-Za-z0-9]*:', key))


def finish(reader: Reader) -> None:
    if reader.word():
        reader.fail('trailing MATH record data')


def device_table(values: dict[int, int]) -> bytes:
    from sfdfont._validation import number

    for size, correction in values.items():
        number(size, 'device size', 0, 65535)
        number(correction, 'device correction', -128, 127)
    if not values:
        return b''
    first, last = min(values), max(values)
    if sorted(values) != list(range(first, last + 1)):
        raise SfdValidationError('device table sizes must be contiguous')
    return (
        f' {{{first}-{last} '.encode()
        + b','.join(str(values.get(i, 0)).encode() for i in range(first, last + 1))
        + b'}'
    )


def glyph_token(reader: Reader) -> str:
    reader.whitespace()
    match = re.match(rb'[^\s%\x00]+', reader.data[reader.pos :])
    if match is None:
        reader.fail('expected MATH component glyph')
    reader.pos += len(match[0])
    return decode_text(match[0])


def glyph_name(value: str) -> bytes:
    from sfdfont._writer import plain

    if not isinstance(value, str) or not re.fullmatch(r'[^\s%\x00]+', value):
        raise SfdValidationError('invalid MATH glyph name')
    return plain(value)


def parse_math(reader: Reader, key: str):
    stream = LayoutReader(reader)
    if key in MATH_VALUE_KEYS or math_constant(key):
        return SfdMathValue(key, stream.integer(-32768, 32767), stream.device_table())
    if key in ASSEMBLY_KEYS:
        result = SfdGlyphAssembly(key)
        for _ in range(stream.count()):
            glyph = glyph_token(reader)
            if stream.peek() == b'%':
                stream.expect(b'%')
            extender = stream.integer(maximum=1)
            values = []
            for _ in range(3):
                if stream.peek() == b',':
                    stream.expect(b',')
                values.append(stream.integer())
            if max(values[:2]) > values[2]:
                reader.fail('MATH connector exceeds component advance')
            result.parts.append(SfdGlyphPart(glyph, bool(extender), *values))
        return result
    if key in MATH_KERN_KEYS:
        result = SfdMathKern(key)
        for _ in range(stream.count()):
            height = stream.integer(-32768, 32767)
            height_adjustments = stream.device_table()
            if stream.peek() == b',':
                stream.expect(b',')
            kern = stream.integer(-32768, 32767)
            result.entries.append(SfdMathKernEntry(height, kern, height_adjustments, stream.device_table()))
        return result
    if key in VARIANT_KEYS:
        return SfdGlyphVariants(key, decode_text(reader.line()).split())
    if key == 'IsExtendedShape:':
        return stream.integer(maximum=1)
    reader.fail(f'not a MATH record: {key}')


def math_record(reader: Reader, key: str) -> SfdRecord:
    start = reader.pos
    parse_math(reader, key)
    return SfdRecord(key, reader.data[start : reader.pos].strip())


def decode(record: SfdRecord, keys):
    if record.keyword not in keys:
        raise SfdParseError('unexpected MATH record kind')
    reader = Reader(record.value)
    result = parse_math(reader, record.keyword)
    finish(reader)
    return result


def decode_math_value(record: SfdRecord) -> SfdMathValue:
    if not math_constant(record.keyword) and record.keyword not in MATH_VALUE_KEYS:
        raise SfdParseError('not a MATH value record')
    return decode(record, {record.keyword})


def decode_assembly(record: SfdRecord) -> SfdGlyphAssembly:
    return decode(record, ASSEMBLY_KEYS)


def decode_variants(record: SfdRecord) -> SfdGlyphVariants:
    return decode(record, VARIANT_KEYS)


def decode_math_kern(record: SfdRecord) -> SfdMathKern:
    return decode(record, MATH_KERN_KEYS)


def checked(keyword, data, keys) -> SfdRecord:
    result = SfdRecord(keyword, data)
    try:
        decode(result, keys)
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
    return result


def encode_math_value(value: SfdMathValue) -> SfdRecord:
    from sfdfont._validation import check, number

    check(math_constant(value.keyword) or value.keyword in MATH_VALUE_KEYS, 'invalid MATH value keyword')
    number(value.value, 'MATH value', -32768, 32767)
    return checked(value.keyword, str(value.value).encode() + device_table(value.adjustments), {value.keyword})


def encode_assembly(value: SfdGlyphAssembly) -> SfdRecord:
    from sfdfont._validation import check, number

    parts = [str(len(value.parts)).encode()]
    for part in value.parts:
        check(isinstance(part.is_extender, bool), 'invalid MATH extender flag')
        for metric in (part.start_connector, part.end_connector, part.full_advance):
            number(metric, 'MATH component metric', 0, 65535)
        parts.append(
            glyph_name(part.glyph)
            + f'%{int(part.is_extender)},{part.start_connector},{part.end_connector},{part.full_advance}'.encode()
        )
    return checked(value.keyword, b' '.join(parts), ASSEMBLY_KEYS)


def encode_variants(value: SfdGlyphVariants) -> SfdRecord:
    return checked(value.keyword, b' '.join(glyph_name(g) for g in value.glyphs), VARIANT_KEYS)


def encode_math_kern(value: SfdMathKern) -> SfdRecord:
    from sfdfont._validation import number

    data = str(len(value.entries)).encode()
    for entry in value.entries:
        number(entry.height, 'MATH kern height', -32768, 32767)
        number(entry.kern, 'MATH kern', -32768, 32767)
        data += b' ' + str(entry.height).encode() + device_table(entry.height_adjustments)
        data += b',' + str(entry.kern).encode() + device_table(entry.kern_adjustments)
    return checked(value.keyword, data, MATH_KERN_KEYS)


def validate_math(font) -> None:
    glyphs = list(font.iter_glyphs())
    names = {glyph.name for glyph in glyphs}
    try:
        for record in font.metadata.records:
            if math_constant(record.keyword):
                decode_math_value(record)
            elif record.keyword in GLYPH_MATH_KEYS:
                raise SfdValidationError('glyph MATH record in font metadata')
        for glyph in glyphs:
            seen = set()
            records = [*glyph.records, *(record for layer in glyph.layers for record in layer.records)]
            for record in records:
                if record.keyword not in GLYPH_MATH_KEYS:
                    continue
                if record.keyword in seen:
                    raise SfdValidationError(f'duplicate glyph MATH record {record.keyword}')
                seen.add(record.keyword)
                value = decode(record, GLYPH_MATH_KEYS)
                targets = (
                    value.glyphs
                    if record.keyword in VARIANT_KEYS
                    else [p.glyph for p in value.parts]
                    if record.keyword in ASSEMBLY_KEYS
                    else []
                )
                for name in targets:
                    if name not in names:
                        raise SfdValidationError(f'unknown MATH glyph {name!r}')
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
