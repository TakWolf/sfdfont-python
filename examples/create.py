import shutil

from examples import BUILD_DIR
from sfdfont import SfdContour, SfdFont, SfdGlyph, SfdLayer, SfdPoint


def main() -> None:
    outputs_dir = BUILD_DIR.joinpath('create')
    if outputs_dir.exists():
        shutil.rmtree(outputs_dir)
    outputs_dir.mkdir(parents=True)

    font = SfdFont()

    font.metadata.font_name = 'Example'
    font.metadata.family_name = 'Example'
    font.metadata.full_name = 'Example Regular'
    font.metadata.comments = 'Created with sfdfont. 中文与 emoji 😀'

    font.glyphs.append(
        SfdGlyph(
            name='A',
            glyph_id=0,
            encoding=65,
            unicode=65,
            width=600,
            layers=[
                SfdLayer(
                    index=1,
                    contours=[
                        SfdContour(
                            [
                                SfdPoint(0, 0),
                                SfdPoint(300, 700, 'l'),
                                SfdPoint(600, 0, 'l'),
                                SfdPoint(0, 0, 'l'),
                            ]
                        )
                    ],
                )
            ],
        )
    )

    font.save(outputs_dir.joinpath('example.sfd'))


if __name__ == '__main__':
    main()
