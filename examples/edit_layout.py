from examples import ASSETS_DIR, BUILD_DIR
from sfdfont import SfdFont, SfdKerningClass


def main() -> None:
    font = SfdFont.load(ASSETS_DIR.joinpath('fontforge', 'VKern.sfd'))
    for index, record in enumerate(font.metadata.records):
        if record.keyword in ('VKernClass:', 'VKernClass2:', 'VKernClass3:'):
            kerning = SfdKerningClass.from_record(record)
            kerning.offsets[1][1] -= 10
            font.metadata.records[index] = kerning.to_record()
            break
    else:
        raise ValueError('The example font has no vertical kerning classes')

    outputs_dir = BUILD_DIR.joinpath('edit_layout')
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_path = outputs_dir.joinpath('VKern.sfd')
    font.save(output_path)
    print(output_path)


if __name__ == '__main__':
    main()
