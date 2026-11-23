import pytest

from sfdfont import (
    SfdAxisMap,
    SfdCidInfo,
    SfdContour,
    SfdFont,
    SfdGlyph,
    SfdLayer,
    SfdMultipleMaster,
    SfdPoint,
    SfdRecord,
    SfdValidationError,
)


def family_font(kind, opaque_scope):
    child = SfdFont(
        glyphs=[
            SfdGlyph(
                'A',
                0,
                65,
                65,
                layers=[
                    SfdLayer(1, [SfdContour([SfdPoint(0, 0), SfdPoint(10, 0, 'l')])]),
                ],
            )
        ]
    )
    font = SfdFont()
    if kind == 'cid':
        font.cid = SfdCidInfo()
        font.subfonts = [child]
    else:
        font.glyphs = [glyph.deepcopy() for glyph in child.glyphs]
        font.multiple_master = SfdMultipleMaster(
            axes=['Weight'],
            positions=[[0]],
            weights=[1],
            axis_maps=[SfdAxisMap()],
            instances=[child],
        )
    if opaque_scope in ('root', 'both'):
        font.metadata.records.append(SfdRecord('Unknown:', b'root dependency'))
    if opaque_scope in ('child', 'both'):
        child.metadata.records.append(SfdRecord('Unknown:', b'child dependency'))
    return SfdFont.parse(font.dump_to_bytes())


def family_child(font):
    return font.subfonts[0] if font.subfonts else font.multiple_master.instances[0]


@pytest.mark.parametrize('kind', ['cid', 'mm'])
@pytest.mark.parametrize('scope', ['root', 'child', 'both'])
@pytest.mark.parametrize('change', ['outline', 'unicode', 'layer', 'alias'])
def test_retained_family_dependencies_protect_child_structure(tmp_path, kind, scope, change):
    font = family_font(kind, scope)
    child = family_child(font)
    if change == 'outline':
        child.glyphs[0].layers[0].contours[0].points[0].x += 1
    elif change == 'unicode':
        child.glyphs[0].unicode = 66
    elif change == 'layer':
        child.layer_infos[1].quadratic = True
    else:
        child.encoding_aliases[66] = 0
    path = tmp_path.joinpath('keep.sfd')
    path.write_bytes(b'keep')
    with pytest.raises(SfdValidationError, match='uninterpreted'):
        font.save(path)
    assert path.read_bytes() == b'keep'


@pytest.mark.parametrize('kind', ['cid', 'mm'])
def test_root_snapshot_protects_new_child_objects(kind):
    font = family_font(kind, 'root')
    # Replacing the child must not discard the container's dependency protection.
    replacement = SfdFont(glyphs=[glyph.deepcopy() for glyph in family_child(font).glyphs])
    replacement.glyphs[0].layers[0].contours[0].points[0].x += 1
    if kind == 'cid':
        font.subfonts[0] = replacement
    else:
        font.multiple_master.instances[0] = replacement
    with pytest.raises(SfdValidationError, match='uninterpreted'):
        font.dump_to_bytes()


@pytest.mark.parametrize('kind', ['cid', 'mm'])
@pytest.mark.parametrize('scope', ['root', 'child', 'both'])
def test_family_dependencies_allow_documented_numeric_and_text_edits(kind, scope):
    font = family_font(kind, scope)
    child = family_child(font)
    child.glyphs[0].width += 1
    child.glyphs[0].flags = 'HW'
    child.metadata.comments = 'edited child'
    child.guidelines = [SfdContour([SfdPoint(20, 30)])]
    font.metadata.comments = 'edited container'
    assert SfdFont.parse(font.dump_to_bytes()) == font


@pytest.mark.parametrize('kind', ['cid', 'mm'])
@pytest.mark.parametrize('scope', ['none', 'root', 'child', 'both'])
def test_explicitly_removing_family_dependencies_permits_geometry_edits(kind, scope):
    font = family_font(kind, scope)
    font.metadata.records.clear()
    child = family_child(font)
    child.metadata.records.clear()
    child.glyphs[0].layers[0].contours[0].points[0].x += 1
    assert SfdFont.parse(font.dump_to_bytes()) == font
