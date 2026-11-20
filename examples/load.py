from examples import ASSETS_DIR
from sfdfont import SfdFont


def main() -> None:
    font = SfdFont.load(ASSETS_DIR.joinpath('fontforge', 'Ambrosia.sfd'))
    print(font.metadata.font_name, font.version)
    for glyph in font.iter_glyphs():
        print(glyph.glyph_id, glyph.name, glyph.unicode, glyph.width)
    for strike in font.bitmap_strikes:
        print('Bitmap strike:', strike.pixelsize, strike.depth, len(strike.glyphs))


if __name__ == '__main__':
    main()
