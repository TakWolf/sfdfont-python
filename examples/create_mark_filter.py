from examples import BUILD_DIR
from sfdfont import (
    SfdFont,
    SfdGlyph,
    SfdLookup,
    SfdLookupFeature,
    SfdLookupSubtable,
    SfdMarkClasses,
    SfdMarkGroup,
    SfdMarkSets,
    SfdRecord,
    SfdSubstitution,
)


def main() -> None:
    font = SfdFont()
    font.metadata.font_name = 'MarkFilterExample'
    font.glyphs = [
        SfdGlyph('acutecomb', 0, 0x0301, 0x0301, 0, records=[SfdRecord('GlyphClass:', b'3')]),
        SfdGlyph('gravecomb', 1, 0x0300, 0x0300, 0, records=[SfdRecord('GlyphClass:', b'3')]),
    ]
    font.metadata.records.extend(
        [
            SfdMarkClasses([SfdMarkGroup('above', ['acutecomb', 'gravecomb'])]).to_record(),
            SfdMarkSets([SfdMarkGroup('acute-only', ['acutecomb'])]).to_record(),
        ]
    )
    font.set_lookup(
        SfdLookup(
            1,
            'filtered-substitution',
            flags=0x10,  # Enable filtering set 0.
            subtables=[SfdLookupSubtable('filtered-subtable')],
            features=[SfdLookupFeature('ccmp', {'latn': ['dflt']})],
        )
    )
    font.glyphs[0].records.append(
        SfdSubstitution('Substitution2:', 'filtered-subtable', ['gravecomb']).to_record(),
    )
    outputs_dir = BUILD_DIR.joinpath('create_mark_filter')
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_path = outputs_dir.joinpath('mark_filter.sfd')
    font.save(output_path)
    print(output_path)


if __name__ == '__main__':
    main()
