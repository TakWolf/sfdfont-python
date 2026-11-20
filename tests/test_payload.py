from sfdfont import SfdFont
from sfdfont._reader import encode_ascii85


def test_embedded_images_and_tt_payloads():
    png = b'\x89PNG\r\n\x1a\n'
    data = (
        b'SplineFontDB: 3.2\nTtfTable: cvt  2\n'
        + encode_ascii85(b'\0\1')
        + b'\nEndTtf\nBeginChars: 1 1\nStartChar: a\nEncoding: 0 97 0\nWidth: 500\n'
        + b'TtfInstrs: 3\n'
        + encode_ascii85(b'abc')
        + b'\nEndTtf\nBack\n'
        + b'Image2: image/png 8 0 0 1 1\n'
        + encode_ascii85(png)
        + b'\nEndImage2\n'
        + b'Image: 1 1 1 1 1 ffffffff 0 0 1 1 0\n'
        + encode_ascii85(b'\xff\0\0\x01')
        + b'\nEndImage\nEndChar\nEndChars\nEndSplineFont\n'
    )
    font = SfdFont.parse(data)
    assert font.payloads[0].data == b'\0\1'
    assert font.glyphs[0].payloads[0].data == b'abc'
    assert font.glyphs[0].layers[0].images[0].data == png
    assert font.glyphs[0].layers[0].images[1].data == b'\xff\0\0\x01'


def test_pickle_is_retained_without_execution():
    font = SfdFont.parse(
        b'SplineFontDB: 3.2\nPickledData: "first\nEndSplineFont\n\\"quoted\\""\n'
        b'BeginChars: 0 0\nEndChars\nEndSplineFont\n'
    )
    assert font.metadata.records[0].value == b'"first\nEndSplineFont\n\\"quoted\\""'
