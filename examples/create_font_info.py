from examples import BUILD_DIR
from sfdfont import SfdDesignSize, SfdFont, SfdGaspRange, SfdGaspTable, SfdStyleName


def main() -> None:
    font = SfdFont()
    font.metadata.font_name = 'FontInfoExample'
    font.metadata.records.append(SfdGaspTable([SfdGaspRange(8, 2), SfdGaspRange(65535, 3)]).to_record())
    font.metadata.records.append(
        SfdDesignSize(120, (100, 140), 1, [SfdStyleName(0x0409, 'Text'), SfdStyleName(0x0804, '正文')]).to_record()
    )
    outputs_dir = BUILD_DIR.joinpath('create_font_info')
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_path = outputs_dir.joinpath('font_info.sfd')
    font.save(output_path)
    print(output_path)


if __name__ == '__main__':
    main()
