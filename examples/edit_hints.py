from examples import ASSETS_DIR, BUILD_DIR
from sfdfont import SfdFont, SfdStemHints


def main() -> None:
    font = SfdFont.load(ASSETS_DIR.joinpath('fontforge', 'Ambrosia.sfd'))
    for glyph in font.iter_glyphs():
        for records in [glyph.records, *(layer.records for layer in glyph.layers)]:
            for index, record in enumerate(records):
                if record.keyword == 'HStem:':
                    hints = SfdStemHints.from_record(record)
                    if hints.hints:
                        hints.hints[0].start += 1
                        records[index] = hints.to_record()
                        outputs_dir = BUILD_DIR.joinpath('edit_hints')
                        outputs_dir.mkdir(parents=True, exist_ok=True)
                        output_path = outputs_dir.joinpath('Ambrosia.sfd')
                        font.save(output_path)
                        print(glyph.name, output_path)
                        return
    raise ValueError('The example font has no horizontal stem hints')


if __name__ == '__main__':
    main()
