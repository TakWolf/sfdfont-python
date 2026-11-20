import pytest

from sfdfont import SfdDesignSize, SfdFont, SfdParseError, SfdRecord, SfdStyleName, SfdValidationError
from sfdfont._parser import record
from sfdfont._reader import Reader


def test_design_size_models_copy_and_unicode_names():
    names = [SfdStyleName(0x0409, 'Text'), SfdStyleName(0x0804, '正文 😀')]
    value = SfdDesignSize(120, (100, 140), 1, names)
    assert value.names is names
    assert value.copy().names is names
    assert value.deepcopy().names[0] is not names[0]
    assert value.deepcopy() == value
    assert SfdDesignSize.from_record(value.to_record()) == value
    assert names[0].copy() == names[0].deepcopy() == names[0]
    assert SfdDesignSize().names is not SfdDesignSize().names


@pytest.mark.parametrize('value', [SfdDesignSize(), SfdDesignSize(120), SfdDesignSize(120, (0, 0), 0)])
def test_design_size_optional_fields_are_preserved(value):
    assert SfdDesignSize.from_record(value.to_record()) == value


def test_design_size_accepts_old_space_separated_range():
    value = SfdDesignSize.from_record(SfdRecord('DesignSize:', b'120 100 140 1 1033 "Text"'))
    assert value == SfdDesignSize(120, (100, 140), 1, [SfdStyleName(1033, 'Text')])
    assert b'100-140' in value.to_record().value


@pytest.mark.parametrize(
    'data',
    [
        b'-1',
        b'65536',
        b'120 100-140',
        b'120 140-100 1',
        b'120 100-65536 1',
        b'120 100-140 65536',
        b'120 100-140 1 1033',
        b'120 100-140 1 65536 "Text"',
        b'120 100-140 1 1033 "One" 1033 "Two"',
        b'120 unexpected',
    ],
)
def test_invalid_design_size_records(data):
    reader = Reader(b'DesignSize: ' + data + b'\n')
    with pytest.raises(SfdParseError):
        record(reader, reader.word())


@pytest.mark.parametrize(
    'value',
    [
        SfdDesignSize(-1),
        SfdDesignSize(120, style_id=1),
        SfdDesignSize(120, names=[SfdStyleName()]),
        SfdDesignSize(120, (100, 140)),
        SfdDesignSize(120, (140, 100), 1),
        SfdDesignSize(120, (100, 140), 1, [SfdStyleName(65536)]),
    ],
)
def test_invalid_design_size_models(value):
    with pytest.raises(SfdValidationError):
        value.to_record()


def test_design_size_edit_on_upstream_font(assets_dir):
    font = SfdFont.load(assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd'))
    font.metadata.records.append(SfdDesignSize(120).to_record())
    font = SfdFont.parse(font.dump_to_bytes())
    index = next(i for i, item in enumerate(font.metadata.records) if item.keyword == 'DesignSize:')
    value = SfdDesignSize.from_record(font.metadata.records[index])
    value.range = (100, 140)
    value.style_id = 1
    value.names = [SfdStyleName(1033, 'Text')]
    font.metadata.records[index] = value.to_record()
    assert SfdFont.parse(font.dump_to_bytes()) == font
    font.metadata.records.append(value.to_record())
    with pytest.raises(SfdValidationError, match='duplicate'):
        font.validate()
    with pytest.raises(SfdParseError):
        SfdDesignSize.from_record(SfdRecord('Unknown:', b'120'))
