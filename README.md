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
    for glyph in font.iter_glyphs():
        print(glyph.glyph_id, glyph.name, glyph.unicode, glyph.width)
    for strike in font.bitmap_strikes:
        print('Bitmap strike:', strike.pixelsize, strike.depth, len(strike.glyphs))


if __name__ == '__main__':
    main()
```

### Edit layout

```python
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
```

`SfdLookup`, `SfdContext`, `SfdKerningClass` and `SfdStateMachine` provide
`from_record()` / `to_record()` conversions. Decoded objects are independent:
replace the entry in `font.metadata.records` to apply changes. Likewise,
`font.find_lookup(name)` returns an independent lookup; use `font.set_lookup()`
to replace or append its definition.

### Edit MATH data

MATH constants and glyph metrics use `SfdMathValue`; assemblies use
`SfdGlyphAssembly` / `SfdGlyphPart`, size variants use `SfdGlyphVariants`, and
corner kerning uses `SfdMathKern` / `SfdMathKernEntry`. These models also use
`from_record()` / `to_record()`; replace an existing record when editing a field.
Do not append a second copy of the same glyph field.

```python
from sfdfont import SfdGlyphAssembly, SfdGlyphPart, SfdMathValue

axis_height = SfdMathValue('MATH:AxisHeight:', 250, {12: 1, 13: 0, 14: -1})
assembly = SfdGlyphAssembly(
    parts=[
        SfdGlyphPart('brace.bottom', False, 0, 20, 100),
        SfdGlyphPart('brace.extender', True, 20, 20, 80),
        SfdGlyphPart('brace.top', False, 20, 0, 100),
    ],
)
axis_record = axis_height.to_record()
assembly_record = assembly.to_record()
```

Device adjustments map each ppem in a contiguous range to a signed correction;
include explicit zeros for unchanged sizes. Assembly components and variants must
name existing glyphs in the font. The final corner-kern entry's height is retained
although OpenType does not use it. See `examples/edit_math.py` for a complete example
using an upstream test font.

## Supported formats and boundaries

- SFD versions 1.0, 2.0, 3.0, 3.1 and 3.2, with standard-library-only runtime code.
- Font names, language names, comments, SFD UTF-7, UTF-8 and legacy text fields.
- Layer definitions, m/l/c operations, point flags, control coordinates, hint masks
  and TrueType point indices. Curve order is defined by the layer, including c
  commands in quadratic layers. Closing endpoints are retained without rewriting.
- Named points/contours, clipping path flags, path start offsets and Spiro control
  points. Spiro coordinates are preserved; this library does not regenerate curves.
- Glyph encodings, alternate Unicode/variation mappings, DupEnc encoding aliases,
  vector references and guideline contours. `encoding_aliases` maps additional
  encoding slots to glyph IDs; `find_glyph_by_encoding()` also searches these aliases.
- Glyph state flags through `glyph.flags`. Newly constructed glyphs default to `W`
  (explicit width), so FontForge retains blank glyphs such as spaces. Loaded flags,
  including their absence, are preserved.
- Bitmap strikes with 1/2/4/8-bit sample depths, properties and bitmap references.
  Grayscale data uses one byte per sample; monochrome rows use packed bits.
- Old Image and PNG Image2 payloads, TrueType binary tables and instructions are
  retained as bytes. Images are not rendered and instructions are not executed.
- Editable lookup definitions, contextual/chained/reverse substitution and
  positioning, horizontal/vertical kerning classes (legacy, version 2 and version 3),
  and AAT state machines. Lookup ownership, glyph references and dependency cycles
  are checked. Shaping is outside the scope of the library.
- BASE baselines and language extents, JSTF justification and Mac feature names
  are structurally checked and retained as records. Editable MATH models cover
  constants, italic/accent corrections, size variants, glyph assemblies and all
  four corner-kern tables, with device adjustments and glyph dependency checks.
- Type 3 fonts through `font.multilayer`, per-glyph `layer_count` and `layer.paint`.
  `SfdPaint` stores fill/stroke settings, colours, opacity, pen transforms and dashes.
  `SfdGradient` / `SfdGradientStop` and `SfdPattern` describe gradient and tiled
  glyph brushes; pattern targets and drawing dependency cycles are checked.
- Multiple Master families through `font.multiple_master`: axes, positions, weights,
  axis maps, Apple named instances and instance fonts. The root `SfdFont` is the
  default font; `multiple_master.instances` contains the masters. The library does
  not interpolate outlines or recompute the default font when weights change.
- CID containers through `font.cid` (registry, ordering, supplement and version)
  and `font.subfonts`. CID layout is stored in the container; outline references
  are checked within each subfont. `iter_glyphs()` and name/Unicode queries include
  the subfonts in stored order. Encoding queries return the first matching subfont.
- SFD 3.1/3.2 undo/redo history is retained in the corresponding layer's `records`,
  with operation boundaries, nested outlines and binary payloads checked. Historical
  points and payloads count toward read limits. Undo operations are not executed.
- Counted Private dictionary values and ShortTable words are checked; significant
  whitespace and embedded text in dictionary values are preserved.
- Known terminated text blocks and ordinary additional records are retained without
  interpreting their semantics. Pickled data and MM PostScript subroutines are
  preserved without execution or unpickling.

Versions 0/4, sfdir directories and asfd recovery files are not supported.
Unsupported structures raise `SfdUnsupportedError`; malformed structures raise
`SfdParseError`. Accepting a version header does not imply every extension is supported.

Writing normalizes whitespace and numeric formatting; it does not promise
byte-for-byte reproduction. For loaded fonts retaining uninterpreted records or
payloads, metadata text, glyph advances/flags, bitmap pixels, guidelines, paint
settings and validated layout/MATH parameters can be edited. Glyph identities, outlines,
layer structure and uninterpreted data remain protected when retained records may
depend on them. Incompatible edits raise `SfdValidationError` before the destination
file is opened. Explicitly removing dependent opaque data permits supported geometry
edits; keep a source copy when that data matters.

Duplicate glyph IDs/encoding slots, dangling/cyclic references and inconsistent
bitmap dimensions are rejected. Some historical FontForge files rely on implicit
repair and are therefore rejected. SFD 1.0 glyph counts are treated as historical
capacity hints; later-version counts are checked against the actual glyph count,
except the explicit CID `-1` sentinel.

The 29 original FontForge test fonts are retained under `assets/fontforge`.
22 have semantic parse/dump and load/save conformance coverage. The other 7 are
explicit rejection tests for duplicate IDs/encodings, dangling references or count
mismatches; no samples are silently skipped or repaired. In particular, CaslonMM's
family structure is supported, but its original duplicate IDs fail strict loading.

`SfdReadLimits` configures document byte, glyph, point and cumulative binary-payload
budgets. Glyph/point limits apply across a whole MM/CID document, including history
points. Exceeding a budget raises `SfdLimitError`, a subclass of `SfdParseError`.

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
