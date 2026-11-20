import pytest

from sfdfont import SfdFont, SfdLimitError, SfdParseError, SfdReadLimits
from sfdfont._parser import record
from sfdfont._reader import Reader


@pytest.mark.parametrize(
    ('key', 'header', 'body'),
    [
        (
            'ChainSub:',
            b"glyph 0 0 'ccmp' 0 0 0 1\n",
            b"String: 7 EndFPST\nBString: 0\nFString: 0\n1\nSeqLookup: 0 's001'\n",
        ),
        (
            'ChainSub2:',
            b'class "subtable" 2 0 0 1\n',
            b'Class: 1 A\n1 0 0\nClsList: 1\nBClsList:\nFClsList:\n1\nSeqLookup: 0 "lookup"\n'
            b'ClassNames: "default" "named"\n',
        ),
        ('ContextPos:', b"coverage 0 0 'kern' 0 0 0 1\n", b"1 0 0\nCoverage: 3 A B\n1\nSeqLookup: 0 'kern'\n"),
        ('ReverseChain2:', b'revcov "subtable" 0 0 0 1\n', b'1 0 0\nCoverage: 3 A B\nReplace: 3 C D\n'),
    ],
)
def test_context_record_boundary(key, header, body):
    reader = Reader(header + body + b'EndFPST\nNext: value\n')
    parsed = record(reader, key)
    assert parsed.keyword == key
    assert parsed.value.endswith(b'EndFPST')
    assert body.strip() in parsed.value
    assert reader.word() == 'Next:'


@pytest.mark.parametrize(
    'body',
    [
        b'class 0 0\n',
        b"unknown 0 0 'ccmp' 0 0 0 0\nEndFPST\n",
        b"glyph 0 0 'ccmp' 0 0 0 -1\nEndFPST\n",
        b"glyph 0 0 'ccmp' 0 0 0 1\nString: 999 A\nEndFPST\n",
        b"class 0 0 'ccmp' 1 0 0 1\n1 0 0\nClsList: 1\n",
        b"glyph 0 0 'ccmp' 0 0 0 0\nFontName: wrong\n",
    ],
)
def test_malformed_context_record(body):
    with pytest.raises(SfdParseError):
        record(Reader(body), 'ChainSub:')


def test_layout_count_budget():
    with pytest.raises(SfdLimitError):
        record(Reader(b"class 0 0 'ccmp' 0 0 0 1000\n", SfdReadLimits(max_bytes=100)), 'ChainSub:')


def test_dejavu_context_records_retained(assets_dir):
    font = SfdFont.load(assets_dir.joinpath('fontforge', 'DejaVuSerif.sfd'))
    context = next(item for item in font.metadata.records if item.keyword == 'ChainSub:')
    assert context.value.startswith(b"class 0 0 'ccmp'")
    assert context.value.count(b'SeqLookup:') == 2
    assert context.value.endswith(b'EndFPST')
