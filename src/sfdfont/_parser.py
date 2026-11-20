from __future__ import annotations

import math
import re
from typing import BinaryIO

from sfdfont._reader import Reader
from sfdfont._strings import decode_text, decode_utf7
from sfdfont.error import SfdLimitError, SfdParseError, SfdUnsupportedError, SfdValidationError
from sfdfont.font import SfdFont
from sfdfont.glyph import SfdAlternateUnicode, SfdGlyph
from sfdfont.layer import SfdLayer, SfdLayerInfo
from sfdfont.limits import SfdReadLimits
from sfdfont.metadata import SfdLanguageNames
from sfdfont.outline import SfdContour, SfdPoint
from sfdfont.record import SfdRecord
from sfdfont.reference import SfdReference

_TEXT_FIELDS = {
    'FontName:': 'font_name',
    'FullName:': 'full_name',
    'FamilyName:': 'family_name',
    'Weight:': 'weight',
    'Copyright:': 'copyright',
    'Version:': 'version',
    'Encoding:': 'encoding',
}
_MULTILINE = {
    'BeginPrivate:': 'EndPrivate',
    'TtInstrs:': 'EndTTInstrs',
    'TtTable:': 'EndTTInstrs',
    'ShortTable:': 'EndShort',
}
_UNSUPPORTED = {
    'BeginSubFonts:',
    'BeginMMFonts:',
    'MMCounts:',
    'SplineFontDB:',
    'Multilayer:',
    'MultiLayer:',
    'Grid',
    'GridOrder2:',
    'Image:',
    'Image2:',
    'Spiro',
    'Named:',
    'NamedP:',
    'PathFlags:',
    'PathStart:',
    'PickledData:',
    'PickledDataWithLists:',
    'BeginUndo',
    'BeginRedo',
    'Lookup:',
    'KernClass:',
    'VKernClass:',
    'ChainSub:',
    'ChainPos:',
    'ContextSub:',
    'ContextPos:',
    'KernClass2:',
    'KernClass3:',
    'ContextPos2:',
    'ContextSub2:',
    'ChainPos2:',
    'ChainSub2:',
}


def tokens(value: bytes) -> list[bytes]:
    parts = re.findall(rb'"[^"\r\n]*"|[^\s]+', value)
    if any(part.count(b'"') not in (0, 2) for part in parts):
        raise SfdParseError('unterminated quoted string')
    return parts


def string(value: bytes) -> str:
    if value.startswith(b'"'):
        if not value.endswith(b'"') or len(value) < 2 or b'"' in value[1:-1]:
            raise SfdParseError('invalid quoted string')
        return decode_utf7(value[1:-1])
    return decode_text(value)


def integer(value: bytes | str) -> int:
    if len(value) > 12:
        raise SfdParseError('integer exceeds supported field size')
    if not re.fullmatch(rb'[+-]?\d+', value.encode() if isinstance(value, str) else value):
        raise SfdParseError(f'invalid integer: {value!r}')
    return int(value)


def real(value: bytes | str) -> float:
    if len(value) > 128:
        raise SfdParseError('coordinate exceeds supported field size')
    try:
        number = float(value)
    except ValueError as error:
        raise SfdParseError(f'invalid coordinate: {value!r}') from error
    if not math.isfinite(number):
        raise SfdParseError('nonfinite coordinate')
    return number


