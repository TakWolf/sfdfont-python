from examples import BUILD_DIR
from sfdfont import SfdFont, SfdFontText


def main() -> None:
    font = SfdFont()
    font.metadata.font_name = 'FontTextExample'
    font.metadata.set_text(SfdFontText('FONDName:', 'Example Family'))
    font.metadata.set_text(SfdFontText('DefaultBaseFilename:', 'Example-Regular'))
    font.metadata.set_text(SfdFontText('XUID:', '[1021 0 1]'))

    name = font.metadata.find_text('FONDName:')
    name.text = 'Edited Family'
    font.metadata.set_text(name)

    outputs_dir = BUILD_DIR.joinpath('create_font_text')
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_path = outputs_dir.joinpath('font_text.sfd')
    font.save(output_path)
    print(output_path)


if __name__ == '__main__':
    main()
