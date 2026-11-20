from examples import BUILD_DIR
from sfdfont import SfdFont, SfdFontMetric, SfdSfntRevision


def main() -> None:
    font = SfdFont()
    font.metadata.font_name = 'HeaderExample'
    font.metadata.version = '001.500'
    font.metadata.records.append(SfdSfntRevision(0x00018000).to_record())
    for keyword, value in {
        'CreationTime:': 1234567890,
        'ModificationTime:': 1234567890,
        'UniqueID:': 1234567,
        'UseUniqueID:': 1,
        'UseXUID:': 0,
        'NeedsXUIDChange:': 0,
    }.items():
        font.metadata.set_metric(SfdFontMetric(keyword, value))
    outputs_dir = BUILD_DIR.joinpath('create_font_header')
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_path = outputs_dir.joinpath('font_header.sfd')
    font.save(output_path)
    print(output_path)


if __name__ == '__main__':
    main()
