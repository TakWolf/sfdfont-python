import pytest

from sfdfont import (
    SfdBaselines,
    SfdCidInfo,
    SfdFont,
    SfdJustification,
    SfdJustificationScript,
    SfdMacFeature,
    SfdMacFeatures,
    SfdMacName,
    SfdParseError,
    SfdValidationError,
)
from sfdfont._layout import LAYOUT_KEYS
from sfdfont._parser import _parse_font
from sfdfont._reader import Reader


def test_empty_cid_container_boundaries():
    data = (
        b'SplineFontDB: 3.2\nRegistry: Adobe\nOrdering: Identity\nSupplement: 0\nCIDVersion: 1\n'
        b'BeginSubFonts: 1 0\nFontName: EmptySub\nBeginChars: 0 -1\nEndChars\n'
        b'EndSubSplineFont\nEndSubFonts\nEndSplineFont\n'
    )
    font = SfdFont.parse(data)
    assert font.cid == SfdCidInfo(version=1)
    assert len(font.subfonts) == 1
    assert font.subfonts[0].metadata.font_name == 'EmptySub'
    assert font.subfonts[0]._snapshot is not None
    with pytest.raises(SfdParseError):
        SfdFont.parse(data.replace(b'EndSubFonts\n', b''))
    with pytest.raises(SfdParseError):
        SfdFont.parse(data.replace(b'BeginSubFonts: 1 0', b'BeginSubFonts: 2 0'))


def test_legacy_cid_uses_encoding_as_implicit_cid():
    reader = Reader(
        b'BeginChars: 100 -1\nStartChar: A\nEncoding: 65 65\nWidth: 600\nEndChar\nEndChars\nEndSubSplineFont'
    )
    reader.point_count = reader.glyph_count = 0
    font = _parse_font(reader, '1.0', cid_child=True)
    assert font.glyphs[0].glyph_id == 65


def test_cid_shared_layout_and_queries(assets_dir):
    subfont = SfdFont.load(assets_dir.joinpath('fontforge', 'VKern.sfd'))
    font = SfdFont(version=subfont.version, cid=SfdCidInfo(), subfonts=[subfont])
    records = subfont.metadata.records
    font.metadata.records = [r for r in records if r.keyword in LAYOUT_KEYS]
    subfont.metadata.records = [r for r in records if r.keyword not in LAYOUT_KEYS]
    font.validate()
    assert len(list(font.iter_glyphs())) == len(subfont.glyphs)
    assert font.find_glyphs_by_name('A') == subfont.find_glyphs_by_name('A')
    assert font.find_glyphs_by_unicode(65) == subfont.find_glyphs_by_unicode(65)
    assert font.find_glyph_by_encoding(65) is subfont.find_glyph_by_encoding(65)
    font.encoding_size = 0
    with pytest.raises(SfdValidationError, match='capacity'):
        font.validate()
    font.encoding_size = 0x110000
    subfont.glyphs = [g for g in subfont.glyphs if g.name != 'A.vert']
    with pytest.raises(SfdValidationError, match='unknown glyph'):
        font.validate()


def test_cid_recursive_and_metadata_validation():
    font = SfdFont(cid=SfdCidInfo())
    with pytest.raises(SfdValidationError, match='requires subfonts'):
        font.validate()
    font.subfonts.append(font)
    with pytest.raises(SfdValidationError, match='cyclic'):
        font.validate()
    font.subfonts = [SfdFont()]
    font.cid.supplement = -1
    with pytest.raises(SfdValidationError, match='supplement'):
        font.validate()


@pytest.mark.parametrize(
    'model',
    [
        SfdBaselines('BaseHoriz:'),
        SfdBaselines('BaseVert:'),
        SfdJustification([SfdJustificationScript()]),
        SfdMacFeatures([SfdMacFeature(names=[SfdMacName(data=b'Custom')])]),
    ],
)
def test_cid_extended_layout_belongs_to_container(model):
    item = model.to_record()
    subfont = SfdFont()
    font = SfdFont(cid=SfdCidInfo(), subfonts=[subfont])
    font.metadata.records.append(item)
    font.validate()
    font.metadata.records.clear()
    subfont.metadata.records.append(item)
    with pytest.raises(SfdValidationError, match='CID layout belongs in the container'):
        font.validate()
