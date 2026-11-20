from examples import ASSETS_DIR, BUILD_DIR
from sfdfont import SfdAnchor, SfdFont


def main() -> None:
    font = SfdFont.load(ASSETS_DIR.joinpath('fontforge', 'DejaVuSerif.sfd'))
    glyph = font.find_glyphs_by_name('A')[0]
    for index, record in enumerate(glyph.records):
        if record.keyword == 'AnchorPoint:':
            anchor = SfdAnchor.from_record(record)
            anchor.y += 20
            glyph.records[index] = anchor.to_record()
            break
    else:
        raise ValueError('The example glyph has no anchor')

    outputs_dir = BUILD_DIR.joinpath('edit_anchors')
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_path = outputs_dir.joinpath('DejaVuSerif.sfd')
    font.save(output_path)
    print(output_path)


if __name__ == '__main__':
    main()
