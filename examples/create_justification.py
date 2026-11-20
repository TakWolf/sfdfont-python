from examples import BUILD_DIR
from sfdfont import (
    SfdFont,
    SfdGlyph,
    SfdJustification,
    SfdJustificationLanguage,
    SfdJustificationPriority,
    SfdJustificationScript,
    SfdLookup,
    SfdLookupSubtable,
    SfdPosition,
    SfdPositionValue,
)


def main() -> None:
    font = SfdFont(glyphs=[SfdGlyph('A', encoding=65, unicode=65, width=600)])
    font.metadata.font_name = 'JustificationExample'
    font.set_lookup(SfdLookup(257, 'expand', subtables=[SfdLookupSubtable('expand-subtable')]))
    font.glyphs[0].records.append(SfdPosition('expand-subtable', SfdPositionValue(x_advance=20)).to_record())
    justification = SfdJustification(
        [
            SfdJustificationScript(
                'latn',
                ['A'],
                [
                    SfdJustificationLanguage('dflt', [SfdJustificationPriority(max_extend=['expand'])]),
                ],
            ),
        ]
    )
    font.metadata.records.append(justification.to_record())
    outputs_dir = BUILD_DIR.joinpath('create_justification')
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_path = outputs_dir.joinpath('justification.sfd')
    font.save(output_path)
    print(output_path)


if __name__ == '__main__':
    main()
