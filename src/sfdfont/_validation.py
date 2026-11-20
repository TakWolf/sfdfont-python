from __future__ import annotations

import math

from sfdfont._layout import LAYOUT_KEYS, version_matches
from sfdfont.error import SfdParseError, SfdValidationError


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SfdValidationError(message)


def number(value: int, name: str, minimum: int = -0x80000000, maximum: int = 0x7FFFFFFF) -> None:
    check(
        isinstance(value, int) and not isinstance(value, bool) and minimum <= value <= maximum,
        f'invalid {name}: {value!r}',
    )


def unicode_value(value: int, name: str, *, unassigned: bool = True) -> None:
    number(value, name, -1 if unassigned else 0, 0x10FFFF)
    check(not 0xD800 <= value <= 0xDFFF, f'surrogate in {name}')


def cycles(graph: dict, name: str) -> None:
    # Iterative DFS avoids exhausting Python's recursion limit on long chains.
    finished = set()
    for root in graph:
        if root in finished:
            continue
        active = {root}
        stack = [(root, iter(graph[root]))]
        while stack:
            node, children = stack[-1]
            child = next(children, None)
            if child is None:
                active.remove(node)
                finished.add(node)
                stack.pop()
            elif child in active:
                raise SfdValidationError(f'cyclic {name} reference at {child!r}')
            elif child not in finished:
                active.add(child)
                stack.append((child, iter(graph.get(child, ()))))


def contours(items) -> None:
    for contour in items:
        number(contour.flags, 'path flags', 0, 1)
        number(contour.start_offset, 'path start offset', 0)
        if contour.name is not None:
            check(isinstance(contour.name, str) and '\0' not in contour.name, 'invalid contour name')
        for index, point in enumerate(contour.spiro):
            check(math.isfinite(point.x) and math.isfinite(point.y), 'nonfinite Spiro coordinate')
            check(point.kind in ('{', '}', 'v', 'o', 'c', '[', ']', 'z', 'a', 'h'), 'invalid Spiro point kind')
            check(point.kind != 'z' or index == len(contour.spiro) - 1, 'Spiro end marker must be last')
            check(point.kind != '{' or index == 0, 'open Spiro marker must be first')
        check(not contour.spiro or contour.spiro[-1].kind == 'z', 'Spiro data requires an end marker')
        check(bool(contour.points) and contour.points[0].command == 'm', 'contour must begin with m')
        for index, point in enumerate(contour.points):
            if point.name is not None:
                check(isinstance(point.name, str) and '\0' not in point.name, 'invalid point name')
            check(point.command in ('m', 'l', 'c') and (point.command != 'm' or index == 0), 'invalid contour command')
            check(len(point.controls) == (4 if point.command == 'c' else 0), 'invalid control coordinates')
            check(
                all(isinstance(v, (int, float)) and math.isfinite(v) for v in (point.x, point.y, *point.controls)),
                'nonfinite point coordinate',
            )
            number(point.flags, 'point flags', 0, 0xFFFFFFFF)
            if point.hint_mask is not None:
                check(isinstance(point.hint_mask, bytes) and 1 <= len(point.hint_mask) <= 12, 'invalid hint mask')
            for value in (point.ttf_index, point.next_cp_index):
                if value is not None:
                    number(value, 'TTF point index', -1, 65535)
            check(
                not (point.hint_mask is not None and (point.ttf_index is not None or point.next_cp_index is not None)),
                'point cannot contain both a hint mask and TTF indices',
            )


