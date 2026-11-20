# SfdFont - Python

[![Python](https://img.shields.io/badge/python-3.10-brightgreen?style=flat-square)](https://www.python.org)
[![PyPI](https://img.shields.io/pypi/v/sfdfont?style=flat-square)](https://pypi.org/project/sfdfont/)

A pure Python library for [FontForge Spline Font Database (SFD)](https://fontforge.org/docs/techref/sfdformat.html) files.

## Installation

```shell
pip install sfdfont
```

## Usage

### Create

```python
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
```

### Load

```python
from examples import ASSETS_DIR
from sfdfont import SfdFont


def main() -> None:
    font = SfdFont.load(ASSETS_DIR.joinpath('fontforge', 'Ambrosia.sfd'))
    print(font.metadata.font_name, font.version)
    for glyph in font.glyphs:
        print(glyph.glyph_id, glyph.name, glyph.unicode, glyph.width)
    for strike in font.bitmap_strikes:
        print('Bitmap strike:', strike.pixelsize, strike.depth, len(strike.glyphs))


if __name__ == '__main__':
    main()
```

## Supported formats and boundaries

- Core single-font SFD structures in versions 1.0, 2.0, 3.0, 3.1 and 3.2.
- Font names, language names, comments, SFD UTF-7, UTF-8 and legacy text fields.
- Layer definitions, m/l/c operations, point flags, control coordinates, hint masks
  and TrueType point indices. Curve order is defined by the layer, including c
  commands in quadratic layers. Closing endpoints are retained without rewriting.
- Glyph encodings, alternate Unicode/variation mappings, vector references and
  guideline contours.
- Bitmap strikes with 1/2/4/8-bit sample depths, properties and bitmap references.
  Grayscale data uses one byte per sample; monochrome rows use packed bits.
- Old Image and PNG Image2 payloads, TrueType binary tables and instructions are
  retained as bytes. Images are not rendered and instructions are not executed.
- Known terminated text blocks and ordinary additional records are retained without
  interpreting their semantics. Pickled data is retained without unpickling.

CID, Multiple Master, Type 3 multilayer paint data, complex contextual layout and
kerning-class blocks, Spiro, named contours/points and undo/redo blocks are not
implemented. Versions 0/4, sfdir directories and asfd recovery files are not supported.
Unsupported structures raise `SfdUnsupportedError`; malformed structures raise
`SfdParseError`. Accepting a version header does not imply every feature is supported.

Writing normalizes whitespace and numeric formatting; it does not promise
byte-for-byte reproduction. Semantic roundtrips are tested. For loaded fonts that
retain uninterpreted records or payloads, editing followed by writing is rejected
with `SfdValidationError`. Removing such data explicitly permits supported edits;
keep a source copy when that data matters. Fonts built entirely from supported
models can be edited and saved directly.

Duplicate glyph IDs/encoding slots, dangling/cyclic references and inconsistent
bitmap dimensions are rejected. Some historical FontForge files rely on implicit
repair and are therefore rejected. SFD 1.0 glyph counts are treated as historical
capacity hints; later-version counts are checked against the actual glyph count.

`SfdReadLimits` configures document byte, glyph, point and cumulative binary-payload
budgets. Exceeding a budget raises `SfdLimitError`, a subclass of `SfdParseError`.

## Development

```shell
uv sync
uv run -m ruff check --fix
uv run -m ruff format
uv run -m pytest
```

## References

- [FontForge - GitHub](https://github.com/fontforge/fontforge)
- [FontForge - Spline Font Database](https://fontforge.org/docs/techref/sfdformat.html)

## License

[MIT License](LICENSE)
