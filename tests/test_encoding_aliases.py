import pytest

from sfdfont import SfdFont, SfdGlyph, SfdLayer, SfdParseError, SfdReference, SfdValidationError


def test_nimbus_encoding_aliases(assets_dir):
    font = SfdFont.load(assets_dir.joinpath('fontforge', 'NimbusLGCUni-Regular.sfd'))
    assert len(font.encoding_aliases) == 26
    assert font.encoding_aliases[205] == 282
    assert font.find_glyph_by_encoding(205).glyph_id == 282
    assert font.find_glyph_by_encoding(-1) is None
    assert font.find_glyph_by_encoding(0x110000) is None
    copied = font.deepcopy()
    assert copied == font
    assert copied.encoding_aliases is not font.encoding_aliases
    assert font.copy().encoding_aliases is font.encoding_aliases


@pytest.mark.parametrize(
    'replacement', [b'-1 282', b'205 -1', b'205 999999', b'1113 282', b'205', b'205 282\nDupEnc: 205 282']
)
def test_invalid_encoding_aliases(assets_dir, replacement):
    data = assets_dir.joinpath('fontforge', 'NimbusLGCUni-Regular.sfd').read_bytes()
    with pytest.raises(SfdParseError):
        SfdFont.parse(data.replace(b'DupEnc: 205 282', b'DupEnc: ' + replacement))


def test_encoded_reference_resolves_through_alias():
    font = SfdFont(
        glyphs=[
            SfdGlyph('A', 1),
            SfdGlyph('B', 2, layers=[SfdLayer(1, references=[SfdReference(65, encoded=True)])]),
        ],
        encoding_aliases={65: 1},
    )
    font.validate()
    font.encoding_aliases[65] = 2
    with pytest.raises(SfdValidationError, match='cyclic'):
        font.validate()
