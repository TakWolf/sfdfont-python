from sfdfont._glyph_layout import GLYPH_LAYOUT_KEYS
from sfdfont._layout import LAYOUT_KEYS
from sfdfont._layout_validation import layout_identity
from sfdfont._legacy_layout import LEGACY_KEYS, legacy_identity
from sfdfont._math import GLYPH_MATH_KEYS, math_constant
from sfdfont.error import SfdValidationError


def protected_records(items):
    return [
        r
        for r in items
        if r.keyword not in GLYPH_MATH_KEYS | GLYPH_LAYOUT_KEYS | LAYOUT_KEYS | LEGACY_KEYS
        and not math_constant(r.keyword)
    ]


def check_preservation(font) -> None:
    original = font._snapshot
    if original is None or font == original:
        return
    opaque = bool(
        protected_records(font.metadata.records)
        or legacy_identity(font.metadata.records)
        or font.payloads
        or any(
            protected_records(glyph.records)
            or legacy_identity(glyph.records)
            or glyph.payloads
            or any(
                protected_records(layer.records) or legacy_identity(layer.records) or layer.images
                for layer in glyph.layers
            )
            for glyph in font.glyphs
        )
    )
    if not opaque:
        return
    same = (
        font.version == original.version
        and font.multilayer == original.multilayer
        and font.cid == original.cid
        and [[(g.glyph_id, g.name, g.encoding) for g in sub.glyphs] for sub in font.subfonts]
        == [[(g.glyph_id, g.name, g.encoding) for g in sub.glyphs] for sub in original.subfonts]
        and font.layer_infos == original.layer_infos
        and font.encoding_size == original.encoding_size
        and font.encoding_aliases == original.encoding_aliases
        and font.payloads == original.payloads
        and font.metadata.encoding == original.metadata.encoding
        and font.metadata.ascent == original.metadata.ascent
        and font.metadata.descent == original.metadata.descent
        and protected_records(font.metadata.records) == protected_records(original.metadata.records)
        and layout_identity(font) == layout_identity(original)
        and legacy_identity(font.metadata.records) == legacy_identity(original.metadata.records)
        and len(font.glyphs) == len(original.glyphs)
    )
    if same:
        for glyph, before in zip(font.glyphs, original.glyphs, strict=True):
            if (
                glyph.name,
                glyph.glyph_id,
                glyph.encoding,
                glyph.unicode,
                glyph.alternate_unicodes,
                glyph.layer_count,
                [
                    (
                        v.index,
                        v.contours,
                        v.references,
                        protected_records(v.records),
                        legacy_identity(v.records),
                        v.images,
                    )
                    for v in glyph.layers
                ],
                protected_records(glyph.records),
                legacy_identity(glyph.records),
                glyph.payloads,
            ) != (
                before.name,
                before.glyph_id,
                before.encoding,
                before.unicode,
                before.alternate_unicodes,
                before.layer_count,
                [
                    (
                        v.index,
                        v.contours,
                        v.references,
                        protected_records(v.records),
                        legacy_identity(v.records),
                        v.images,
                    )
                    for v in before.layers
                ],
                protected_records(before.records),
                legacy_identity(before.records),
                before.payloads,
            ):
                same = False
                break
    if not same:
        raise SfdValidationError(
            'cannot change identities, outlines or uninterpreted data while retained records depend on them'
        )
