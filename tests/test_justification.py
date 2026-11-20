import pytest

from sfdfont import (
    SfdFont,
    SfdJustification,
    SfdJustificationLanguage,
    SfdJustificationPriority,
    SfdJustificationScript,
    SfdLookup,
    SfdParseError,
    SfdRecord,
    SfdValidationError,
)


def justification():
    return SfdJustification(
        [
            SfdJustificationScript(
                'latn',
                ['Eth'],
                [
                    SfdJustificationLanguage(
                        'dflt',
                        [
                            SfdJustificationPriority(enable_shrink=['substitution'], max_extend=['position']),
                        ],
                    )
                ],
            ),
            SfdJustificationScript('grek', [], [SfdJustificationLanguage('ELL ', [])]),
        ]
    )


def test_justification_models_preserve_omitted_and_empty_fields():
    value = justification()
    value.scripts[0].languages[0].priorities[0].disable_extend = []
    assert SfdJustification.from_record(value.to_record()) == value
    assert value.copy().scripts is value.scripts
    assert value.deepcopy() == value
    assert value.deepcopy().scripts[0].languages[0].priorities[0] is not value.scripts[0].languages[0].priorities[0]
    names = []
    assert SfdJustificationPriority(enable_shrink=names).enable_shrink is names
    assert SfdJustification().scripts is not SfdJustification().scripts


@pytest.mark.parametrize(
    'field',
    [
        'enable_shrink',
        'disable_shrink',
        'max_shrink',
        'enable_extend',
        'disable_extend',
        'max_extend',
    ],
)
def test_all_justification_actions_and_utf7_names(field):
    priority = SfdJustificationPriority()
    setattr(priority, field, ['position 中文 😀', 'second'])
    value = SfdJustification([SfdJustificationScript(languages=[SfdJustificationLanguage(priorities=[priority])])])
    assert SfdJustification.from_record(value.to_record()) == value


@pytest.mark.parametrize(
    'data',
    [
        b"'latn'\nJstfLang: 'dflt' 2\nJstfPrio:\nEndJustify",
        b"'latn'\nJstfLang: 'dflt' 0\nJstfPrio:\nEndJustify",
        b'\'latn\'\nJstfMaxShrink: "position"\nEndJustify',
        b'\'latn\'\nJstfLang: \'dflt\' 1\nJstfPrio:\nJstfMaxShrink: "a"\nJstfMaxShrink: "b"\nEndJustify',
        b"'latn'\nJstfExtender: Eth\nJstfExtender: A\nEndJustify",
        b"'latn'\nJstfLang: 'dflt' 0\nJstfExtender: Eth\nEndJustify",
        b"'latn'\nJstfLang: 'dflt' 0\nJstfLang: 'dflt' 0\nEndJustify",
        b"'latn'\nJustify: 'latn'\nEndJustify",
        b"'latn'\nJstfLang: 'dflt' 1\nJstfPrio: unexpected\nEndJustify",
        b"'latn'\nEndJustify\nInjected:",
        b"'latn'",
    ],
)
def test_invalid_justification_records(data):
    with pytest.raises(SfdParseError):
        SfdJustification.from_record(SfdRecord('Justify:', data))


def test_empty_justification_table_is_not_representable():
    with pytest.raises(SfdValidationError):
        SfdJustification().to_record()
    with pytest.raises(SfdParseError):
        SfdJustification.from_record(SfdRecord('Unknown:', b"'latn'\nEndJustify"))


def prepared_font(assets_dir):
    font = SfdFont.load(assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd'))
    source = font.dump_to_bytes()
    value = justification()
    value.scripts[0].extenders = [font.glyphs[0].name]
    records = [
        SfdLookup(1, 'substitution').to_record(),
        SfdLookup(257, 'position').to_record(),
        value.to_record(),
    ]
    data = b''.join(item.keyword.encode() + b' ' + item.value + b'\n' for item in records)
    return SfdFont.parse(source.replace(b'BeginChars:', data + b'BeginChars:', 1))


def test_justification_edits_validate_dependencies_and_preserve_tags(assets_dir):
    font = prepared_font(assets_dir)
    index = next(i for i, item in enumerate(font.metadata.records) if item.keyword == 'Justify:')
    value = SfdJustification.from_record(font.metadata.records[index])
    priority = value.scripts[0].languages[0].priorities[0]
    priority.max_shrink = ['position']
    value.scripts[0].extenders = [font.glyphs[1].name]
    value.scripts[0].languages[0].priorities.append(SfdJustificationPriority())
    font.metadata.records[index] = value.to_record()
    assert SfdFont.parse(font.dump_to_bytes()) == font
    priority.max_shrink = ['missing']
    font.metadata.records[index] = value.to_record()
    with pytest.raises(SfdValidationError, match='undefined JSTF'):
        font.validate()
    priority.max_shrink = ['position']
    value.scripts[0].tag = 'arab'
    font.metadata.records[index] = value.to_record()
    with pytest.raises(SfdValidationError, match='uninterpreted'):
        font.dump_to_bytes()


@pytest.mark.parametrize('kind', [1, 253, 511])
def test_jstf_maximum_requires_opentype_positioning(kind):
    font = SfdFont()
    font.set_lookup(SfdLookup(kind, 'maximum'))
    value = SfdJustification(
        [
            SfdJustificationScript(
                languages=[
                    SfdJustificationLanguage(
                        priorities=[
                            SfdJustificationPriority(max_extend=['maximum']),
                        ]
                    )
                ]
            )
        ]
    )
    font.metadata.records.append(value.to_record())
    with pytest.raises(SfdValidationError, match='GPOS'):
        font.validate()


def test_duplicate_justification_tables(assets_dir):
    font = prepared_font(assets_dir)
    item = next(item for item in font.metadata.records if item.keyword == 'Justify:')
    font.metadata.records.append(item.copy())
    with pytest.raises(SfdValidationError, match='duplicate JSTF'):
        font.validate()
