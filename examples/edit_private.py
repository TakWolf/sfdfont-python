from examples import ASSETS_DIR, BUILD_DIR
from sfdfont import SfdFont, SfdPrivateDict


def main() -> None:
    font = SfdFont.load(ASSETS_DIR.joinpath('fontforge', 'Ambrosia.sfd'))
    for index, record in enumerate(font.metadata.records):
        if record.keyword == 'BeginPrivate:':
            private = SfdPrivateDict.from_record(record)
            for entry in private.entries:
                if entry.key == 'BlueValues':
                    entry.value = b'[-20 0 502 517 750 768]'
                    font.metadata.records[index] = private.to_record()
                    outputs_dir = BUILD_DIR.joinpath('edit_private')
                    outputs_dir.mkdir(parents=True, exist_ok=True)
                    output_path = outputs_dir.joinpath('Ambrosia.sfd')
                    font.save(output_path)
                    print(output_path)
                    return
    raise ValueError('The example font has no BlueValues entry')


if __name__ == '__main__':
    main()
