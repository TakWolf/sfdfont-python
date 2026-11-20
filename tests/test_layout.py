import pytest

from sfdfont import SfdFont, SfdLimitError, SfdParseError, SfdReadLimits, SfdRecord, SfdValidationError
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


@pytest.mark.parametrize(
    ('key', 'header', 'classes', 'matrix'),
    [
        ('KernClass:', b'2 2 0 0\n', b'1 A\n1 V\n', b'0 0 0 -80'),
        ('VKernClass:', b'2 2 0 0\n', b'1 A\n1 V\n', b'0 0 0 -80'),
        ('KernClass2:', b'2+ 2 "kern"\n', b'0\n1 A\n1 V\n', b'0 0 0 -80 {12-13 1,-1}'),
        ('VKernClass2:', b'2 2 "kern"\n', b'1 A\n1 V\n', b'0 0 0 -80 {}'),
        ('KernClass3:', b'2+ 2 "kern"\n', b'0 "" ""\n1 "left" "A"\n0 "right" "V"\n', b'0 0 0 0 0 0 1 -80 {12-13 1,-1}'),
        ('VKernClass3:', b'2 2 "kern"\n', b'0\n0\n', b'0 0 0 0 0 0 0 -80'),
    ],
)
def test_kerning_class_boundaries(key, header, classes, matrix):
    reader = Reader(header + classes + matrix + b'\nNext: value\n')
    parsed = record(reader, key)
    assert parsed.value == (header + classes + matrix).strip()
    assert reader.word() == 'Next:'


@pytest.mark.parametrize(
    'body',
    [
        b'0 1 0 0\n',
        b'2 2 0 0\n-1 A\n',
        b'2 2 0 0\n999 A\n',
        b'1 1 0 0\n',
        b'1 1 0 0\n-80 {14-12 0}\n',
        b'1 1 0 0\n-80 {12-13 1}\n',
    ],
)
def test_malformed_kerning_classes(body):
    with pytest.raises(SfdParseError):
        record(Reader(body), 'KernClass:')


def test_kerning_matrix_budget():
    with pytest.raises(SfdLimitError):
        record(Reader(b'100 100 0 0\n', SfdReadLimits(max_bytes=100)), 'KernClass:')


def test_horizontal_and_vertical_classes_retained(assets_dir):
    font = SfdFont.load(assets_dir.joinpath('fontforge', 'VKern.sfd'))
    classes = {item.keyword: item for item in font.metadata.records if item.keyword in ('KernClass:', 'VKernClass:')}
    assert classes['KernClass:'].value.startswith(b'4 4 0 0')
    assert b'-200 -146' in classes['KernClass:'].value
    assert classes['VKernClass:'].value.startswith(b'3 3 0 0')


@pytest.mark.parametrize(
    'definition',
    [
        b'1 0 0 "single" { "subtable" ("suffix") } [\'liga\' (\'latn\' <\'dflt\' >)]',
        b"258 0 1 \"pair\" { \"subtable\" (1)[20,-40,7] } ['kern' ('latn' <'dflt' 'TRK '>)]",
        b'4 0 0 "mac" { "subtable" } [<1,2> (\'latn\' <\'dflt\'>)]',
        b'5 0 0 "empty" {} []',
    ],
)
def test_lookup_boundaries(definition):
    reader = Reader(definition + b'\nNext: value\n')
    parsed = record(reader, 'Lookup:')
    assert parsed.value == definition
    assert reader.word() == 'Next:'


@pytest.mark.parametrize(
    'definition',
    [
        b'1 0 0 "unterminated',
        b'1 0 0 "name" { "subtable"',
        b'1 0 0 "name" { "subtable" (2) } []',
        b"1 0 0 \"name\" {} ['liga' ('latn' <'dflt'>)",
        b'1 0 0 "" {} []',
    ],
)
def test_malformed_lookup(definition):
    with pytest.raises(SfdParseError):
        record(Reader(definition), 'Lookup:')


@pytest.mark.parametrize(
    ('version', 'key'),
    [
        ('1.0', 'Lookup:'),
        ('1.0', 'ChainSub2:'),
        ('1.0', 'KernClass2:'),
        ('3.2', 'KernClass:'),
        ('3.2', 'TableOrder:'),
    ],
)
def test_layout_version_mismatch(version, key):
    font = SfdFont(version=version)
    font.metadata.records.append(SfdRecord(key))
    with pytest.raises(SfdValidationError, match='conflicts with SFD version'):
        font.validate()
