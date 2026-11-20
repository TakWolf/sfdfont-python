from examples import BUILD_DIR
from sfdfont import SfdFont, SfdLanguageNames, SfdStyleMapName


def main() -> None:
    font = SfdFont()
    font.metadata.font_name = 'LegacyNameExample'
    font.metadata.language_names.append(
        SfdLanguageNames(
            language=0x0409,
            names=['Copyright (c) Example'],
            style_map_family_names=[SfdStyleMapName('StyleMapFamilyName:', 'Legacy Family')],
        )
    )
    font.metadata.records.append(SfdStyleMapName('OS2StyleName:', 'bold italic').to_record())
    outputs_dir = BUILD_DIR.joinpath('create_legacy_names')
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_path = outputs_dir.joinpath('legacy_names.sfd')
    font.save(output_path)
    print(output_path)


if __name__ == '__main__':
    main()
