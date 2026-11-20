from __future__ import annotations

import re

from sfdfont._binary import payload
from sfdfont._parser import record
from sfdfont._preservation import check_preservation
from sfdfont._reader import Reader, encode_ascii85
from sfdfont._strings import quote
from sfdfont.error import SfdParseError, SfdValidationError


def plain(value: str) -> bytes:
    if any(char in value for char in '\r\n\0'):
        raise SfdValidationError('plain SFD field contains a line break or NUL')
    try:
        return value.encode('utf-8')
    except UnicodeEncodeError as error:
        raise SfdValidationError('unpaired surrogate in plain field') from error


def scalar(value: float) -> bytes:
    return format(value, '.17g').encode('ascii')


def records(items) -> bytes:
    result = []
    forbidden = {
        'SplineFontDB:',
        'Encoding:',
        'Width:',
        'VWidth:',
        'Layer:',
        'LayerCount:',
        'FontName:',
        'FullName:',
        'FamilyName:',
        'Copyright:',
        'Weight:',
        'Version:',
        'Ascent:',
        'Descent:',
        'UComments:',
        'FontLog:',
        'LangName:',
        'Order2:',
        'DupEnc:',
        'MultiLayer:',
    }
    for item in items:
        if item.keyword in forbidden or not isinstance(item.value, bytes):
            raise SfdValidationError(f'reserved or invalid raw record {item.keyword!r}')
        encoded = plain(item.keyword) + b' ' + item.value + b'\n'
        reader = Reader(encoded)
        try:
            parsed = record(reader, reader.word())
            if reader.word() or parsed != item:
                raise SfdValidationError(f'raw record boundary mismatch: {item.keyword}')
        except SfdParseError as error:
            raise SfdValidationError(f'invalid raw record {item.keyword}: {error}') from error
        result.append(encoded)
    return b''.join(result)


def binary(item) -> bytes:
    if b'\n' in item.parameters or b'\r' in item.parameters or b'\0' in item.parameters:
        raise SfdValidationError('invalid binary header')
    data = plain(item.keyword) + b' ' + item.parameters + b'\n' + encode_ascii85(item.data)
    data += b'\n' + plain(item.terminator) + b'\n'
    try:
        reader = Reader(data)
        parsed = payload(reader, reader.word())
        if parsed != item or reader.word():
            raise SfdValidationError('binary payload length or terminator mismatch')
    except SfdParseError as error:
        raise SfdValidationError(f'invalid binary payload: {error}') from error
    return data


def splines(contours) -> bytes:
    if not contours:
        return b''
    result = [b'SplineSet\n']
    for contour in contours:
        for point in contour.points:
            values = [scalar(value) for value in (*point.controls, point.x, point.y)]
            flags = str(point.flags).encode()
            if point.hint_mask is not None:
                flags += b'x' + point.hint_mask.hex().encode()
            elif point.ttf_index is not None or point.next_cp_index is not None:
                flags += b',' + (str(point.ttf_index).encode() if point.ttf_index is not None else b'')
                if point.next_cp_index is not None:
                    flags += b',' + str(point.next_cp_index).encode()
            result.append(b' '.join([*values, point.command.encode(), flags]) + b'\n')
            if point.name is not None:
                result.append(b'NamedP: ' + quote(point.name) + b'\n')
        if contour.spiro:
            result.append(b'Spiro\n')
            for point in contour.spiro:
                result.append(b' '.join((scalar(point.x), scalar(point.y), point.kind.encode())) + b'\n')
            result.append(b'EndSpiro\n')
        if contour.name is not None:
            result.append(b'Named: ' + quote(contour.name) + b'\n')
        if contour.flags:
            result.append(f'PathFlags: {contour.flags}\n'.encode())
        if contour.start_offset:
            result.append(f'PathStart: {contour.start_offset}\n'.encode())
    return b''.join([*result, b'EndSplineSet\n'])


