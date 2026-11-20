import pytest

from sfdfont import (
    SfdFont,
    SfdParseError,
    SfdPrivateDict,
    SfdPrivateEntry,
    SfdRecord,
    SfdShortTable,
    SfdShortTableWord,
    SfdValidationError,
)


def test_private_model_retains_order_duplicates_and_raw_bytes():
    model = SfdPrivateDict(
        [
            SfdPrivateEntry('Custom', b'  (first\nEndPrivate\nlast)  '),
            SfdPrivateEntry('Custom', b''),
            SfdPrivateEntry('Raw', b'\xff'),
        ]
    )
    assert SfdPrivateDict.from_record(model.to_record()) == model
    assert model.copy().entries is model.entries
    assert model.deepcopy().entries[0] is not model.entries[0]
    assert model.deepcopy() == model
    entries = []
    assert SfdPrivateDict(entries).entries is entries
    assert SfdPrivateDict().entries is not SfdPrivateDict().entries


def test_private_model_decodes_logical_continuations():
    value = SfdPrivateDict.from_record(SfdRecord('BeginPrivate:', b'1\nBlueValues 6 [1\\\n 20]\nEndPrivate'))
    assert value.entries == [SfdPrivateEntry('BlueValues', b'[1 20]')]
    assert SfdPrivateDict.from_record(value.to_record()) == value


@pytest.mark.parametrize(
    'entry',
    [
        SfdPrivateEntry('', b'[]'),
        SfdPrivateEntry('a b', b'[]'),
        SfdPrivateEntry('汉字', b'[]'),
        SfdPrivateEntry('Custom', b'\0'),
        SfdPrivateEntry('Custom', b'\\\n'),
        SfdPrivateEntry('Custom', b'last\\'),
    ],
)
def test_unrepresentable_private_entries_rejected(entry):
    with pytest.raises(SfdValidationError):
        SfdPrivateDict([entry]).to_record()


def test_short_table_word_names_and_copy_semantics():
    words = [SfdShortTableWord(-32768, '竖笔画 😀'), SfdShortTableWord(65535), SfdShortTableWord(0, '')]
    value = SfdShortTable(words=words)
    assert value.words is words
    assert SfdShortTable.from_record(value.to_record()) == value
    assert value.copy().words is words
    assert value.deepcopy().words[0] is not words[0]
    assert value.deepcopy() == value
    assert SfdShortTableWord(1, 'a').copy() == SfdShortTableWord(1, 'a')


@pytest.mark.parametrize(
    'value',
    [
        SfdShortTable('bad'),
        SfdShortTable(' cvt'),
        SfdShortTable('汉字ab'),
        SfdShortTable('a\nbc'),
        SfdShortTable(words=[SfdShortTableWord(-32769)]),
        SfdShortTable(words=[SfdShortTableWord(65536)]),
        SfdShortTable('maxp', [SfdShortTableWord(1, 'forbidden')]),
    ],
)
def test_invalid_short_tables_rejected(value):
    with pytest.raises(SfdValidationError):
        value.to_record()


@pytest.mark.parametrize('name', ['Ambrosia.sfd', 'AmbrosiaItalic.sfd', 'ItalicHand.sfd', 'Hinting.sfd'])
def test_upstream_private_dictionary_value_edit(assets_dir, name):
    font = SfdFont.load(assets_dir.joinpath('fontforge', name))
    index = next(i for i, item in enumerate(font.metadata.records) if item.keyword == 'BeginPrivate:')
    value = SfdPrivateDict.from_record(font.metadata.records[index])
    value.entries[0].value = b'  [10 20]  '
    font.metadata.records[index] = value.to_record()
    assert SfdFont.parse(font.dump_to_bytes()) == font
    value.entries[0].key = 'Changed'
    font.metadata.records[index] = value.to_record()
    with pytest.raises(SfdValidationError, match='uninterpreted'):
        font.dump_to_bytes()


def test_short_table_preserves_word_indices_and_outlines(assets_dir):
    table = SfdShortTable(words=[SfdShortTableWord(10, 'stem'), SfdShortTableWord(20)])
    source = assets_dir.joinpath('fontforge', 'Ambrosia.sfd').read_bytes()
    source = source.replace(b'BeginChars:', b'ShortTable: ' + table.to_record().value + b'\nBeginChars:', 1)
    font = SfdFont.parse(source)
    index = next(i for i, item in enumerate(font.metadata.records) if item.keyword == 'ShortTable:')
    value = SfdShortTable.from_record(font.metadata.records[index])
    value.words[0].value += 2
    value.words[0].name = 'new name'
    font.metadata.records[index] = value.to_record()
    assert SfdFont.parse(font.dump_to_bytes()) == font
    modified = font.deepcopy()
    modified.glyphs[0].layers[0].contours[0].points[0].x += 1
    with pytest.raises(SfdValidationError, match='uninterpreted'):
        modified.dump_to_bytes()
    value.words.append(SfdShortTableWord())
    font.metadata.records[index] = value.to_record()
    with pytest.raises(SfdValidationError, match='uninterpreted'):
        font.dump_to_bytes()


def test_text_models_reject_wrong_kind_or_trailing_data():
    for model in (SfdPrivateDict(), SfdShortTable()):
        with pytest.raises(SfdParseError):
            model.from_record(SfdRecord('Unknown:', model.to_record().value))
        item = model.to_record()
        item.value += b'\nInjected:'
        with pytest.raises(SfdParseError):
            model.from_record(item)
    font = SfdFont()
    font.metadata.records.append(SfdRecord('BeginPrivate:', b'1\nEndPrivate'))
    with pytest.raises(SfdValidationError):
        font.validate()
