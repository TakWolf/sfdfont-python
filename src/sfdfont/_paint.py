import math
import re

from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.paint import SfdGradient, SfdGradientStop, SfdPaint, SfdPattern


def decode_paint(data: bytes) -> tuple[int, SfdPaint]:
    from sfdfont._parser import integer, real

    fields = re.findall(rb'\[|\]|[^\s\[\]]+', data)
    if len(fields) < 19 or fields[11] != b'[' or fields[16:18] != [b']', b'['] or fields[-1] != b']':
        raise SfdParseError('invalid Type 3 layer header')
    if any(value not in (b'0', b'1') for value in fields[1:4]):
        raise SfdParseError('invalid Type 3 fill/stroke flags')
    if any(not re.fullmatch(rb'#[0-9a-fA-F]{1,8}', fields[index]) for index in (4, 6)):
        raise SfdParseError('invalid Type 3 colour')
    if fields[9] not in (b'miter', b'round', b'bevel', b'inher', b'inherited'):
        raise SfdParseError('invalid line join')
    if fields[10] not in (b'butt', b'round', b'square', b'inher', b'inherited'):
        raise SfdParseError('invalid line cap')
    paint = SfdPaint(
        bool(integer(fields[1])),
        bool(integer(fields[2])),
        bool(integer(fields[3])),
        int(fields[4][1:], 16),
        real(fields[5]),
        int(fields[6][1:], 16),
        real(fields[7]),
        real(fields[8]),
        'inherited' if fields[9] == b'inher' else fields[9].decode('ascii'),
        'inherited' if fields[10] == b'inher' else fields[10].decode('ascii'),
        tuple(real(v) for v in fields[12:16]),
        tuple(integer(v) for v in fields[18:-1]),
    )
    return integer(fields[0]), paint


def validate_paint(paint: SfdPaint) -> None:
    from sfdfont._validation import check, number

    check(all(isinstance(v, bool) for v in (paint.fill, paint.stroke, paint.fill_first)), 'invalid paint flags')
    for color in (paint.fill_color, paint.stroke_color):
        number(color, 'paint colour', 0, 0xFFFFFFFF)
    for opacity in (paint.fill_opacity, paint.stroke_opacity):
        check(opacity == -1 or 0 <= opacity <= 1, 'paint opacity out of range')
    check(math.isfinite(paint.stroke_width) and paint.stroke_width >= -1, 'invalid stroke width')
    check(paint.line_join in ('miter', 'round', 'bevel', 'inherited'), 'invalid line join')
    check(paint.line_cap in ('butt', 'round', 'square', 'inherited'), 'invalid line cap')
    check(len(paint.pen_transform) == 4 and all(math.isfinite(v) for v in paint.pen_transform), 'invalid pen transform')
    check(len(paint.dash) <= 8, 'pen dash pattern exceeds eight entries')
    for value in paint.dash:
        number(value, 'pen dash', 0, 255)
    check(paint.dash == (0, 255) or all(paint.dash), 'zero dash requires inherited pattern (0, 255)')
    for gradient, pattern in [(paint.fill_gradient, paint.fill_pattern), (paint.stroke_gradient, paint.stroke_pattern)]:
        check(gradient is None or pattern is None, 'a brush cannot have both a gradient and a pattern')
        if gradient is not None:
            validate_gradient(gradient)
        if pattern is not None:
            validate_pattern(pattern)


def encode_paint(index: int, paint: SfdPaint) -> bytes:
    validate_paint(paint)
    join = 'inher' if paint.line_join == 'inherited' else paint.line_join
    cap = 'inher' if paint.line_cap == 'inherited' else paint.line_cap
    data = (
        f'{index} {int(paint.fill)} {int(paint.stroke)} {int(paint.fill_first)} '
        f'#{paint.fill_color:08x} {paint.fill_opacity:.17g} #{paint.stroke_color:08x} '
        f'{paint.stroke_opacity:.17g} {paint.stroke_width:.17g} {join} {cap} ['
    )
    data += ' '.join(format(value, '.17g') for value in paint.pen_transform) + '] ['
    data += ' '.join(format(value, '.17g') for value in paint.dash) + ']'
    try:
        return data.encode('ascii')
    except UnicodeError as error:
        raise SfdValidationError('invalid paint data') from error