def record(reader: Reader, key: str) -> SfdRecord:
    if key in ('StartChar:', 'BeginChars:', 'BitmapFont:', 'BDFChar:', 'BDFRefChar:'):
        reader.fail(f'misplaced structural record {key}')
    if key in ('PickledData:', 'PickledDataWithLists:'):
        start = reader.pos
        while reader.pos < len(reader.data) and reader.data[reader.pos] in b' \t':
            reader.pos += 1
        if reader.char() != b'"':
            reader.fail('expected quoted pickle payload')
        escaped = False
        while reader.pos < len(reader.data):
            char = reader.data[reader.pos]
            reader.pos += 1
            if char == 34 and not escaped:
                return SfdRecord(key, reader.data[start : reader.pos].strip())
            escaped = char == 92 and not escaped
        reader.fail('unterminated pickle payload')
    if key in _UNSUPPORTED or key.startswith(('BeginUndo', 'BeginRedo')):
        reader.fail(f'unsupported record {key}', SfdUnsupportedError)
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*:', key):
        reader.fail(f'unexpected token {key!r}')
    if key == 'ScriptLang:':
        start = reader.pos
        count = integer(reader.word())
        if count < 0 or count > reader.limits.max_bytes:
            reader.fail('invalid ScriptLang count')
        for _ in range(count):
            script_count = integer(reader.word())
            if script_count < 0 or script_count > reader.limits.max_bytes:
                reader.fail('invalid script count')
            for _ in range(script_count):
                reader.word()
                language_count = integer(reader.word())
                if language_count < 0 or language_count > reader.limits.max_bytes:
                    reader.fail('invalid language count')
                for _ in range(language_count):
                    if not reader.word():
                        reader.fail('truncated script language list')
        return SfdRecord(key, reader.data[start : reader.pos].strip())
    value = reader.line()
    if key in _MULTILINE:
        end = _MULTILINE[key]
        lines = [value]
        while True:
            if reader.pos == len(reader.data):
                reader.fail(f'unterminated {key}')
            line = reader.line()
            lines.append(line)
            if line == end.encode():
                break
        value = b'\n'.join(lines)
    return SfdRecord(key, value)


def spline_set(reader: Reader, *, legacy: bool = False) -> list[SfdContour]:
    contours: list[SfdContour] = []
    while True:
        saved = reader.pos
        key = reader.word()
        if key == 'EndSplineSet':
            return contours
        if not key:
            reader.fail('unterminated spline set')
        if key in _UNSUPPORTED:
            reader.fail(f'unsupported contour record {key}', SfdUnsupportedError)
        reader.pos = saved
        fields = reader.line().split()
        if not fields:
            continue
        try:
            command_index = next(i for i, value in enumerate(fields) if value in (b'm', b'l', b'c'))
        except StopIteration:
            reader.fail('expected m, l or c spline command')
        command = fields[command_index].decode()
        if command_index != (6 if command == 'c' else 2) or len(fields) != command_index + 2:
            reader.fail('invalid spline operation')
        coords = [real(value) for value in fields[:command_index]]
        flag = fields[-1]
        match = re.fullmatch(rb'(\d+)(?:x([0-9a-fA-F]+)|,(-?\d*)?(?:,(-?\d+))?)?', flag)
        if match is None:
            reader.fail('invalid point flags')
        flags, mask, ttf, cp = match.groups()
        if mask and len(mask) % 2:
            reader.fail('odd-length hint mask')
        point = SfdPoint(
            coords[-2],
            coords[-1],
            command,
            tuple(coords[:-2]),
            int(flags),
            bytes.fromhex(mask.decode()) if mask else None,
            integer(ttf) if ttf else None,
            integer(cp) if cp else None,
        )
        if command == 'm':
            contours.append(SfdContour())
        if not contours:
            reader.fail('spline must begin with m')
        contours[-1].points.append(point)
        reader.point_count += 1
        if reader.point_count > reader.limits.max_points:
            reader.fail('max_points exceeded', SfdLimitError)


def reference(reader: Reader, encoded: bool) -> SfdReference:
    parts = reader.line().split()
    if len(parts) >= 2 and parts[1] in (b'N', b'S'):
        parts.insert(1, b'-1')
    if len(parts) < 9:
        reader.fail('incomplete glyph reference')
    target, unicode = integer(parts[0]), integer(parts[1])
    if parts[2] not in (b'N', b'S'):
        reader.fail('invalid reference selection flag')
    transform = tuple(real(value) for value in parts[3:9])
    flags = integer(parts[9]) if len(parts) > 9 else 0
    point_match = None
    outdated = False
    expected = 10 if len(parts) > 9 else 9
    if flags & 4:
        if len(parts) < 12:
            reader.fail('missing reference point match')
        point_match = (integer(parts[10]), integer(parts[11]))
        expected = 12
        if len(parts) == 13 and parts[12] == b'O':
            outdated = True
            expected = 13
    if len(parts) != expected:
        reader.fail('unexpected reference parameters')
    return SfdReference(target, unicode, parts[2] == b'S', transform, flags, point_match, outdated, encoded)


