from examples import BUILD_DIR
from sfdfont import SfdFeatureName, SfdFeatureNames, SfdFont


def main() -> None:
    font = SfdFont()
    font.metadata.font_name = 'FeatureNameExample'
    font.metadata.records.extend(
        [
            SfdFeatureNames('ss01', [SfdFeatureName(0x0409, 'Round a'), SfdFeatureName(0x0804, '圆形 a')]).to_record(),
            SfdFeatureNames(
                'cv01', [SfdFeatureName(0x0409, 'a style', 'Choose a style', 'a', ['Single storey'])], ''
            ).to_record(),
        ]
    )
    outputs_dir = BUILD_DIR.joinpath('create_feature_names')
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_path = outputs_dir.joinpath('feature_names.sfd')
    font.save(output_path)
    print(output_path)


if __name__ == '__main__':
    main()
