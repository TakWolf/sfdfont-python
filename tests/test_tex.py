import pytest

from sfdfont import SfdFont, SfdGlyph, SfdLayer, SfdParseError, SfdRecord, SfdTexData, SfdTexMetrics, SfdValidationError
from sfdfont._parser import record
from sfdfont._reader import Reader


def test_tex_data_fixed_parameters_and_copy_semantics():
    parameters = [0] * 22
    parameters[0], parameters[-1] = -0x80000000, 0x7FFFFFFF
    value = SfdTexData(2, 12 << 20, parameters)
    assert value.parameters is parameters
    assert value.copy().parameters is parameters
    assert value.deepcopy().parameters is not parameters
    assert value.deepcopy() == value
    assert SfdTexData.from_record(value.to_record()) == value
    assert SfdTexData().parameters == [0] * 22
    assert SfdTexData().parameters is not SfdTexData().parameters
    explicit = []
    assert SfdTexData(parameters=explicit).parameters is explicit


@pytest.mark.parametrize('kind', [0, 1, 2, 3])
def test_tex_data_kinds(kind):
    value = SfdTexData(kind, 0)
    assert SfdTexData.from_record(value.to_record()) == value


def test_tex_glyph_metrics_preserve_old_fixup_inputs():
    value = SfdTexMetrics.from_record(SfdRecord('TeX:', b'0 0 0 0'))
    assert value == SfdTexMetrics(0, 0, (0, 0))
    assert value.to_record().value == b'0 0 0 0'
    assert value.copy() == value.deepcopy() == value
    modern = SfdTexMetrics.from_record(SfdRecord('TeX:', b'700 65535'))
    assert modern == SfdTexMetrics(700, -1)
    assert modern.legacy is None
    assert SfdTexMetrics.from_record(SfdTexMetrics().to_record()) == SfdTexMetrics()


@pytest.mark.parametrize(
    'key, data',
    [
        ('TeX:', b'700'),
        ('TeX:', b'700 10 0'),
        ('TeX:', b'700 10 0 0 1'),
        ('TeX:', b'65536 10'),
        ('TeX:', b'-32769 10'),
        ('TeXData:', b'4 0 ' + b'0 ' * 22),
        ('TeXData:', b'1 0 ' + b'0 ' * 21),
        ('TeXData:', b'1 0 ' + b'0 ' * 23),
        ('TeXData:', b'1 2147483648 ' + b'0 ' * 22),
        ('TeXData:', b'1 0 -2147483649 ' + b'0 ' * 21),
    ],
)
def test_invalid_tex_records(key, data):
    reader = Reader(key.encode() + b' ' + data + b'\n')
    with pytest.raises(SfdParseError):
        record(reader, reader.word())


@pytest.mark.parametrize(
    'model',
    [
        SfdTexData(parameters=[]),
        SfdTexData(kind=True),
        SfdTexData(design_size=1 << 31),
        SfdTexMetrics(height=32768),
        SfdTexMetrics(legacy=(1,)),
        SfdTexMetrics(legacy=(0, False)),
    ],
)
def test_invalid_tex_models(model):
    with pytest.raises(SfdValidationError):
        model.to_record()


@pytest.mark.parametrize('name', ['Hinting.sfd', 'NumberPoints.sfd', 'NimbusLGCUni-Regular.sfd', 'DejaVuSerif.sfd'])
def test_upstream_tex_models_and_numeric_edits(assets_dir, name):
    font = SfdFont.load(assets_dir.joinpath('fontforge', name))
    changed = 0
    for glyph in font.iter_glyphs():
        for items in [glyph.records, *(layer.records for layer in glyph.layers)]:
            for i, item in enumerate(items):
                if item.keyword == 'TeX:':
                    value = SfdTexMetrics.from_record(item)
                    assert SfdTexMetrics.from_record(value.to_record()) == value
                    value.height += 1
                    items[i] = value.to_record()
                    changed += 1
    assert changed
    assert SfdFont.parse(font.dump_to_bytes()) == font


def test_tex_data_and_design_size_remain_independent(assets_dir):
    source = assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd').read_bytes()
    # Historical files may have redundant sizes; preserve them without applying FontForge's fixups.
    data = b'DesignSize: 120\nTeXData: ' + SfdTexData(1, 10 << 20).to_record().value + b'\n'
    font = SfdFont.parse(source.replace(b'BeginChars:', data + b'BeginChars:', 1))
    value = SfdTexData.from_record(next(item for item in font.metadata.records if item.keyword == 'TeXData:'))
    assert value.design_size == 10 << 20
    assert SfdFont.parse(font.dump_to_bytes()) == font


def test_tex_scope_and_duplicates():
    font = SfdFont()
    font.metadata.records.append(SfdTexMetrics().to_record())
    with pytest.raises(SfdValidationError, match='font metadata'):
        font.validate()
    font.metadata.records.clear()
    font.glyphs = [SfdGlyph(records=[SfdTexData().to_record()])]
    with pytest.raises(SfdValidationError, match='record in glyph'):
        font.validate()
    font.glyphs[0].records = [SfdTexMetrics().to_record()]
    font.glyphs[0].layers = [SfdLayer(records=[SfdTexMetrics().to_record()])]
    with pytest.raises(SfdValidationError, match='duplicate TeX'):
        font.validate()
