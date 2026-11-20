from examples import ASSETS_DIR, BUILD_DIR
from sfdfont import (
    SfdFont,
    SfdGlyphAssembly,
    SfdGlyphPart,
    SfdGlyphVariants,
    SfdMathKern,
    SfdMathKernEntry,
    SfdMathValue,
)


def main() -> None:
    font = SfdFont.load(ASSETS_DIR.joinpath('fontforge', 'BoxesAndBounds.sfd'))
    glyph, variant, extender = font.glyphs[:3]
    font.metadata.records.append(SfdMathValue('MATH:AxisHeight:', 250).to_record())
    glyph.records.extend(
        [
            SfdMathValue('ItalicCorrection:', 20).to_record(),
            SfdGlyphVariants(glyphs=[variant.name, extender.name]).to_record(),
            SfdGlyphAssembly(
                parts=[
                    SfdGlyphPart(variant.name, False, 0, 20, 100),
                    SfdGlyphPart(extender.name, True, 20, 20, 80),
                ]
            ).to_record(),
            SfdMathKern(entries=[SfdMathKernEntry(100, -10), SfdMathKernEntry(0, -20)]).to_record(),
        ]
    )

    outputs_dir = BUILD_DIR.joinpath('edit_math')
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_path = outputs_dir.joinpath('BoxesAndBounds.sfd')
    font.save(output_path)
    print(output_path)


if __name__ == '__main__':
    main()
