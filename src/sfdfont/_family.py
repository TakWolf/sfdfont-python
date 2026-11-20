import math
import re

from sfdfont._reader import Reader
from sfdfont.error import SfdLimitError
from sfdfont.variation import SfdAxisMap, SfdMacName, SfdMultipleMaster, SfdNamedInstance


def snapshot_family(font) -> None:
    for subfont in font.subfonts:
        snapshot_family(subfont)
    if font.multiple_master is not None:
        for instance in font.multiple_master.instances:
            snapshot_family(instance)
    font._snapshot = font.deepcopy()


def mac_name(value: bytes) -> SfdMacName:
    from sfdfont._parser import integer
    from sfdfont.error import SfdParseError

    match = re.fullmatch(rb'([0-9]+)\s+([0-9]+)\s+([0-9]+)\s+"((?:[^"\\]|\\[0-7]{3})*)"', value)
    if match is None:
        raise SfdParseError('invalid MacName')
    try:
        data = re.sub(rb'\\([0-7]{3})', lambda m: bytes([int(m[1], 8)]), match[4])
    except ValueError as error:
        raise SfdParseError('MacName escape exceeds one byte') from error
    if len(data) != integer(match[3]):
        raise SfdParseError('MacName length mismatch')
    encoding, language = integer(match[1]), integer(match[2])
    if not 0 <= encoding <= 65535 or not 0 <= language <= 65535 or b'\0' in data:
        raise SfdParseError('invalid MacName encoding, language or NUL byte')
    return SfdMacName(encoding, language, data)


def encode_mac_name(item) -> bytes:
    from sfdfont._validation import check, number

    number(item.encoding, 'Mac name encoding', 0, 65535)
    number(item.language, 'Mac name language', 0, 65535)
    check(isinstance(item.data, bytes) and b'\0' not in item.data, 'invalid Mac name bytes')
    escaped = b''.join(bytes([v]) if 32 <= v <= 126 and v not in (34, 92) else f'\\{v:03o}'.encode() for v in item.data)
    return f'{item.encoding} {item.language} {len(item.data)} "'.encode() + escaped + b'"'


