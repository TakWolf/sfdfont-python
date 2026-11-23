from sfdfont._encoding import REMAP_KEYS, remap_identity
from sfdfont._extended import EXTENDED_KEYS
from sfdfont._feature_names import feature_names_opaque
from sfdfont._font_info import INFO_KEYS
from sfdfont._font_text import FONT_TEXT_KEYS
from sfdfont._glyph_layout import GLYPH_LAYOUT_KEYS
from sfdfont._groups import group_identity
from sfdfont._hints import HINT_KEYS, hint_identity
from sfdfont._layout import LAYOUT_KEYS
from sfdfont._layout_validation import layout_identity
from sfdfont._legacy_layout import LEGACY_KEYS, legacy_identity
from sfdfont._math import GLYPH_MATH_KEYS, math_constant
from sfdfont._tables import TABLE_KEYS, table_identity
from sfdfont._tex import TEX_GLYPH_KEYS
from sfdfont.error import SfdValidationError


def protected_records(items):
    editable = (
        GLYPH_MATH_KEYS
        | GLYPH_LAYOUT_KEYS
        | LAYOUT_KEYS
        | LEGACY_KEYS
        | HINT_KEYS
        | TABLE_KEYS
        | EXTENDED_KEYS
        | INFO_KEYS
        | TEX_GLYPH_KEYS
        | REMAP_KEYS
    )
    return [r for r in items if r.keyword not in editable and not math_constant(r.keyword)]


def check_preservation(font) -> None:
    original = font._snapshot
    if original is None or font == original:
        return
    opaque = bool(
        protected_records(font.metadata.records)
        or any(item.keyword in FONT_TEXT_KEYS for item in font.metadata.records)
        or any(item.keyword == 'woffMetadata:' for item in font.metadata.records)
        or feature_names_opaque(font.metadata.records)
        or group_identity(font.metadata.records)
        or any(item.keyword == 'ScriptLang:' for item in font.metadata.records)
        or remap_identity(font.metadata.records) is not None
        or legacy_identity(font.metadata.records)
        or table_identity(font.metadata.records)
        or font.payloads
        or any(
            protected_records(glyph.records)
            or legacy_identity(glyph.records)
            or hint_identity(glyph.records)
            or glyph.payloads
            or any(
                protected_records(layer.records)
                or legacy_identity(layer.records)
                or hint_identity(layer.records)
                or layer.images
                for layer in glyph.layers
            )
            for glyph in font.glyphs
        )
    )
    if not opaque:
        return
    if family_identity(font) != family_identity(original):
        raise SfdValidationError(
            'cannot change identities, outlines or uninterpreted data while retained records depend on them'
        )


def glyph_identity(glyph):
    return (
        glyph.name,
        glyph.glyph_id,
        glyph.encoding,
        glyph.unicode,
        glyph.alternate_unicodes,
        glyph.layer_count,
        [
            (
                layer.index,
                layer.contours,
                layer.references,
                protected_records(layer.records),
                legacy_identity(layer.records),
                hint_identity(layer.records),
                layer.images,
            )
            for layer in glyph.layers
        ],
        protected_records(glyph.records),
        legacy_identity(glyph.records),
        hint_identity(glyph.records),
        glyph.payloads,
    )


def family_identity(font):
    # A container's opaque records can depend on any child's structure. Compare
    # children against the container snapshot even if a child has no opaque data
    # or was replaced by a newly constructed object without its own snapshot.
    return (
        font.version,
        font.multilayer,
        font.cid,
        font.layer_infos,
        font.encoding_size,
        font.encoding_aliases,
        font.payloads,
        font.metadata.encoding,
        font.metadata.ascent,
        font.metadata.descent,
        protected_records(font.metadata.records),
        layout_identity(font),
        remap_identity(font.metadata.records),
        legacy_identity(font.metadata.records),
        table_identity(font.metadata.records),
        [glyph_identity(glyph) for glyph in font.glyphs],
        [family_identity(subfont) for subfont in font.subfonts],
        None
        if font.multiple_master is None
        else [family_identity(instance) for instance in font.multiple_master.instances],
    )
