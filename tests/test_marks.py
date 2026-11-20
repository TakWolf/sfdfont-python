import pytest

from sfdfont import (
    SfdFont,
    SfdGlyph,
    SfdLookup,
    SfdMarkClasses,
    SfdMarkGroup,
    SfdMarkSets,
    SfdParseError,
    SfdRecord,
    SfdValidationError,
)
from sfdfont._parser import record
from sfdfont._reader import Reader
from sfdfont._writer import records


def read_record(data):
    reader = Reader(data)
    item = record(reader, reader.word())
    assert reader.word() == 'Next:'
    return item


def test_mark_classes_and_sets_use_different_index_origins():
    classes = read_record(b'MarkAttachClasses: 2\n"above" 3 A B\nNext: value\n')
    sets = read_record(b'MarkAttachSets: 2\n"above" 1 A\n"below" 1 B\nNext: value\n')
    assert SfdMarkClasses.from_record(classes).classes == [SfdMarkGroup('above', ['A', 'B'])]
    assert len(SfdMarkSets.from_record(sets).sets) == 2
    for item, factory in [(classes, SfdMarkClasses), (sets, SfdMarkSets)]:
        model = factory.from_record(item)
        assert factory.from_record(model.to_record()) == model
        assert read_record(records([item]) + b'Next: value\n') == item


def test_empty_groups_and_utf8_member_lengths():
    for factory, field in [(SfdMarkClasses, 'classes'), (SfdMarkSets, 'sets')]:
        groups = [SfdMarkGroup('中文😀', ['字形']), SfdMarkGroup('', [])]
        model = factory(groups)
        item = model.to_record()
        assert '6 字形'.encode() in item.value
        assert getattr(factory.from_record(item), field) == groups
        assert read_record(records([item]) + b'Next: value\n') == item
    assert SfdMarkClasses.from_record(SfdMarkClasses().to_record()).classes == []
    assert SfdMarkSets.from_record(SfdMarkSets().to_record()).sets == []
    assert SfdMarkSets().sets is not SfdMarkSets().sets
    groups = []
    assert SfdMarkClasses(groups).classes is groups


def test_counted_member_whitespace_is_not_trimmed():
    item = read_record(b'MarkAttachClasses: 2\n"above" 4 A B \nNext: value\n')
    assert item.value.endswith(b'A B ')
    assert read_record(records([item]) + b'Next: value\n') == item


@pytest.mark.parametrize(
    'data',
    [
        b'MarkAttachClasses: 0\n',
        b'MarkAttachClasses: 2\n"above" 6 A B\n',
        b'MarkAttachSets: 2\n"above" 1 A\n',
        b'MarkAttachSets: -1\n',
    ],
)
def test_malformed_mark_blocks(data):
    reader = Reader(data)
    with pytest.raises(SfdParseError):
        record(reader, reader.word())


def marked_font():
    font = SfdFont(glyphs=[SfdGlyph('A'), SfdGlyph('B', 1)])
    font.metadata.records.extend(
        [
            SfdMarkClasses([SfdMarkGroup('above', ['A'])]).to_record(),
            SfdMarkSets([SfdMarkGroup('marks', ['A', 'B'])]).to_record(),
        ]
    )
    font.set_lookup(SfdLookup(1, 'class-filter', flags=0x100))
    font.set_lookup(SfdLookup(1, 'set-filter', flags=0x10))
    return font


def test_mark_flag_indices_and_membership_validation():
    font = marked_font()
    font.validate()
    lookup = font.find_lookup('class-filter')
    lookup.flags = 0x200
    font.set_lookup(lookup)
    with pytest.raises(SfdValidationError, match='class index 2'):
        font.validate()
    lookup.flags = 0
    font.set_lookup(lookup)
    lookup = font.find_lookup('set-filter')
    lookup.flags = 0x10010
    font.set_lookup(lookup)
    with pytest.raises(SfdValidationError, match='set index 1'):
        font.validate()
    lookup.flags = 0x10000  # Inactive high bits do not select a filtering set.
    font.set_lookup(lookup)
    font.validate()
    font.metadata.records[1] = SfdMarkSets([SfdMarkGroup('marks', ['missing'])]).to_record()
    with pytest.raises(SfdValidationError, match='unknown glyph'):
        font.validate()


def test_classes_are_disjoint_but_sets_can_overlap():
    font = marked_font()
    font.metadata.records[0] = SfdMarkClasses([SfdMarkGroup('one', ['A']), SfdMarkGroup('two', ['A'])]).to_record()
    with pytest.raises(SfdValidationError, match='multiple mark attachment classes'):
        font.validate()
    font.metadata.records[0] = SfdMarkClasses([SfdMarkGroup('one', ['A'])]).to_record()
    font.metadata.records[1] = SfdMarkSets([SfdMarkGroup('one', ['A']), SfdMarkGroup('two', ['A'])]).to_record()
    font.validate()
    font.metadata.records.append(font.metadata.records[1].deepcopy())
    with pytest.raises(SfdValidationError, match='duplicate MarkAttachSets'):
        font.validate()


def test_mark_table_scope():
    font = marked_font()
    font.glyphs[0].records.append(SfdRecord('MarkAttachSets:', b'0'))
    with pytest.raises(SfdValidationError, match='layout record in glyph'):
        font.validate()


def test_edit_upstream_mark_members_with_other_records_retained(assets_dir, tmp_path):
    data = assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd').read_bytes()
    font = SfdFont.parse(data.replace(b'BeginChars:', b'MarkAttachSets: 1\n"marks" 8 NameMe.0\nBeginChars:', 1))
    index = next(i for i, item in enumerate(font.metadata.records) if item.keyword == 'MarkAttachSets:')
    groups = SfdMarkSets.from_record(font.metadata.records[index])
    groups.sets[0].glyphs.append('NameMe.1')
    font.metadata.records[index] = groups.to_record()
    path = tmp_path.joinpath('BoxesAndBounds.sfd')
    font.save(path)
    assert SfdFont.load(path) == font
    groups.sets[0].name = 'changed identity'
    font.metadata.records[index] = groups.to_record()
    with pytest.raises(SfdValidationError, match='uninterpreted'):
        font.save(path)