def parse_mm(reader: Reader, version: str):
    from sfdfont._parser import _parse_font, integer, real
    from sfdfont._strings import decode_text

    counts = [integer(value) for value in reader.line().split()]
    if len(counts) == 2:
        counts.extend((0, 0))
    if len(counts) != 4 or counts[0] < 1 or not 1 <= counts[1] <= 16 or counts[2] not in (0, 1) or counts[3] < 0:
        reader.fail('invalid MMCounts')
    instance_count, axis_count, apple, named_count = counts
    if instance_count + named_count > reader.limits.max_bytes:
        reader.fail('Multiple Master count exceeds document budget', SfdLimitError)
    mm = SfdMultipleMaster(apple=bool(apple))
    maps = {}
    named = {}
    seen = set()
    names = None
    while True:
        key = reader.word()
        if not key:
            reader.fail('missing BeginMMFonts')
        if key in ('MMAxis:', 'MMPositions:', 'MMWeights:', 'MMCDV:', 'MMNDV:'):
            if key in seen:
                reader.fail(f'duplicate {key}')
            seen.add(key)
        if key == 'MMAxis:':
            mm.axes = [decode_text(v) for v in reader.line().split()]
        elif key == 'MMPositions:':
            values = [real(v) for v in reader.line().split()]
            if len(values) != instance_count * axis_count:
                reader.fail('MMPositions count mismatch')
            mm.positions = [values[i : i + axis_count] for i in range(0, len(values), axis_count)]
        elif key == 'MMWeights:':
            mm.weights = [real(v) for v in reader.line().split()]
        elif key == 'MMAxisMap:':
            values = reader.line().split()
            if len(values) < 2:
                reader.fail('invalid MMAxisMap')
            index, count = integer(values[0]), integer(values[1])
            if not 0 <= index < axis_count or index in maps or count != len(values) - 2 or count < 0:
                reader.fail('MMAxisMap index or count mismatch')
            points = []
            for value in values[2:]:
                pair = value.split(b'=>')
                if len(pair) != 2:
                    reader.fail('invalid MMAxisMap coordinate pair')
                points.append((real(pair[0]), real(pair[1])))
            entry = maps[index] = SfdAxisMap(points)
            names = entry.names
        elif key == 'MMNamedInstance:':
            values = reader.line().split()
            if len(values) != axis_count + 1:
                reader.fail('MMNamedInstance coordinate count mismatch')
            index = integer(values[0])
            if not 0 <= index < named_count or index in named:
                reader.fail('invalid MMNamedInstance index')
            entry = named[index] = SfdNamedInstance([real(v) for v in values[1:]])
            names = entry.names
        elif key == 'MacName:':
            if names is None:
                reader.fail('MacName requires an axis map or named instance')
            names.append(mac_name(reader.line()))
        elif key in ('MMCDV:', 'MMNDV:'):
            if reader.line():
                reader.fail('MM subroutine must start on the next line')
            start = reader.pos
            while True:
                position = reader.pos
                line = reader.line()
                if line == b'EndMMSubroutine':
                    break
                if reader.pos == len(reader.data):
                    reader.fail('unterminated MM subroutine')
            data = reader.data[start:position].rstrip(b'\r\n')
            setattr(mm, 'cdv' if key == 'MMCDV:' else 'ndv', data)
        elif key == 'BeginMMFonts:':
            values = reader.line().split()
            if len(values) != 2 or integer(values[0]) != instance_count + 1 or integer(values[1]) < 0:
                reader.fail('BeginMMFonts count mismatch')
            if len(mm.axes) != axis_count or len(mm.weights) != instance_count or len(mm.positions) != instance_count:
                reader.fail('incomplete Multiple Master header')
            if len(maps) != axis_count or len(named) != named_count:
                reader.fail('missing axis maps or named instances')
            mm.axis_maps = [maps[i] for i in range(axis_count)]
            mm.named_instances = [named[i] for i in range(named_count)]
            mm.instances = [_parse_font(reader, version) for _ in range(instance_count)]
            font = _parse_font(reader, version)
            if reader.word() != 'EndMMFonts':
                reader.fail('missing EndMMFonts')
            font.multiple_master = mm
            return font
        else:
            reader.fail(f'unexpected Multiple Master record {key!r}')


def validate_mm(font) -> None:
    from sfdfont._validation import check, number, validate

    mm = font.multiple_master
    check(not font.subfonts and font.cid is None, 'cannot combine CID and Multiple Master containers')
    axes = len(mm.axes)
    check(1 <= axes <= 16 and len(set(mm.axes)) == axes, 'invalid Multiple Master axes')
    for axis in mm.axes:
        check(isinstance(axis, str) and bool(re.fullmatch(r'[^\s\x00]+', axis)), 'invalid MM axis name')
    check(bool(mm.instances), 'Multiple Master requires instances')
    check(isinstance(mm.apple, bool), 'invalid MM apple flag')
    check(len(mm.positions) == len(mm.weights) == len(mm.instances), 'MM instance count mismatch')
    for position in mm.positions:
        check(len(position) == axes and all(math.isfinite(v) for v in position), 'invalid MM position')
    check(all(math.isfinite(v) for v in mm.weights), 'invalid MM weights')
    check(len(mm.axis_maps) == axes, 'MM axis map count mismatch')
    for mapping in mm.axis_maps:
        check(all(len(v) == 2 and all(math.isfinite(c) for c in v) for v in mapping.points), 'invalid MM axis map')
        check(
            all(a[0] < b[0] for a, b in zip(mapping.points, mapping.points[1:], strict=False)), 'MM map must be ordered'
        )
    check(mm.apple or not mm.named_instances, 'named instances require Apple variation mode')
    for named in mm.named_instances:
        check(
            len(named.coordinates) == axes and all(math.isfinite(v) for v in named.coordinates),
            'invalid named position',
        )
    for entry in [*mm.axis_maps, *mm.named_instances]:
        for name in entry.names:
            number(name.encoding, 'Mac name encoding', 0, 65535)
            number(name.language, 'Mac name language', 0, 65535)
            check(isinstance(name.data, bytes) and b'\0' not in name.data, 'invalid Mac name bytes')
    for data in (mm.cdv, mm.ndv):
        if data is not None:
            check(isinstance(data, bytes) and b'\0' not in data, 'invalid MM subroutine')
            check(
                not any(v.strip() == b'EndMMSubroutine' for v in data.splitlines()), 'MM subroutine contains terminator'
            )
    for instance in mm.instances:
        check(instance is not font and instance.multiple_master is None, 'nested or cyclic Multiple Master family')
        check(instance.version == font.version, 'MM instance version mismatch')
        check(not instance.subfonts and instance.cid is None, 'CID instance in Multiple Master family')
        validate(instance)


