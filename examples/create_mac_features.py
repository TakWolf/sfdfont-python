from examples import BUILD_DIR
from sfdfont import SfdFont, SfdMacFeature, SfdMacFeatures, SfdMacName, SfdMacSetting


def main() -> None:
    font = SfdFont()
    font.metadata.font_name = 'MacFeatureExample'
    features = SfdMacFeatures(
        [
            SfdMacFeature(
                feature=1,
                is_mutex=True,
                default_setting=0,
                names=[SfdMacName(0, 0, b'Ligatures')],
                settings=[
                    SfdMacSetting(0, [SfdMacName(0, 0, b'Off')]),
                    SfdMacSetting(1, [SfdMacName(0, 0, b'On')]),
                ],
            ),
        ]
    )
    font.metadata.records.append(features.to_record())
    outputs_dir = BUILD_DIR.joinpath('create_mac_features')
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_path = outputs_dir.joinpath('mac_features.sfd')
    font.save(output_path)
    print(output_path)


if __name__ == '__main__':
    main()
