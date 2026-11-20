from examples import BUILD_DIR
from sfdfont import SfdFont, SfdGlyph, SfdGlyphGroup, SfdGroupKerningPair


def main() -> None:
    font = SfdFont(
        glyphs=[
            SfdGlyph('A', glyph_id=0, encoding=65, unicode=65, width=600),
            SfdGlyph('V', glyph_id=1, encoding=86, unicode=86, width=600),
        ]
    )
    font.metadata.font_name = 'GroupExample'
    font.metadata.records.extend(
        [
            SfdGlyphGroup('public.kern1.A', ['A']).to_record(),
            SfdGlyphGroup('public.kern2.V', ['V']).to_record(),
            SfdGroupKerningPair(left='public.kern1.A', right='public.kern2.V', offset=-80).to_record(),
            SfdGroupKerningPair('GroupVKern:', 'A', 'V', -20).to_record(),
        ]
    )
    outputs_dir = BUILD_DIR.joinpath('create_groups')
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_path = outputs_dir.joinpath('groups.sfd')
    font.save(output_path)
    print(output_path)


if __name__ == '__main__':
    main()
