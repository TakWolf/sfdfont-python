import io

import pytest

from sfdfont import SfdFont, SfdLimitError, SfdParseError, SfdReadLimits, SfdUnsupportedError

MINIMAL = b"""SplineFontDB: 3.2
FontName: Research
LayerCount: 2
Layer: 0 0 "Back" 1
Layer: 1 1 "Fore" 0
BeginChars: 1114112 2
StartChar: composite
Encoding: -1 -1 9
Width: 600
Fore
Refer: 5 65 N 1 0 0 1 20 -30 2
EndChar
StartChar: A
Encoding: 65 65 5
AltUni2: 000041.00fe00.0 0000c0.ffffffff.0
Width: 600
Fore
SplineSet
0 0 m 0,0,1
100 50 100 50 200 0 c 1024,2,-1
EndSplineSet
EndChar
EndChars
EndSplineFont
"""


def test_layers_ids_references_and_alternate_encoding():
    stream = io.BytesIO(MINIMAL)
    font = SfdFont.parse(stream)
    assert not stream.closed
    assert font.layer_infos[1].quadratic
    assert [glyph.glyph_id for glyph in font.glyphs] == [9, 5]
    assert font.glyphs[0].layers[0].references[0].target == 5
    point = font.glyphs[1].layers[0].contours[0].points[1]
    assert point.controls == (100, 50, 100, 50)
    assert point.flags == 1024
    assert point.next_cp_index == -1
    assert font.find_glyphs_by_unicode(0xC0) == [font.glyphs[1]]
    assert font.find_glyphs_by_unicode(65) == [font.glyphs[1]]
    assert font.find_glyphs_by_name('A') == [font.glyphs[1]]
    assert font.copy().glyphs is font.glyphs
    assert font.deepcopy() == font
    assert font.deepcopy().glyphs is not font.glyphs


def test_old_format_implicit_splines_and_reference():
    font = SfdFont.parse_text(
        """SplineFontDB: 1.0
Order2: 1
ScriptLang: 1
1 latn 1 dflt
BeginChars: 256 256
StartChar: A
Encoding: 65 65
Width: 500
Fore
0 0 m 1
100 0 l 0x80
EndSplineSet
Ref: 65 N 1 0 0 1 0 0
EndChar
EndChars
EndSplineFont
""".replace('0x80', '128')
    )
    assert font.layer_infos[1].quadratic
    assert font.glyphs[0].layers[0].references[0].encoded
    assert font.metadata.records[0].keyword == 'ScriptLang:'


def test_utf7_and_legacy_text_fields():
    data = b"""SplineFontDB: 3.0
Copyright: caf\xe9
UComments: "+Ti0A"
LangName: 1033 "" "+2D3eAAAA"
BeginChars: 256 0
EndChars
EndSplineFont
"""
    font = SfdFont.parse(data)
    assert font.metadata.copyright == 'café'
    assert font.metadata.comments == '中'
    assert font.metadata.language_names[0].names == ['', '😀']


@pytest.mark.parametrize(
    'data',
    [
        MINIMAL[:-15],
        MINIMAL + b'junk',
        MINIMAL.replace(b'EndChar\n', b'', 1),
        MINIMAL.replace(b'0 0 m', b'0 0 l'),
        MINIMAL.replace(b'Width: 600', b'Width: nan'),
        MINIMAL.replace(b'1114112 2', b'1114112 3'),
        MINIMAL.replace(b'0 0 m', b'nan 0 m'),
    ],
)
def test_malformed_files(data):
    with pytest.raises(SfdParseError) as caught:
        SfdFont.parse(data)
    assert caught.value.line is not None


@pytest.mark.parametrize('value', [b'0', b'4.0', b'3.9'])
def test_unsupported_versions(value):
    with pytest.raises(SfdUnsupportedError):
        SfdFont.parse(MINIMAL.replace(b'3.2', value))


def test_resource_limits():
    with pytest.raises(SfdLimitError):
        SfdFont.parse(MINIMAL, limits=SfdReadLimits(max_glyphs=1))
    with pytest.raises(SfdLimitError):
        SfdFont.parse(MINIMAL, limits=SfdReadLimits(max_points=1))


def test_unsupported_blocks_are_not_silently_ignored():
    with pytest.raises(SfdUnsupportedError):
        SfdFont.parse(MINIMAL.replace(b'BeginChars:', b'BeginMMFonts:'))
