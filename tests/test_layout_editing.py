import pytest

from sfdfont import (
    SfdContext,
    SfdContextRule,
    SfdFont,
    SfdGlyph,
    SfdKerningClass,
    SfdLookup,
    SfdLookupFeature,
    SfdLookupSubtable,
    SfdSequenceLookup,
    SfdValidationError,
)


def modern_font():
    font = SfdFont(glyphs=[SfdGlyph('A', 0, 65, 65), SfdGlyph('B', 1, 66, 66)])
    font.set_lookup(SfdLookup(1, 'replace', subtables=[SfdLookupSubtable('replace-sub')]))
    font.set_lookup(
        SfdLookup(
            6,
            'context',
            subtables=[SfdLookupSubtable('context-sub')],
            features=[SfdLookupFeature('calt', {'latn': ['dflt']})],
        )
    )
    context = SfdContext(
        subtable='context-sub',
        rules=[
            SfdContextRule(inputs=['A'], lookups=[SfdSequenceLookup(0, 'replace')]),
        ],
    )
    font.metadata.records.append(context.to_record())
    return font


def test_lookup_dependency_validation():
    font = modern_font()
    font.validate()
    definition = font.find_lookup('replace')
    assert definition is not None
    definition.flags = 8
    assert font.find_lookup('replace').flags == 0
    font.set_lookup(definition)
    assert font.find_lookup('replace').flags == 8
    font.metadata.records.pop(0)
    with pytest.raises(SfdValidationError, match='undefined nested lookup'):
        font.validate()


def test_context_cycle_rejected():
    font = modern_font()
    context = SfdContext.from_record(font.metadata.records[-1])
    context.rules[0].lookups[0].lookup = 'context'
    font.metadata.records[-1] = context.to_record()
    with pytest.raises(SfdValidationError, match='cyclic layout'):
        font.validate()


def test_wrong_lookup_type_rejected():
    font = modern_font()
    lookup = font.find_lookup('context')
    lookup.lookup_type = 258
    font.set_lookup(lookup)
    with pytest.raises(SfdValidationError, match='type mismatch'):
        font.validate()


def test_edit_upstream_metadata_advance_and_kerning(assets_dir, tmp_path):
    font = SfdFont.load(assets_dir.joinpath('fontforge', 'VKern.sfd'))
    font.metadata.full_name = 'Edited VKern'
    font.metadata.comments = '保留排版与提示 😀'
    font.glyphs[0].width += 12
    index = next(i for i, record in enumerate(font.metadata.records) if record.keyword == 'KernClass:')
    kern = SfdKerningClass.from_record(font.metadata.records[index])
    kern.offsets[1][1] = -220
    font.metadata.records[index] = kern.to_record()
    path = tmp_path.joinpath('VKern.sfd')
    font.save(path)
    assert SfdFont.load(path) == font


def test_edit_upstream_bitmap_pixels(assets_dir, tmp_path):
    font = SfdFont.load(assets_dir.joinpath('fontforge', 'Ambrosia.sfd'))
    strike = next(strike for strike in font.bitmap_strikes if strike.depth == 8)
    bitmap = strike.glyphs[0]
    bitmap.data = bytes([bitmap.data[0] ^ 1]) + bitmap.data[1:]
    path = tmp_path.joinpath('Ambrosia.sfd')
    font.save(path)
    assert SfdFont.load(path) == font


def test_unknown_geometry_dependency_remains_protected(assets_dir):
    font = SfdFont.load(assets_dir.joinpath('fontforge', 'DejaVuSerif.sfd'))
    font.glyphs[0].name = 'Changed'
    with pytest.raises(SfdValidationError):
        font.dump_to_bytes()