def glyph(reader: Reader, font: SfdFont) -> SfdGlyph:
    name = string(reader.line())
    if not name:
        reader.fail('empty glyph name')
    result = SfdGlyph(name=name, glyph_id=reader.next_gid)
    current: SfdLayer | None = None
    seen = set()
    while True:
        key = reader.word()
        if key == 'EndChar':
            if 'Encoding:' not in seen or 'Width:' not in seen:
                reader.fail(f'missing Encoding or Width in glyph {name!r}')
            return result
        if not key:
            reader.fail(f'unterminated glyph {name!r}')
        if key in ('Encoding:', 'Width:', 'VWidth:', 'LayerCount:'):
            if key in seen:
                reader.fail(f'duplicate {key} in glyph {name!r}')
            seen.add(key)
            values = [integer(value) for value in reader.line().split()]
            if key == 'Encoding:':
                if len(values) not in (2, 3):
                    reader.fail('Encoding requires two or three integers')
                result.encoding, result.unicode = values[:2]
                if len(values) == 3 and values[2] != 65535:
                    result.glyph_id = values[2]
                reader.next_gid = max(reader.next_gid, result.glyph_id + 1)
            elif len(values) != 1:
                reader.fail(f'{key} requires one integer')
            elif key == 'Width:':
                result.width = values[0]
            elif key == 'VWidth:':
                result.vertical_width = values[0]
            elif values[0] != len(font.layer_infos):
                reader.fail('glyph LayerCount differs from font')
        elif key in ('AltUni:', 'AltUni2:'):
            for item in reader.line().split():
                if key == 'AltUni:':
                    result.alternate_unicodes.append(SfdAlternateUnicode(integer(item)))
                else:
                    if not re.fullmatch(rb'[0-9a-fA-F]+\.[0-9a-fA-F]+\.[0-9a-fA-F]+', item):
                        reader.fail('invalid AltUni2 entry')
                    uni, vs, fid = (int(part, 16) for part in item.split(b'.'))
                    result.alternate_unicodes.append(SfdAlternateUnicode(uni, -1 if vs == 0xFFFFFFFF else vs, fid))
        elif key in ('Fore', 'Back', 'Layer:'):
            index = {'Fore': 1, 'Back': 0}.get(key)
            if index is None:
                index = integer(reader.line())
            current = next((layer for layer in result.layers if layer.index == index), None)
            if current is None:
                current = SfdLayer(index)
                result.layers.append(current)
        elif key == 'SplineSet' or (font.version in ('1.0', '2.0') and re.fullmatch(r'[-+\d.]+', key)):
            if current is None:
                current = SfdLayer()
                result.layers.append(current)
            if key != 'SplineSet':
                reader.pos -= len(key)
            current.contours.extend(spline_set(reader))
        elif key in ('Image:', 'Image2:', 'TtfInstrs:'):
            from sfdfont._binary import payload

            item = payload(reader, key)
            if key.startswith('Image'):
                if current is None:
                    current = SfdLayer()
                    result.layers.append(current)
                current.images.append(item)
            else:
                result.payloads.append(item)
        elif key in ('Refer:', 'Ref:'):
            if current is None:
                current = SfdLayer()
                result.layers.append(current)
            current.references.append(reference(reader, key == 'Ref:'))
        else:
            (current.records if current is not None else result.records).append(record(reader, key))


def parse_font(stream: bytes | bytearray | BinaryIO, limits: SfdReadLimits | None) -> SfdFont:
    reader = Reader(stream, limits)
    reader.point_count = 0
    reader.next_gid = 0
    try:
        font = _parse_font(reader)
        try:
            font.validate()
        except SfdValidationError as error:
            reader.fail(str(error))
        font._snapshot = font.deepcopy()
        return font
    except SfdParseError as error:
        if error.offset is not None:
            raise
        reader.fail(str(error), type(error))
    raise AssertionError