def color(value: bytes) -> int:
    if not re.fullmatch(rb'#[0-9a-fA-F]{1,8}', value):
        raise SfdParseError('invalid gradient colour')
    return int(value[1:], 16)


def decode_gradient(data: bytes) -> SfdGradient:
    from sfdfont._parser import integer, real

    fields = re.findall(rb'[{};]|[^{}\s;]+', data)
    if len(fields) < 9 or fields[1] != b';' or fields[4] != b';' or fields[7] not in (b'pad', b'reflect', b'repeat'):
        raise SfdParseError('invalid gradient header')
    count = integer(fields[8])
    if count < 0 or len(fields) != 9 + 5 * count:
        raise SfdParseError('gradient stop count mismatch')
    stops = []
    for index in range(9, len(fields), 5):
        if fields[index] != b'{' or fields[index + 4] != b'}':
            raise SfdParseError('invalid gradient stop delimiters')
        stops.append(SfdGradientStop(real(fields[index + 1]), color(fields[index + 2]), real(fields[index + 3])))
    return SfdGradient(
        (real(fields[0]), real(fields[2])),
        (real(fields[3]), real(fields[5])),
        real(fields[6]),
        fields[7].decode(),
        stops,
    )


def decode_pattern(data: bytes) -> SfdPattern:
    from sfdfont._parser import real
    from sfdfont._strings import decode_text

    fields = re.findall(rb'[\[\];]|[^\[\]\s;]+', data)
    if len(fields) != 12 or fields[2] != b';' or fields[4] != b'[' or fields[-1] != b']':
        raise SfdParseError('invalid pattern header')
    return SfdPattern(decode_text(fields[0]), real(fields[1]), real(fields[3]), tuple(real(v) for v in fields[5:11]))


def validate_gradient(gradient: SfdGradient) -> None:
    from sfdfont._validation import check, number

    for point in (gradient.start, gradient.end):
        check(len(point) == 2 and all(math.isfinite(v) for v in point), 'invalid gradient coordinate')
    check(math.isfinite(gradient.radius) and gradient.radius >= 0, 'invalid gradient radius')
    check(gradient.spread in ('pad', 'reflect', 'repeat'), 'invalid gradient spread')
    check(len(gradient.stops) >= 2, 'gradient requires at least two stops')
    last = -1
    for stop in gradient.stops:
        check(last <= stop.offset <= 1, 'gradient stops must be ordered between zero and one')
        check(0 <= stop.offset, 'negative gradient offset')
        check(0 <= stop.opacity <= 1, 'invalid gradient opacity')
        number(stop.color, 'gradient colour', 0, 0xFFFFFFFF)
        last = stop.offset


def validate_pattern(pattern: SfdPattern) -> None:
    from sfdfont._validation import check

    check(
        isinstance(pattern.glyph, str) and bool(re.fullmatch(r'[^\s\x00;\[\]]+', pattern.glyph)),
        'invalid pattern glyph',
    )
    check(all(math.isfinite(v) and v > 0 for v in (pattern.width, pattern.height)), 'invalid pattern size')
    check(len(pattern.transform) == 6 and all(math.isfinite(v) for v in pattern.transform), 'invalid pattern transform')
    a, b, c, d, _, _ = pattern.transform
    check(a * d != b * c, 'singular pattern transform')


def encode_gradient(gradient: SfdGradient) -> bytes:
    from sfdfont._writer import scalar

    validate_gradient(gradient)
    result = b' '.join(
        [
            scalar(gradient.start[0]) + b';' + scalar(gradient.start[1]),
            scalar(gradient.end[0]) + b';' + scalar(gradient.end[1]),
            scalar(gradient.radius),
            gradient.spread.encode(),
            str(len(gradient.stops)).encode(),
        ]
    )
    for stop in gradient.stops:
        result += b' {' + scalar(stop.offset) + f' #{stop.color:06x} '.encode() + scalar(stop.opacity) + b'}'
    return result


def encode_pattern(pattern: SfdPattern) -> bytes:
    from sfdfont._writer import plain, scalar

    validate_pattern(pattern)
    return (
        plain(pattern.glyph)
        + b' '
        + scalar(pattern.width)
        + b';'
        + scalar(pattern.height)
        + b' ['
        + b' '.join(scalar(v) for v in pattern.transform)
        + b']'
    )