def validate(font, *, layout: bool = True) -> None:
    from sfdfont._encoding import REMAP_KEYS, validate_remap
    from sfdfont._extended import EXTENDED_KEYS
    from sfdfont._font_info import INFO_KEYS, validate_info
    from sfdfont._glyph_layout import GLYPH_LAYOUT_KEYS
    from sfdfont._hints import HINT_KEYS
    from sfdfont._legacy_layout import LEGACY_GLYPH_KEYS
    from sfdfont._tables import decode_private, decode_short_table
    from sfdfont._tex import TEX_GLYPH_KEYS, validate_tex
    from sfdfont.legacy_names import SfdStyleMapName

    def font_record(record) -> bool:
        return record.keyword in LAYOUT_KEYS | EXTENDED_KEYS | INFO_KEYS | REMAP_KEYS | {
            'BeginPrivate:',
            'ShortTable:',
            'TtTable:',
        } or record.keyword.startswith('MATH:')

    if font.subfonts or font.cid is not None:
        from sfdfont._family import validate_cid

        validate_cid(font)
    if font.multiple_master is not None:
        from sfdfont._family import validate_mm

        validate_mm(font)
    check(font.version in ('1.0', '2.0', '3.0', '3.1', '3.2'), 'unsupported SFD version')
    validate_info(font.metadata.records)
    validate_remap(font.metadata.records)
    for names in font.metadata.language_names:
        for name in names.style_map_family_names:
            check(
                isinstance(name, SfdStyleMapName) and name.keyword == 'StyleMapFamilyName:',
                'invalid style mapping family name prefix',
            )
            name.to_record()
    validate_tex(font)
    for record in font.metadata.records:
        check(
            record.keyword not in GLYPH_LAYOUT_KEYS | LEGACY_GLYPH_KEYS | HINT_KEYS | TEX_GLYPH_KEYS,
            'glyph layout record in font metadata',
        )
        check(record.keyword != 'UndoRedoHistory', 'undo history belongs in a glyph layer')
        check(
            version_matches(record.keyword, font.version), f'layout record {record.keyword} conflicts with SFD version'
        )
        try:
            if record.keyword == 'BeginPrivate:':
                decode_private(record)
            elif record.keyword == 'ShortTable:':
                decode_short_table(record)
        except SfdParseError as error:
            raise SfdValidationError(str(error)) from error
    number(font.encoding_size, 'encoding size', 0)
    number(font.metadata.ascent, 'ascent', 0)
    number(font.metadata.descent, 'descent', 0)
    check(font.metadata.ascent + font.metadata.descent > 0, 'em size must be positive')
    indices = [info.index for info in font.layer_infos]
    check(len(indices) >= 2 and sorted(indices) == list(range(len(indices))), 'layer IDs must be contiguous from zero')
    gids = {}
    encodings = {}
    for glyph in font.glyphs:
        number(glyph.glyph_id, 'glyph ID', 0)
        check(glyph.glyph_id not in gids, f'duplicate glyph ID {glyph.glyph_id}')
        gids[glyph.glyph_id] = glyph
        number(glyph.encoding, 'glyph encoding', -1)
        if glyph.encoding != -1:
            check(glyph.encoding not in encodings, f'duplicate encoding {glyph.encoding}')
            check(glyph.encoding < font.encoding_size, 'glyph encoding exceeds encoding size')
            encodings[glyph.encoding] = glyph.glyph_id
        unicode_value(glyph.unicode, 'glyph Unicode')
        check(bool(glyph.name) and '\0' not in glyph.name, 'invalid glyph name')
        number(glyph.width, 'glyph width', -32768, 32767)
        check(isinstance(glyph.flags, str) and set(glyph.flags) <= set('HMWOI'), 'invalid glyph flags')
        if glyph.vertical_width is not None:
            number(glyph.vertical_width, 'glyph vertical width', -32768, 32767)
        for alt in glyph.alternate_unicodes:
            unicode_value(alt.unicode, 'alternate Unicode', unassigned=False)
            unicode_value(alt.variation_selector, 'variation selector')
            number(alt.font_id, 'alternate font ID', 0)
        layer_ids = [layer.index for layer in glyph.layers]
        check(len(set(layer_ids)) == len(layer_ids), 'duplicate glyph layer')
        if font.multilayer:
            count = glyph.layer_count if glyph.layer_count is not None else max(layer_ids, default=1) + 1
            number(count, 'Type 3 layer count', 2)
            check(all(0 <= index < count for index in layer_ids), 'undefined Type 3 glyph layer')
        else:
            check(all(index in indices for index in layer_ids), 'undefined glyph layer')
        for layer in glyph.layers:
            if font.multilayer and (layer.index > 0 or layer.paint is not None):
                from sfdfont._paint import validate_paint

                check(layer.paint is not None, 'Type 3 foreground layers require paint settings')
                validate_paint(layer.paint)
            else:
                check(layer.paint is None, 'paint settings require Type 3 layers')
            for record in layer.records:
                check(version_matches(record.keyword, font.version), 'glyph layout record conflicts with SFD version')
                if record.keyword == 'UndoRedoHistory':
                    from sfdfont._history import history_layer

                    check(font.version in ('3.1', '3.2'), 'undo history requires SFD 3.1 or 3.2')
                    try:
                        check(history_layer(record) == layer.index, 'undo history layer mismatch')
                    except SfdParseError as error:
                        raise SfdValidationError(str(error)) from error
            contours(layer.contours)
            check(not any(font_record(record) for record in layer.records), 'layout record in glyph layer')
        for record in glyph.records:
            check(version_matches(record.keyword, font.version), 'glyph layout record conflicts with SFD version')
        check(not any(font_record(record) for record in glyph.records), 'layout record in glyph')
        check(not any(r.keyword == 'UndoRedoHistory' for r in glyph.records), 'undo history belongs in a glyph layer')
    for encoding, target in font.encoding_aliases.items():
        number(encoding, 'alias encoding', 0)
        number(target, 'alias glyph ID', 0)
        check(encoding < font.encoding_size, 'alias encoding exceeds encoding size')
        check(target in gids, f'dangling encoding alias {target}')
        check(encoding not in encodings or encodings[encoding] == target, f'conflicting alias encoding {encoding}')
        encodings[encoding] = target
    graph = {}
    named_glyphs = {glyph.name: glyph for glyph in font.glyphs}
    for glyph in font.glyphs:
        for layer in glyph.layers:
            edges = []
            if layer.paint is not None:
                for pattern in (layer.paint.fill_pattern, layer.paint.stroke_pattern):
                    if pattern is not None:
                        check(pattern.glyph in named_glyphs, f'dangling pattern glyph {pattern.glyph!r}')
                        target = named_glyphs[pattern.glyph]
                        edges.extend((target.glyph_id, v.index) for v in target.layers if v.index > 0)
            for ref in layer.references:
                target = encodings.get(ref.target) if ref.encoded else ref.target
                check(target in gids, f'dangling glyph reference {ref.target}')
                check(
                    len(ref.transform) == 6 and all(math.isfinite(v) for v in ref.transform),
                    'reference requires six finite transform values',
                )
                number(ref.flags, 'reference flags', 0)
                check(bool(ref.flags & 4) == (ref.point_match is not None), 'reference point-match flag mismatch')
                if ref.point_match is not None:
                    check(len(ref.point_match) == 2, 'invalid point-match pair')
                    for point in ref.point_match:
                        number(point, 'reference point index', 0)
                if font.multilayer:
                    edges.extend((target, v.index) for v in gids[target].layers if v.index > 0)
                else:
                    edges.append((target, layer.index))
            graph[(glyph.glyph_id, layer.index)] = edges
    cycles(graph, 'outline')
    contours(font.guidelines)
    bitmap_gids = gids if not font.subfonts else {g.glyph_id: g for sub in font.subfonts for g in sub.glyphs}
    for strike in font.bitmap_strikes:
        number(strike.pixelsize, 'bitmap pixelsize', 1)
        number(strike.ascent, 'bitmap ascent', 0)
        number(strike.descent, 'bitmap descent', 0)
        check(strike.depth in (1, 2, 4, 8), 'unsupported bitmap depth')
        seen = set()
        for glyph in strike.glyphs:
            check(glyph.glyph_id in bitmap_gids, f'bitmap refers to missing glyph {glyph.glyph_id}')
            check(glyph.glyph_id not in seen, 'duplicate bitmap glyph ID')
            seen.add(glyph.glyph_id)
            for value in (glyph.xmin, glyph.xmax, glyph.ymin, glyph.ymax, glyph.advance):
                number(value, 'bitmap metric')
            check(glyph.width > 0 and glyph.height > 0, 'invalid bitmap dimensions')
            stride = (glyph.width + 7) // 8 if strike.depth == 1 else glyph.width
            check(
                isinstance(glyph.data, bytes) and len(glyph.data) == stride * glyph.height,
                'bitmap data length differs from dimensions',
            )
            if strike.depth != 1:
                check(all(v < 1 << strike.depth for v in glyph.data), 'bitmap sample exceeds depth')
        graph = {gid: [] for gid in seen}
        for ref in strike.references:
            check(ref.source in seen and ref.target in seen, 'dangling bitmap reference')
            graph[ref.source].append(ref.target)
        cycles(graph, 'bitmap')
    from sfdfont._layout_validation import validate_layout

    if layout:
        from sfdfont._hints import validate_hints
        from sfdfont._math import validate_math

        validate_layout(font)
        validate_math(font)
        validate_hints(font)
