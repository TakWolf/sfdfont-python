from __future__ import annotations

import math

from sfdfont.error import SfdValidationError


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
        check(bool(contour.points) and contour.points[0].command == 'm', 'contour must begin with m')
        for index, point in enumerate(contour.points):
            check(point.command in ('m', 'l', 'c') and (point.command != 'm' or index == 0), 'invalid contour command')
            check(len(point.controls) == (4 if point.command == 'c' else 0), 'invalid control coordinates')
            check(
                all(isinstance(v, (int, float)) and math.isfinite(v) for v in (point.x, point.y, *point.controls)),
                'nonfinite point coordinate',
            )
            number(point.flags, 'point flags', 0, 0xFFFFFFFF)
            if point.hint_mask is not None:
                check(isinstance(point.hint_mask, bytes) and bool(point.hint_mask), 'invalid hint mask')
            for value in (point.ttf_index, point.next_cp_index):
                if value is not None:
                    number(value, 'TTF point index', -1, 65535)
            check(
                not (point.hint_mask is not None and (point.ttf_index is not None or point.next_cp_index is not None)),
                'point cannot contain both a hint mask and TTF indices',
            )


def validate(font) -> None:
    check(font.version in ('1.0', '2.0', '3.0', '3.1', '3.2'), 'unsupported SFD version')
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
        if glyph.vertical_width is not None:
            number(glyph.vertical_width, 'glyph vertical width', -32768, 32767)
        for alt in glyph.alternate_unicodes:
            unicode_value(alt.unicode, 'alternate Unicode', unassigned=False)
            unicode_value(alt.variation_selector, 'variation selector')
            number(alt.font_id, 'alternate font ID', 0)
        layer_ids = [layer.index for layer in glyph.layers]
        check(len(set(layer_ids)) == len(layer_ids), 'duplicate glyph layer')
        check(all(index in indices for index in layer_ids), 'undefined glyph layer')
        for layer in glyph.layers:
            contours(layer.contours)
    graph = {}
    for glyph in font.glyphs:
        for layer in glyph.layers:
            edges = []
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
                edges.append((target, layer.index))
            graph[(glyph.glyph_id, layer.index)] = edges
    cycles(graph, 'outline')
    contours(font.guidelines)
    for strike in font.bitmap_strikes:
        number(strike.pixelsize, 'bitmap pixelsize', 1)
        number(strike.ascent, 'bitmap ascent', 0)
        number(strike.descent, 'bitmap descent', 0)
        check(strike.depth in (1, 2, 4, 8), 'unsupported bitmap depth')
        seen = set()
        for glyph in strike.glyphs:
            check(glyph.glyph_id in gids, f'bitmap refers to missing glyph {glyph.glyph_id}')
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
