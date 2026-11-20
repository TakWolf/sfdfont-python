from __future__ import annotations

import math
import re
from typing import BinaryIO

from sfdfont._layout import (
    AAT_KEYS,
    CONTEXT_KEYS,
    KERN_CLASS_KEYS,
    context_record,
    kern_class_record,
    lookup_record,
    table_order_record,
)
from sfdfont._math import GLYPH_MATH_KEYS, math_constant
from sfdfont._reader import Reader
from sfdfont._strings import decode_text, decode_utf7
from sfdfont.error import SfdLimitError, SfdParseError, SfdUnsupportedError, SfdValidationError
from sfdfont.font import SfdFont
from sfdfont.glyph import SfdAlternateUnicode, SfdGlyph
from sfdfont.layer import SfdLayer, SfdLayerInfo
from sfdfont.limits import SfdReadLimits
from sfdfont.metadata import SfdLanguageNames
from sfdfont.outline import SfdContour, SfdPoint, SfdSpiroPoint
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
    'TtInstrs:': 'EndTTInstrs',
    'TtTable:': 'EndTTInstrs',
}
_UNSUPPORTED = {
    'BeginSubFonts:',
    'Registry:',
    'Ordering:',
    'Supplement:',
    'CIDVersion:',
    'BeginMMFonts:',
    'MMCounts:',
    'BaseScript:',
    'JstfExtender:',
    'JstfLang:',
    'JstfPrio:',
    'JstfEnableShrink:',
    'JstfDisableShrink:',
    'JstfMaxShrink:',
    'JstfEnableExtend:',
    'JstfDisableExtend:',
    'JstfMaxExtend:',
    'MacSetting:',
    'MacName:',
    'MMAxis:',
    'MMPositions:',
    'MMWeights:',
    'MMAxisMap:',
    'MMNamedInstance:',
    'MMCDV:',
    'MMNDV:',
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
    from sfdfont._encoding import REMAP_KEYS, remap_record
    from sfdfont._font_info import INFO_KEYS, info_record

    if key in REMAP_KEYS:
        return remap_record(reader, key)
    if key == 'ScriptLang:':
        from sfdfont._script_languages import script_languages_record

        return script_languages_record(reader, key)
    if key in INFO_KEYS:
        return info_record(reader, key)
    if key in ('Group:', 'GroupKern:', 'GroupVKern:'):
        from sfdfont._groups import group_record

        return group_record(reader, key)
    if key == 'TeX:':
        from sfdfont._tex import tex_record

        return tex_record(reader, key)
    if key in ('HStem:', 'VStem:', 'DStem:', 'DStem2:', 'CounterMasks:', 'MinimumDistance:'):
        from sfdfont._hints import hint_record

        return hint_record(reader, key)
    if key in ('MarkAttachClasses:', 'MarkAttachSets:'):
        from sfdfont._marks import mark_record

        return mark_record(reader, key)
    from sfdfont._glyph_layout import GLYPH_LAYOUT_KEYS, ROOT_LAYOUT_KEYS, layout_record
    from sfdfont._legacy_layout import LEGACY_KEYS, legacy_record

    if key in LEGACY_KEYS:
        return legacy_record(reader, key)

    if key in GLYPH_LAYOUT_KEYS | ROOT_LAYOUT_KEYS:
        return layout_record(reader, key)
    if key in ('BeginPrivate:', 'ShortTable:'):
        from sfdfont._tables import private_record, short_table_record

        return private_record(reader, key) if key == 'BeginPrivate:' else short_table_record(reader, key)
    if key == 'UndoRedoHistory':
        from sfdfont._history import history_record

        return history_record(reader, key)
    if key in AAT_KEYS:
        from sfdfont._aat import machine_record

        return machine_record(reader, key)
    if key in GLYPH_MATH_KEYS or math_constant(key):
        from sfdfont._math import math_record

        return math_record(reader, key)
    if key in ('BaseHoriz:', 'BaseVert:', 'Justify:', 'MacFeat:'):
        from sfdfont._extended import base_record, justify_record, mac_features_record

        if key == 'Justify:':
            return justify_record(reader, key)
        if key == 'MacFeat:':
            return mac_features_record(reader, key)
        return base_record(reader, key)
    if key in CONTEXT_KEYS:
        return context_record(reader, key)
    if key == 'TableOrder:':
        return table_order_record(reader, key)
    if key in KERN_CLASS_KEYS:
        return kern_class_record(reader, key)
    if key == 'Lookup:':
        return lookup_record(reader, key)
    if key in (
        'StartChar:',
        'BeginChars:',
        'BitmapFont:',
        'BDFChar:',
        'BDFRefChar:',
        'DupEnc:',
        'BeginSubrs:',
        'OrigType1:',
        'TtfInstrs:',
        'TtfTable:',
        'FillGradient:',
        'StrokeGradient:',
        'FillPattern:',
        'StrokePattern:',
    ):
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
    start = reader.pos
    value = reader.line()
    if key in _MULTILINE:
        end = _MULTILINE[key]
        while True:
            if reader.pos == len(reader.data):
                reader.fail(f'unterminated {key}')
            line = reader.line()
            if line == end.encode():
                break
        value = reader.data[start : reader.pos].strip()
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
        if key in ('Named:', 'NamedP:', 'PathFlags:', 'PathStart:', 'Spiro'):
            if not contours or not contours[-1].points:
                reader.fail('contour attributes require a preceding point')
            contour = contours[-1]
            if key == 'Named:':
                contour.name = string(reader.line())
            elif key == 'NamedP:':
                contour.points[-1].name = string(reader.line())
            elif key == 'PathFlags:':
                contour.flags = integer(reader.line())
            elif key == 'PathStart:':
                contour.start_offset = integer(reader.line())
            else:
                while True:
                    row = reader.line().split()
                    if row == [b'EndSpiro']:
                        break
                    if not row and reader.pos < len(reader.data):
                        continue
                    if len(row) != 3 or row[2] not in (b'{', b'}', b'v', b'o', b'c', b'[', b']', b'z', b'a', b'h'):
                        reader.fail('invalid or unterminated Spiro data')
                    contour.spiro.append(SfdSpiroPoint(real(row[0]), real(row[1]), row[2].decode()))
                    reader.point_count += 1
                    if reader.point_count > reader.limits.max_points:
                        reader.fail('max_points exceeded', SfdLimitError)
            continue
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
        if mask and len(mask) > 24:
            reader.fail('hint mask exceeds 96 bits')
        point = SfdPoint(
            coords[-2],
            coords[-1],
            command,
            tuple(coords[:-2]),
            integer(flags),
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


def glyph(reader: Reader, font: SfdFont, *, cid_child: bool = False) -> SfdGlyph:
    name = string(reader.line())
    if not name:
        reader.fail('empty glyph name')
    result = SfdGlyph(name=name, glyph_id=reader.next_gid, flags='')
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
                elif len(values) == 2 and cid_child:
                    result.glyph_id = result.encoding
                reader.next_gid = max(reader.next_gid, result.glyph_id + 1)
            elif len(values) != 1:
                reader.fail(f'{key} requires one integer')
            elif key == 'Width:':
                result.width = values[0]
            elif key == 'VWidth:':
                result.vertical_width = values[0]
            elif font.multilayer:
                result.layer_count = values[0]
            elif values[0] != len(font.layer_infos):
                reader.fail('glyph LayerCount differs from font')
        elif key == 'UndoRedoHistory':
            from sfdfont._history import history_layer

            item = record(reader, key)
            index = history_layer(item)
            layer = next((v for v in result.layers if v.index == index), None)
            if layer is None:
                layer = SfdLayer(index)
                result.layers.append(layer)
            layer.records.append(item)
        elif key == 'Flags:':
            if key in seen:
                reader.fail('duplicate glyph Flags')
            seen.add(key)
            result.flags = decode_text(reader.line())
        elif key in ('AltUni:', 'AltUni2:'):
            for item in reader.line().split():
                if key == 'AltUni:':
                    result.alternate_unicodes.append(SfdAlternateUnicode(integer(item)))
                else:
                    if not re.fullmatch(rb'[0-9a-fA-F]{1,16}\.[0-9a-fA-F]{1,16}\.[0-9a-fA-F]{1,16}', item):
                        reader.fail('invalid AltUni2 entry')
                    uni, vs, fid = (int(part, 16) for part in item.split(b'.'))
                    result.alternate_unicodes.append(SfdAlternateUnicode(uni, -1 if vs == 0xFFFFFFFF else vs, fid))
        elif key in ('Fore', 'Back', 'Layer:'):
            index = {'Fore': 1, 'Back': 0}.get(key)
            paint = None
            if index is None:
                if font.multilayer:
                    from sfdfont._paint import decode_paint

                    index, paint = decode_paint(reader.line())
                else:
                    index = integer(reader.line())
            current = next((layer for layer in result.layers if layer.index == index), None)
            if current is None:
                current = SfdLayer(index)
                result.layers.append(current)
            if paint is not None:
                current.paint = paint
        elif key in ('FillGradient:', 'StrokeGradient:', 'FillPattern:', 'StrokePattern:'):
            from sfdfont._paint import decode_gradient, decode_pattern

            if not font.multilayer or current is None or current.paint is None:
                reader.fail('brush records require a Type 3 foreground layer')
            prefix = 'fill' if key.startswith('Fill') else 'stroke'
            if (
                getattr(current.paint, prefix + '_gradient') is not None
                or getattr(current.paint, prefix + '_pattern') is not None
            ):
                reader.fail('duplicate layer brush')
            gradient = key.endswith('Gradient:')
            value = decode_gradient(reader.line()) if gradient else decode_pattern(reader.line())
            setattr(current.paint, prefix + ('_gradient' if gradient else '_pattern'), value)
        elif key == 'SplineSet' or (font.version in ('1.0', '2.0') and re.fullmatch(r'[-+\d.]+', key)):
            if current is None:
                current = SfdLayer()
                result.layers.append(current)
            if key != 'SplineSet':
                reader.pos -= len(key)
            current.contours.extend(spline_set(reader))
        elif key in ('Image:', 'Image2:', 'TtfInstrs:', 'OrigType1:'):
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
    try:
        font = _parse_font(reader)
        reader.whitespace()
        if reader.pos != len(reader.data):
            reader.fail('unexpected content after font')
        try:
            font.validate()
        except SfdValidationError as error:
            reader.fail(str(error))
        from sfdfont._family import snapshot_family

        snapshot_family(font)
        return font
    except SfdParseError as error:
        if error.offset is not None:
            raise
        reader.fail(str(error), type(error))
    raise AssertionError


def _parse_font(reader: Reader, version: str | None = None, *, cid_child: bool = False) -> SfdFont:
    nested = version is not None
    if not nested:
        if reader.word() != 'SplineFontDB:':
            reader.fail('not a FontForge SFD file')
        version = decode_text(reader.line())
    if version not in ('1.0', '2.0', '3.0', '3.1', '3.2'):
        reader.fail(f'unsupported SFD version {version!r}', SfdUnsupportedError)
    font = SfdFont(version=version)
    reader.next_gid = 0
    declared_layers = 2
    explicit_layers = False
    seen_chars = False
    pending_style_names = []
    while True:
        key = reader.word()
        if key == ('EndSubSplineFont' if cid_child else 'EndSplineFont'):
            if not seen_chars:
                reader.fail('missing BeginChars')
            if len(font.layer_infos) != declared_layers:
                reader.fail('LayerCount differs from layer definitions')
            if pending_style_names:
                from sfdfont._legacy_names import restore_pending_names

                font.metadata.records[:] = restore_pending_names(font.metadata.records, pending_style_names)
            return font
        if not key:
            reader.fail('missing EndSplineFont')
        if key == 'MMCounts:' and not nested:
            from sfdfont._family import parse_mm

            if seen_chars or pending_style_names or font != SfdFont(version=version):
                reader.fail('MMCounts must precede font metadata')
            return parse_mm(reader, version)
        if key == 'BeginSubFonts:' and not cid_child:
            if seen_chars:
                reader.fail('duplicate font body')
            fields = reader.line().split()
            if len(fields) != 2:
                reader.fail('BeginSubFonts requires two integers')
            count, font.encoding_size = (integer(v) for v in fields)
            if count < 1 or font.encoding_size < 0:
                reader.fail('invalid BeginSubFonts count')
            if count > reader.limits.max_bytes:
                reader.fail('subfont count exceeds document budget', SfdLimitError)
            font.subfonts = [_parse_font(reader, version, cid_child=True) for _ in range(count)]
            if reader.word() != 'EndSubFonts':
                reader.fail('missing EndSubFonts')
            seen_chars = True
        elif key == 'BeginChars:':
            if seen_chars:
                reader.fail('duplicate BeginChars')
            seen_chars = True
            fields = reader.line().split()
            if len(fields) != 2:
                reader.fail('BeginChars requires two integers')
            font.encoding_size, count = (integer(value) for value in fields)
            if font.encoding_size < 0 or count < (-1 if cid_child else 0):
                reader.fail('negative BeginChars count')
            if version != '1.0' and count > reader.limits.max_glyphs:
                reader.fail('max_glyphs exceeded', SfdLimitError)
            while True:
                key = reader.word()
                if key == 'EndChars':
                    break
                if key != 'StartChar:':
                    reader.fail('expected StartChar or EndChars')
                if reader.glyph_count >= reader.limits.max_glyphs:
                    reader.fail('max_glyphs exceeded', SfdLimitError)
                font.glyphs.append(glyph(reader, font, cid_child=cid_child))
                reader.glyph_count += 1
            if version != '1.0' and count != -1 and len(font.glyphs) != count:
                reader.fail('BeginChars count differs from actual glyph count')
        elif key == 'BitmapFont:' and seen_chars:
            from sfdfont._bitmap import bitmap

            font.bitmap_strikes.append(bitmap(reader, font))
        elif key == 'DupEnc:' and seen_chars:
            values = reader.line().split()
            if len(values) != 2:
                reader.fail('DupEnc requires an encoding slot and glyph ID')
            encoding, target = (integer(value) for value in values)
            if encoding in font.encoding_aliases:
                reader.fail(f'duplicate DupEnc slot {encoding}')
            font.encoding_aliases[encoding] = target
        elif seen_chars:
            reader.fail(f'unsupported post-glyph record {key}', SfdUnsupportedError)
        elif key in ('TtfTable:', 'BeginSubrs:'):
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
        elif key in ('MultiLayer:', 'Multilayer:'):
            value = integer(reader.line())
            if value not in (0, 1):
                reader.fail('invalid MultiLayer flag')
            font.multilayer = bool(value)
        elif key in ('Registry:', 'Ordering:', 'Supplement:', 'CIDVersion:') and not cid_child:
            from sfdfont.cid import SfdCidInfo

            if font.cid is None:
                font.cid = SfdCidInfo()
            field = {
                'Registry:': 'registry',
                'Ordering:': 'ordering',
                'Supplement:': 'supplement',
                'CIDVersion:': 'version',
            }
            data = reader.line()
            value = integer(data) if key == 'Supplement:' else real(data) if key == 'CIDVersion:' else decode_text(data)
            setattr(font.cid, field[key], value)
        elif key in _TEXT_FIELDS:
            setattr(font.metadata, _TEXT_FIELDS[key], decode_text(reader.line()))
        elif key in ('UComments:', 'FontLog:'):
            setattr(font.metadata, 'comments' if key == 'UComments:' else 'font_log', string(reader.line()))
        elif key in ('Ascent:', 'Descent:'):
            setattr(font.metadata, key[:-1].lower(), integer(reader.line()))
        elif key == 'StyleMapFamilyName:':
            pending_style_names.append((len(font.metadata.records), record(reader, key)))
        elif key == 'LangName:':
            from sfdfont._legacy_names import decode_style_map_name

            fields = tokens(reader.line())
            if not fields:
                reader.fail('missing LangName language')
            font.metadata.language_names.append(
                SfdLanguageNames(
                    integer(fields[0]),
                    [string(v) for v in fields[1:]],
                    [decode_style_map_name(item) for _, item in pending_style_names],
                )
            )
            pending_style_names.clear()
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
