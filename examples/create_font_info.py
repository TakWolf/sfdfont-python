from examples import BUILD_DIR
from sfdfont import SfdFont, SfdGaspRange, SfdGaspTable


def main() -> None:
    font = SfdFont()
    font.metadata.font_name = 'FontInfoExample'
    font.metadata.records.append(SfdGaspTable([SfdGaspRange(8, 2), SfdGaspRange(65535, 3)]).to_record())
    outputs_dir = BUILD_DIR.joinpath('create_font_info')
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_path = outputs_dir.joinpath('font_info.sfd')
    font.save(output_path)
    print(output_path)


if __name__ == '__main__':
    main()