def _parse_font(reader: Reader) -> SfdFont:
    if reader.word() != 'SplineFontDB:':
        reader.fail('not a FontForge SFD file')
    version = decode_text(reader.line())
    if version not in ('1.0', '2.0', '3.0', '3.1', '3.2'):
        reader.fail(f'unsupported SFD version {version!r}', SfdUnsupportedError)
    font = SfdFont(version=version)
    declared_layers = 2
    explicit_layers = False
    seen_chars = False
    while True:
        key = reader.word()
        if key == 'EndSplineFont':
            if not seen_chars:
                reader.fail('missing BeginChars')
            reader.whitespace()
            if reader.pos != len(reader.data):
                reader.fail('unexpected content after EndSplineFont')
            if len(font.layer_infos) != declared_layers:
                reader.fail('LayerCount differs from layer definitions')
            return font
        if not key:
            reader.fail('missing EndSplineFont')
        if key == 'BeginChars:':
            if seen_chars:
                reader.fail('duplicate BeginChars')
            seen_chars = True
            fields = reader.line().split()
            if len(fields) != 2:
                reader.fail('BeginChars requires two integers')
            font.encoding_size, count = (integer(value) for value in fields)
            if min(font.encoding_size, count) < 0:
                reader.fail('negative BeginChars count')
            if version != '1.0' and count > reader.limits.max_glyphs:
                reader.fail('max_glyphs exceeded', SfdLimitError)
            while True:
                key = reader.word()
                if key == 'EndChars':
                    break
                if key != 'StartChar:':
                    reader.fail('expected StartChar or EndChars')
                if len(font.glyphs) >= reader.limits.max_glyphs:
                    reader.fail('max_glyphs exceeded', SfdLimitError)
                font.glyphs.append(glyph(reader, font))
            if version != '1.0' and len(font.glyphs) != count:
                reader.fail('BeginChars count differs from actual glyph count')
        elif key == 'BitmapFont:' and seen_chars:
            from sfdfont._bitmap import bitmap

            font.bitmap_strikes.append(bitmap(reader, font))
        elif seen_chars:
            reader.fail(f'unsupported post-glyph record {key}', SfdUnsupportedError)
        elif key == 'TtfTable:':
            from sfdfont._binary import payload

            font.payloads.append(payload(reader, key))
        elif key == 'GridOrder2:':
            value = integer(reader.line())
            if value not in (0, 1):
                reader.fail('invalid GridOrder2')
            font.grid_quadratic = bool(value)
        elif key == 'Grid':
            saved = reader.pos
            if reader.word() != 'SplineSet':
                reader.pos = saved
            font.guidelines.extend(spline_set(reader))
        elif key in ('Copyright:', 'Comments:'):
            value = decode_text(reader.escaped_line())
            setattr(font.metadata, 'copyright' if key == 'Copyright:' else 'comments', value)
        elif key in _TEXT_FIELDS:
            setattr(font.metadata, _TEXT_FIELDS[key], decode_text(reader.line()))
        elif key in ('UComments:', 'FontLog:'):
            setattr(font.metadata, 'comments' if key == 'UComments:' else 'font_log', string(reader.line()))
        elif key in ('Ascent:', 'Descent:'):
            setattr(font.metadata, key[:-1].lower(), integer(reader.line()))
        elif key == 'LangName:':
            fields = tokens(reader.line())
            if not fields:
                reader.fail('missing LangName language')
            font.metadata.language_names.append(SfdLanguageNames(integer(fields[0]), [string(v) for v in fields[1:]]))
        elif key == 'Order2:':
            value = integer(reader.line())
            if value not in (0, 1):
                reader.fail('invalid Order2')
            for info in font.layer_infos:
                info.quadratic = bool(value)
        elif key == 'LayerCount:':
            declared_layers = integer(reader.line())
            if declared_layers < 2:
                reader.fail('LayerCount must be at least two')
        elif key == 'Layer:':
            values = tokens(reader.line())
            if not 3 <= len(values) <= 5:
                reader.fail('invalid Layer definition')
            if not explicit_layers:
                font.layer_infos.clear()
                explicit_layers = True
            order = integer(values[1])
            background = integer(values[3]) if len(values) >= 4 else integer(values[0]) == 0
            if order not in (0, 1) or background not in (0, 1):
                reader.fail('invalid layer flag')
            font.layer_infos.append(
                SfdLayerInfo(
                    integer(values[0]),
                    bool(order),
                    string(values[2]),
                    bool(background),
                    string(values[4]) if len(values) == 5 else None,
                )
            )
        else:
            font.metadata.records.append(record(reader, key))
