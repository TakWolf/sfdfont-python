import math
import re

from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.paint import SfdPaint


def decode_paint(data: bytes) -> tuple[int, SfdPaint]:
    from sfdfont._parser import integer, real

    fields = re.findall(rb'\[|\]|[^\s\[\]]+', data)
    if len(fields) < 19 or fields[11] != b'[' or fields[16:18] != [b']', b'['] or fields[-1] != b']':
        raise SfdParseError('invalid Type 3 layer header')
    if any(value not in (b'0', b'1') for value in fields[1:4]):
        raise SfdParseError('invalid Type 3 fill/stroke flags')
    if any(not re.fullmatch(rb'#[0-9a-fA-F]{1,8}', fields[index]) for index in (4, 6)):
        raise SfdParseError('invalid Type 3 colour')
    if fields[9] not in (b'miter', b'round', b'bevel', b'inherited'):
        raise SfdParseError('invalid line join')
    if fields[10] not in (b'butt', b'round', b'square', b'inherited'):
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
        fields[9].decode('ascii'),
        fields[10].decode('ascii'),
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


def encode_paint(index: int, paint: SfdPaint) -> bytes:
    validate_paint(paint)
    data = (
        f'{index} {int(paint.fill)} {int(paint.stroke)} {int(paint.fill_first)} '
        f'#{paint.fill_color:08x} {paint.fill_opacity:.17g} #{paint.stroke_color:08x} '
        f'{paint.stroke_opacity:.17g} {paint.stroke_width:.17g} {paint.line_join} {paint.line_cap} ['
    )
    data += ' '.join(format(value, '.17g') for value in paint.pen_transform) + '] ['
    data += ' '.join(format(value, '.17g') for value in paint.dash) + ']'
    try:
        return data.encode('ascii')
    except UnicodeError as error:
        raise SfdValidationError('invalid paint data') from error
