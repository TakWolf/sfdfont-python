from examples import BUILD_DIR
from sfdfont import SfdDesignSize, SfdFont, SfdGlyph, SfdTexData, SfdTexMetrics


def main() -> None:
    font = SfdFont(
        glyphs=[
            SfdGlyph('A', encoding=65, unicode=65, width=600, records=[SfdTexMetrics(700, 20).to_record()]),
        ]
    )
    font.metadata.font_name = 'TexExample'
    data = SfdTexData(kind=1, design_size=12 << 20)
    data.parameters[1] = 1 << 19
    font.metadata.records.extend([SfdDesignSize(120).to_record(), data.to_record()])
    outputs_dir = BUILD_DIR.joinpath('create_tex')
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_path = outputs_dir.joinpath('tex.sfd')
    font.save(output_path)
    print(output_path)


if __name__ == '__main__':
    main()
