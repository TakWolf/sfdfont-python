from examples import BUILD_DIR
from sfdfont import SfdContour, SfdFont, SfdGlyph, SfdLayer, SfdPoint


def main() -> None:
    font = SfdFont()
    font.metadata.font_name = 'OutlineExample'
    font.metadata.family_name = 'OutlineExample'
    font.metadata.full_name = 'OutlineExample Regular'
    font.metadata.comments = 'Created with sfdfont. 中文与 emoji 😀'
    contour = SfdContour(
        [
            SfdPoint(0, 0),
            SfdPoint(300, 700, 'l'),
            SfdPoint(600, 0, 'l'),
            SfdPoint(0, 0, 'l'),
        ]
    )
    font.glyphs.append(
        SfdGlyph(
            name='A',
            glyph_id=0,
            encoding=65,
            unicode=65,
            width=600,
            layers=[SfdLayer(index=1, contours=[contour])],
        )
    )

    outputs_dir = BUILD_DIR.joinpath('create_outlines')
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_path = outputs_dir.joinpath('outlines.sfd')
    font.save(output_path)
    print(output_path)


if __name__ == '__main__':
    main()