def validate_cid(font) -> None:
    from sfdfont._extended import EXTENDED_KEYS
    from sfdfont._layout import LAYOUT_KEYS
    from sfdfont._validation import check, number, validate

    check(font.cid is not None and bool(font.subfonts), 'CID metadata requires subfonts')
    check(not font.glyphs and not font.encoding_aliases, 'CID container cannot contain ordinary glyphs or aliases')
    check(font.multiple_master is None, 'cannot combine CID and Multiple Master containers')
    for value in (font.cid.registry, font.cid.ordering):
        check(isinstance(value, str) and bool(re.fullmatch(r'[^\s\x00]+', value)), 'invalid CID registry/ordering')
    number(font.cid.supplement, 'CID supplement', 0)
    check(math.isfinite(font.cid.version) and font.cid.version >= 0, 'invalid CID version')
    names = set()
    for subfont in font.subfonts:
        check(subfont is not font and not subfont.subfonts and subfont.cid is None, 'nested or cyclic CID font')
        check(subfont.multiple_master is None, 'Multiple Master child in CID family')
        check(subfont.version == font.version, 'CID subfont version mismatch')
        check(subfont.metadata.font_name not in names, 'duplicate CID subfont name')
        names.add(subfont.metadata.font_name)
        check(not subfont.bitmap_strikes, 'CID bitmap strikes must be stored in the container')
        check(
            not any(r.keyword in LAYOUT_KEYS | EXTENDED_KEYS for r in subfont.metadata.records),
            'CID layout belongs in the container',
        )
        check(all(g.glyph_id < font.encoding_size for g in subfont.glyphs), 'CID glyph exceeds container capacity')
        validate(subfont, layout=False)


def dump_mm(font) -> bytes:
    from sfdfont._writer import _dump_body, plain, scalar

    mm = font.multiple_master
    result = []

    def line(key, values):
        result.append(key.encode() + b' ' + values + b'\n')

    line('MMCounts:', f'{len(mm.instances)} {len(mm.axes)} {int(mm.apple)} {len(mm.named_instances)}'.encode())
    line('MMAxis:', b' '.join(plain(v) for v in mm.axes))
    line('MMPositions:', b' '.join(scalar(v) for pos in mm.positions for v in pos))
    line('MMWeights:', b' '.join(scalar(v) for v in mm.weights))

    def names(items):
        for item in items:
            line('MacName:', encode_mac_name(item))

    for index, mapping in enumerate(mm.axis_maps):
        line(
            'MMAxisMap:',
            f'{index} {len(mapping.points)}'.encode()
            + b''.join(b' ' + scalar(a) + b'=>' + scalar(b) for a, b in mapping.points),
        )
        names(mapping.names)
    for key, data in [('MMCDV:', mm.cdv), ('MMNDV:', mm.ndv)]:
        if data is not None:
            result.extend([key.encode() + b'\n', data, b'\nEndMMSubroutine\n'])
    for index, named in enumerate(mm.named_instances):
        line('MMNamedInstance:', str(index).encode() + b' ' + b' '.join(scalar(v) for v in named.coordinates))
        names(named.names)
    capacity = max((glyph.glyph_id for instance in mm.instances for glyph in instance.glyphs), default=-1) + 1
    line('BeginMMFonts:', f'{len(mm.instances) + 1} {capacity}'.encode())
    for instance in [*mm.instances, font]:
        result.append(_dump_body(instance))
    result.append(b'EndMMFonts\n')
    return b''.join(result)
