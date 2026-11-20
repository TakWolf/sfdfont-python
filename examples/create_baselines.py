from examples import BUILD_DIR
from sfdfont import SfdBaselineExtent, SfdBaselines, SfdBaselineScript, SfdFont


def main() -> None:
    font = SfdFont()
    font.metadata.font_name = 'BaselineExample'
    baselines = SfdBaselines(
        tags=['romn', 'ideo'],
        scripts=[
            SfdBaselineScript(
                'latn',
                default_baseline=0,
                positions=[0, -120],
                extents=[
                    SfdBaselineExtent(None, -200, 800),
                    SfdBaselineExtent('kern', -150, 750, depth=1),
                ],
            )
        ],
    )
    font.metadata.records.append(baselines.to_record())
    outputs_dir = BUILD_DIR.joinpath('create_baselines')
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_path = outputs_dir.joinpath('baselines.sfd')
    font.save(output_path)
    print(output_path)


if __name__ == '__main__':
    main()
