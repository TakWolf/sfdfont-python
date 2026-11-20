from sfdfont._layout import LAYOUT_KEYS
from sfdfont._layout_validation import layout_identity
from sfdfont.error import SfdValidationError


def check_preservation(font) -> None:
    original = font._snapshot
    if original is None or font == original:
        return
    opaque = bool(
        any(record.keyword not in LAYOUT_KEYS for record in font.metadata.records)
        or font.payloads
        or any(
            glyph.records or glyph.payloads or any(layer.records or layer.images for layer in glyph.layers)
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
        and [r for r in font.metadata.records if r.keyword not in LAYOUT_KEYS]
        == [r for r in original.metadata.records if r.keyword not in LAYOUT_KEYS]
        and layout_identity(font) == layout_identity(original)
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
                [(v.index, v.contours, v.references, v.records, v.images) for v in glyph.layers],
                glyph.records,
                glyph.payloads,
            ) != (
                before.name,
                before.glyph_id,
                before.encoding,
                before.unicode,
                before.alternate_unicodes,
                before.layer_count,
                [(v.index, v.contours, v.references, v.records, v.images) for v in before.layers],
                before.records,
                before.payloads,
            ):
                same = False
                break
    if not same:
        raise SfdValidationError(
            'cannot change identities, outlines or uninterpreted data while retained records depend on them'
        )
