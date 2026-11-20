from examples import BUILD_DIR
from sfdfont import (
    SfdDesignSize,
    SfdFont,
    SfdFontMetric,
    SfdFontRealMetric,
    SfdGaspRange,
    SfdGaspTable,
    SfdOs2Mask,
    SfdOs2Vendor,
    SfdPanose,
    SfdStyleName,
)


def main() -> None:
    font = SfdFont()
    font.metadata.font_name = 'FontInfoExample'
    font.metadata.records.append(SfdGaspTable([SfdGaspRange(8, 2), SfdGaspRange(65535, 3)]).to_record())
    font.metadata.records.append(
        SfdDesignSize(120, (100, 140), 1, [SfdStyleName(0x0409, 'Text'), SfdStyleName(0x0804, '正文')]).to_record()
    )
    font.metadata.records.extend(
        [
            SfdPanose([2, 0, 6, 3, 0, 0, 0, 0, 0, 0]).to_record(),
            SfdOs2Mask('OS2CodePages:', 1).to_record(),
            SfdOs2Mask('OS2UnicodeRanges:', 1).to_record(),
            SfdOs2Vendor(b'TakW').to_record(),
        ]
    )
    for keyword, value in {
        'PfmFamily:': 17,
        'TTFWeight:': 400,
        'TTFWidth:': 5,
        'OS2TypoAscent:': 800,
        'OS2TypoAOffset:': 0,
        'OS2TypoDescent:': -200,
        'OS2TypoDOffset:': 0,
        'StyleMap:': 0x40,
    }.items():
        font.metadata.set_metric(SfdFontMetric(keyword, value))
    for keyword, value in {
        'ItalicAngle:': -12.5,
        'UnderlinePosition:': -100,
        'UnderlineWidth:': 50,
        'StrokeWidth:': 2.5,
        'UFOAscent:': 800.25,
        'UFODescent:': -200.5,
    }.items():
        font.metadata.set_metric(SfdFontRealMetric(keyword, value))
    outputs_dir = BUILD_DIR.joinpath('create_font_info')
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_path = outputs_dir.joinpath('font_info.sfd')
    font.save(output_path)
    print(output_path)


if __name__ == '__main__':
    main()
