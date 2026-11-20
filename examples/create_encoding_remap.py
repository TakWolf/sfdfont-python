from examples import BUILD_DIR
from sfdfont import SfdEncodingRange, SfdEncodingRemap, SfdFont


def main() -> None:
    font = SfdFont()
    font.metadata.font_name = 'EncodingRemapExample'
    remap = SfdEncodingRemap([SfdEncodingRange(0x1000000, 0x10000FF, 256)])
    font.metadata.records.extend(remap.to_records())

    outputs_dir = BUILD_DIR.joinpath('create_encoding_remap')
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_path = outputs_dir.joinpath('encoding_remap.sfd')
    font.save(output_path)
    print(output_path)


if __name__ == '__main__':
    main()
