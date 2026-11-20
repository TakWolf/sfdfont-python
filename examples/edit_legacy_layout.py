from examples import ASSETS_DIR, BUILD_DIR
from sfdfont import SfdFont, SfdLegacyKerningPairs, SfdLegacyPst


def main() -> None:
    font = SfdFont.load(ASSETS_DIR.joinpath('fontforge', 'VKern.sfd'))
    for glyph in font.glyphs:
        for group in [glyph.records, *(layer.records for layer in glyph.layers)]:
            for index, record in enumerate(group):
                if record.keyword == 'PairPos:':
                    pair = SfdLegacyPst.from_record(record)
                    pair.positions[0].y_offset += 10
                    group[index] = pair.to_record()
                elif record.keyword in ('KernsSLIF:', 'VKernsSLIF:'):
                    kerning = SfdLegacyKerningPairs.from_record(record)
                    kerning.pairs[0].offset -= 10
                    group[index] = kerning.to_record()

    outputs_dir = BUILD_DIR.joinpath('edit_legacy_layout')
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_path = outputs_dir.joinpath('VKern.sfd')
    font.save(output_path)
    print(output_path)


if __name__ == '__main__':
    main()
