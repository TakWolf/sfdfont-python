from examples import BUILD_DIR
from sfdfont import SfdFont, SfdFontMetric, SfdWoffMetadata


def main() -> None:
    font = SfdFont()
    font.metadata.font_name = 'WoffMetadataExample'
    font.metadata.set_metric(SfdFontMetric('woffMajor:', 1))
    font.metadata.set_metric(SfdFontMetric('woffMinor:', 2))
    font.metadata.records.append(
        SfdWoffMetadata(
            '<metadata version="1.0">\n'
            '  <description><text lang="en">Example font</text>'
            '<text lang="zh">示例字体 😀</text></description>\n'
            '</metadata>'
        ).to_record()
    )
    outputs_dir = BUILD_DIR.joinpath('create_woff_metadata')
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_path = outputs_dir.joinpath('woff_metadata.sfd')
    font.save(output_path)
    print(output_path)


if __name__ == '__main__':
    main()
