import pytest

from sfdfont import SfdFont, SfdLimitError, SfdMacName, SfdParseError, SfdReadLimits, SfdValidationError
from sfdfont._family import mac_name
from sfdfont._parser import _parse_font
from sfdfont._reader import Reader


def read_caslon_structure(assets_dir):
    # This upstream legacy file has duplicate glyph IDs, so inspect its family
    # grammar independently of the document's strict integrity check.
    reader = Reader(assets_dir.joinpath('fontforge', 'CaslonMM.sfd').read_bytes())
    reader.point_count = reader.glyph_count = 0
    return _parse_font(reader)


def test_upstream_multiple_master_structure(assets_dir):
    font = read_caslon_structure(assets_dir)
    mm = font.multiple_master
    assert font.metadata.font_name == 'CaslonMM'
    assert [f.metadata.font_name for f in mm.instances] == ['CaslonThin', 'CaslonBlack']
    assert mm.axes == ['Weight']
    assert mm.positions == [[0], [1]]
    assert mm.weights == [0.625, 0.375]
    assert mm.axis_maps[0].points == [(0, 100), (1, 1000)]
    assert b'100 sub 900 div' in mm.ndv
    assert mm.copy().instances is mm.instances
    assert mm.deepcopy().instances is not mm.instances
    assert font.copy() == font.deepcopy() == font


def test_global_family_glyph_budget(assets_dir):
    with pytest.raises(SfdLimitError, match='max_glyphs'):
        SfdFont.load(assets_dir.joinpath('fontforge', 'CaslonMM.sfd'), limits=SfdReadLimits(max_glyphs=400))


def test_mac_names_use_declared_byte_length_and_octal_escapes():
    assert mac_name(b'0 1 3 "A\\217B"') == SfdMacName(0, 1, b'A\x8fB')
    with pytest.raises(SfdParseError, match='length'):
        mac_name(b'0 1 4 "A\\217B"')
    with pytest.raises(SfdParseError, match='escape'):
        mac_name(b'0 1 1 "\\777"')


@pytest.mark.parametrize(
    ('old', 'new', 'message'),
    [
        (b'MMCounts: 2 1', b'MMCounts: 2 0', 'MMCounts'),
        (b'MMPositions: 0 1', b'MMPositions: 0', 'MMPositions'),
        (b'MMAxisMap: 0 2', b'MMAxisMap: 1 2', 'MMAxisMap'),
        (b'BeginMMFonts: 3 336', b'BeginMMFonts: 2 336', 'BeginMMFonts'),
        (b'EndMMFonts', b'', 'EndMMFonts'),
    ],
)
def test_malformed_upstream_family_header(assets_dir, old, new, message):
    data = assets_dir.joinpath('fontforge', 'CaslonMM.sfd').read_bytes()
    with pytest.raises(SfdParseError, match=message):
        SfdFont.parse(data.replace(old, new, 1))


def test_cycle_and_dimension_checks_before_recursing_into_masters(assets_dir):
    font = read_caslon_structure(assets_dir)
    font.multiple_master.positions.pop()
    with pytest.raises(SfdValidationError, match='count mismatch'):
        font.validate()
    font.multiple_master.positions.append([1])
    font.multiple_master.instances[0] = font
    with pytest.raises(SfdValidationError, match='cyclic'):
        font.validate()
