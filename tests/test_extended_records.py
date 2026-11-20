import pytest

from sfdfont import (
    SfdFont,
    SfdGlyph,
    SfdLookup,
    SfdLookupSubtable,
    SfdParseError,
    SfdRecord,
    SfdStateMachine,
    SfdValidationError,
)
from sfdfont._parser import record
from sfdfont._reader import Reader
from sfdfont._writer import records


def parse_record(data):
    reader = Reader(data)
    result = record(reader, reader.word())
    assert not reader.word()
    return result


@pytest.mark.parametrize(
    'kind, action', [('Indic', b''), ('Context', b' ~ "single"'), ('Insert', b' 3 A B 0'), ('Kern', b' 2 -20 10')]
)
def test_aat_state_matrix(kind, action):
    data = f'Mac{kind}2: "state" 0 4 2\n'.encode() + (b'0 0' + action + b'\n') * 8 + b'EndASM\n'
    parsed = parse_record(data)
    machine = SfdStateMachine.from_record(parsed)
    assert machine.classes == [None] * 4
    assert len(machine.states) == 2
    assert SfdStateMachine.from_record(machine.to_record()) == machine
    assert machine.copy().states is machine.states
    assert machine.deepcopy().states is not machine.states
    assert records([parsed])


def test_legacy_aat_features_and_class_lengths():
    parsed = parse_record(b'MacContext: 1,2 0 5 2\nClass: 3 A B\n' + b"0 0 'test' ~\n" * 10 + b'EndASM\n')
    machine = SfdStateMachine.from_record(parsed)
    assert (machine.feature, machine.setting, machine.classes[4]) == (1, 2, ['A', 'B'])
    assert SfdStateMachine.from_record(machine.to_record()) == machine
    with pytest.raises(SfdParseError):
        parse_record(b'MacIndic2: "state" 0 4 2\n' + b'2 0\n' * 8 + b'EndASM\n')
    with pytest.raises(SfdParseError):
        parse_record(b'MacIndic2: "state" 0 4 2\n0 0\nEndASM\n')


def test_aat_lookup_dependencies_and_cycles():
    font = SfdFont(glyphs=[SfdGlyph('A')])
    font.set_lookup(SfdLookup(254, 'context', subtables=[SfdLookupSubtable('state')]))
    font.set_lookup(SfdLookup(1, 'single'))
    machine = SfdStateMachine.from_record(
        parse_record(b'MacContext2: "state" 0 4 2\n' + b'0 0 ~ "single"\n' * 8 + b'EndASM\n')
    )
    font.metadata.records.append(machine.to_record())
    font.validate()
    machine.states[0][0].current_lookup = 'context'
    font.metadata.records[-1] = machine.to_record()
    with pytest.raises(SfdValidationError, match='cyclic'):
        font.validate()
    machine.states[0][0].current_lookup = 'missing'
    font.metadata.records[-1] = machine.to_record()
    with pytest.raises(SfdValidationError, match='undefined nested AAT'):
        font.validate()


def test_baselines_math_and_mac_feature_boundaries():
    values = [
        b"BaseHoriz: 1 'romn'\nBaseScript: 'latn' 0 10 { 'dflt' -200 800 { 'kern' -100 700}}\n",
        b'MATH:AxisHeight: 250 {12-13 1,-1}\n',
        b'MacFeat: 1 1 0\nMacName: 0 0 7 "Regular"\nMacSetting: 0\nMacName: 0 1 1 "\\217"\nEndMacFeatures\n',
    ]
    for data in values:
        parsed = parse_record(data)
        assert records([parsed])
    with pytest.raises(SfdParseError, match='unclosed'):
        parse_record(values[0].replace(b'}}', b'}'))
    with pytest.raises(SfdParseError, match='expected'):
        parse_record(values[1].replace(b'1,-1', b'1'))
    with pytest.raises(SfdParseError, match='requires a name'):
        parse_record(b'MacFeat: 1 1 0\nEndMacFeatures\n')


def test_jstf_counts_and_dependencies():
    data = b"Justify: 'latn'\nJstfExtender: A\nJstfLang: 'dflt' 1\nJstfPrio:\nJstfMaxShrink: \"position\"\nEndJustify\n"
    parsed = parse_record(data)
    assert records([parsed])
    font = SfdFont(glyphs=[SfdGlyph('A')])
    font.metadata.records.append(parsed)
    with pytest.raises(SfdValidationError, match='undefined JSTF'):
        font.validate()
    font.set_lookup(SfdLookup(257, 'position'))
    font.validate()
    with pytest.raises(SfdParseError, match='priority count'):
        parse_record(data.replace(b"'dflt' 1", b"'dflt' 2"))
    font.glyphs[0].records.append(SfdRecord('MATH:AxisHeight:', b'250'))
    with pytest.raises(SfdValidationError, match='record in glyph'):
        font.validate()
