import pytest

from sfdfont import (
    SfdContext,
    SfdContextRule,
    SfdFont,
    SfdKerningClass,
    SfdLookup,
    SfdLookupFeature,
    SfdLookupSubtable,
    SfdRecord,
    SfdValidationError,
)
from sfdfont._layout import CONTEXT_KEYS, KERN_CLASS_KEYS


@pytest.mark.parametrize('filename', ['DejaVuSerif.sfd', 'VKern.sfd', 'NimbusLGCUni-Regular.sfd'])
def test_decode_and_encode_upstream_layout(assets_dir, filename):
    font = SfdFont.load(assets_dir.joinpath('fontforge', filename))
    count = 0
    for record in font.metadata.records:
        if record.keyword in CONTEXT_KEYS:
            model = SfdContext.from_record(record)
            assert SfdContext.from_record(model.to_record()) == model
        elif record.keyword in KERN_CLASS_KEYS:
            model = SfdKerningClass.from_record(record)
            assert SfdKerningClass.from_record(model.to_record()) == model
        else:
            continue
        assert model.copy() == model.deepcopy() == model
        count += 1
    assert count > 0


def test_edit_lookup_values_and_copy():
    lookup = SfdLookup(
        258,
        'Kerning 中文😀',
        subtables=[
            SfdLookupSubtable('pairs', vertical=True, separation=20, minimum_kerning=-30, kerning_flags=7),
        ],
        features=[SfdLookupFeature('kern', {'latn': ['dflt']})],
    )
    decoded = SfdLookup.from_record(lookup.to_record())
    assert decoded == lookup
    copied = lookup.deepcopy()
    copied.flags = 8
    copied.features[0].scripts['latn'].append('TRK ')
    assert copied != lookup
    assert lookup.features[0].scripts['latn'] == ['dflt']
    assert SfdLookup.from_record(copied.to_record()) == copied


def test_edit_legacy_context(assets_dir):
    font = SfdFont.load(assets_dir.joinpath('fontforge', 'DejaVuSerif.sfd'))
    source = next(r for r in font.metadata.records if r.keyword == 'ChainSub:')
    context = SfdContext.from_record(source)
    assert context.input_classes[1] == ['i', 'j']
    context.rules[0].lookups[0].lookup = 'test'
    changed = context.to_record()
    assert b"'test'" in changed.value
    assert b"'test'" not in source.value
    assert SfdContext.from_record(changed) == context


def test_kerning_matrix_shape_rejected():
    kern = SfdKerningClass(first_classes=[None, ['A']], second_classes=[None, ['V']], offsets=[[0, 0], [-80]])
    with pytest.raises(SfdValidationError, match='matrix dimensions'):
        kern.to_record()


def test_context_sequence_out_of_range_rejected():
    context = SfdContext(form='class', subtable='sub', input_classes=[None, ['A']], rules=[SfdContextRule(inputs=[2])])
    with pytest.raises(SfdValidationError):
        context.to_record()


def test_named_kerning_classes_with_implicit_defaults():
    source = SfdRecord('KernClass3:', b'2 2 "kern"\n0\n0\n0 0 0 0 0 0 0 -80')
    kern = SfdKerningClass.from_record(source)
    assert kern.first_names == [None, None]
    # A flag-only row is a valid empty, unnamed class and must remain so.
    assert SfdKerningClass.from_record(kern.to_record()) == kern