def dump_font(font) -> bytes:
    font.validate()
    if font.multiple_master is not None:
        from sfdfont._family import dump_mm

        body = dump_mm(font)
    else:
        body = _dump_body(font)
    return b'SplineFontDB: ' + font.version.encode() + b'\n' + body


def _dump_body(font) -> bytes:
    check_preservation(font)
    result: list[bytes] = []

    def line(key: str, value: bytes = b'') -> None:
        result.append(key.encode() + (b' ' + value if value else b'') + b'\n')

    meta = font.metadata
    if font.multilayer:
        line('MultiLayer:', b'1')
    if not re.fullmatch(r'[^\s\x00]+', meta.font_name):
        raise SfdValidationError('FontName must be a nonempty token')
    for key, value in [
        ('FontName:', meta.font_name),
        ('FullName:', meta.full_name),
        ('FamilyName:', meta.family_name),
        ('Weight:', meta.weight),
        ('Copyright:', meta.copyright),
        ('Version:', meta.version),
        ('Encoding:', meta.encoding),
    ]:
        if key == 'Copyright:':
            value = value.replace('\\', '\\\\').replace('\n', '\\n')
        line(key, plain(value))
    line('Ascent:', str(meta.ascent).encode())
    line('Descent:', str(meta.descent).encode())
    if meta.comments is not None:
        line('UComments:', quote(meta.comments))
    if meta.font_log is not None:
        line('FontLog:', quote(meta.font_log))
    for names in meta.language_names:
        line('LangName:', b' '.join([str(names.language).encode(), *(quote(name) for name in names.names)]))
    if font.version in ('1.0', '2.0'):
        if len(font.layer_infos) != 2 or len({info.quadratic for info in font.layer_infos}) != 1:
            raise SfdValidationError('old-format output requires two layers with the same curve order')
        line('Order2:', str(int(font.layer_infos[1].quadratic)).encode())
    else:
        line('LayerCount:', str(len(font.layer_infos)).encode())
        for info in font.layer_infos:
            value = b' '.join(
                [
                    str(info.index).encode(),
                    str(int(info.quadratic)).encode(),
                    quote(info.name),
                    str(int(info.background)).encode(),
                ]
            )
            if info.ufo_path is not None:
                value += b' ' + quote(info.ufo_path)
            line('Layer:', value)
    result.append(records(meta.records))
    for item in font.payloads:
        if item.keyword != 'TtfTable:':
            raise SfdValidationError('font-level payload must be TtfTable')
        result.append(binary(item))
    if font.guidelines:
        line('GridOrder2:', str(int(font.grid_quadratic)).encode())
        line('Grid')
        result.append(splines(font.guidelines))
    line('BeginChars:', f'{font.encoding_size} {len(font.glyphs)}'.encode())
    next_gid = 0
    for glyph in font.glyphs:
        if glyph.glyph_id == 65535 and next_gid != 65535:
            raise SfdValidationError('glyph ID 65535 is reserved for the next implicit ID in SFD')
        next_gid = max(next_gid, glyph.glyph_id + 1)
        line('StartChar:', quote(glyph.name))
        line('Encoding:', f'{glyph.encoding} {glyph.unicode} {glyph.glyph_id}'.encode())
        line('Width:', str(glyph.width).encode())
        if glyph.vertical_width is not None:
            line('VWidth:', str(glyph.vertical_width).encode())
        if glyph.alternate_unicodes:
            line(
                'AltUni2:',
                b' '.join(
                    f'{alt.unicode:06x}.{alt.variation_selector & 0xFFFFFFFF:06x}.{alt.font_id:x}'.encode()
                    for alt in glyph.alternate_unicodes
                ),
            )
        if font.multilayer:
            if glyph.layer_count is not None:
                line('LayerCount:', str(glyph.layer_count).encode())
        elif font.version not in ('1.0', '2.0'):
            line('LayerCount:', str(len(font.layer_infos)).encode())
        result.append(records(glyph.records))
        for item in glyph.payloads:
            if item.keyword != 'TtfInstrs:':
                raise SfdValidationError('glyph-level payload must be TtfInstrs')
            result.append(binary(item))
        for layer in glyph.layers:
            if font.multilayer and layer.index > 0:
                from sfdfont._paint import encode_paint

                line('Layer:', encode_paint(layer.index, layer.paint))
            else:
                line(
                    'Back' if layer.index == 0 else 'Fore' if layer.index == 1 else 'Layer:',
                    str(layer.index).encode() if layer.index > 1 else b'',
                )
            result.append(splines(layer.contours))
            for ref in layer.references:
                value = b' '.join(
                    [
                        str(ref.target).encode(),
                        str(ref.unicode).encode(),
                        b'S' if ref.selected else b'N',
                        *(scalar(v) for v in ref.transform),
                        str(ref.flags).encode(),
                    ]
                )
                if ref.point_match is not None:
                    value += f' {ref.point_match[0]} {ref.point_match[1]}'.encode()
                    if ref.point_match_outdated:
                        value += b' O'
                line('Ref:' if ref.encoded else 'Refer:', value)
            for item in layer.images:
                if item.keyword not in ('Image:', 'Image2:'):
                    raise SfdValidationError('layer image must be Image or Image2')
                if item.keyword == 'Image2:' and font.version != '3.2':
                    raise SfdValidationError('Image2 output requires SFD 3.2')
                result.append(binary(item))
            result.append(records(layer.records))
        line('EndChar')
    line('EndChars')
    for strike in font.bitmap_strikes:
        capacity = max((glyph.glyph_id for glyph in font.glyphs), default=-1) + 1
        value = f'{strike.pixelsize} {capacity} {strike.ascent} {strike.descent} {strike.depth}'.encode()
        if strike.foundry is not None:
            foundry = plain(strike.foundry)
            if not foundry or any(c in foundry for c in b' \t'):
                raise SfdValidationError('foundry must be a nonempty token')
            value += b' ' + foundry
        line('BitmapFont:', value)
        if strike.properties:
            line('BDFStartProperties:', str(len(strike.properties)).encode())
            for prop in strike.properties:
                if not re.fullmatch(r'[^\s\x00]+', prop.name):
                    raise SfdValidationError('invalid bitmap property name')
                if prop.type & ~0x10 in (0, 1) and isinstance(prop.value, str):
                    encoded = plain(prop.value)
                    if b'"' in encoded:
                        raise SfdValidationError('bitmap property contains a quote')
                    value = b'"' + encoded + b'"'
                elif prop.type & ~0x10 in (2, 3) and isinstance(prop.value, int):
                    value = str(prop.value).encode()
                else:
                    raise SfdValidationError('invalid bitmap property type or value')
                line(prop.name, str(prop.type).encode() + b' ' + value)
            line('BDFEndProperties')
        if strike.resolution is not None:
            line('Resolution:', str(strike.resolution).encode())
        for glyph in strike.glyphs:
            value = f'{glyph.glyph_id} {glyph.encoding} {glyph.advance} {glyph.xmin} {glyph.xmax} '
            value += f'{glyph.ymin} {glyph.ymax}'
            if glyph.vertical_advance is not None:
                value += f' {glyph.vertical_advance}'
            line('BDFChar:', value.encode())
            result.append(encode_ascii85(glyph.data) + b'\n')
        for ref in strike.references:
            line('BDFRefChar:', f'{ref.source} {ref.target} {ref.x} {ref.y} {"S" if ref.selected else "N"}'.encode())
        line('EndBitmapFont')
    for encoding, target in font.encoding_aliases.items():
        line('DupEnc:', f'{encoding} {target}'.encode())
    line('EndSplineFont')
    return b''.join(result)
