from examples import ASSETS_DIR, BUILD_DIR
from sfdfont import SfdFont


def main() -> None:
    font = SfdFont.load(ASSETS_DIR.joinpath('fontforge', 'Ambrosia.sfd'))
    outputs_dir = BUILD_DIR.joinpath('load_save')
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_path = outputs_dir.joinpath('Ambrosia.sfd')
    font.save(output_path)
    print(output_path)


if __name__ == '__main__':
    main()
