# SfdFont - Python

[![Python](https://img.shields.io/badge/python-3.10-brightgreen?style=flat-square)](https://www.python.org)
[![PyPI](https://img.shields.io/pypi/v/sfdfont?style=flat-square)](https://pypi.org/project/sfdfont/)

A pure Python library for [FontForge Spline Font Database (SFD)](https://fontforge.org/docs/techref/sfdformat.html) files.

## Installation

```shell
pip install sfdfont
```

## Usage

### Create outlines

```python
from sfdfont import SfdContour, SfdFont, SfdGlyph, SfdLayer, SfdPoint

contour = SfdContour(
    [
        SfdPoint(0, 0),
        SfdPoint(300, 700, 'l'),
        SfdPoint(600, 0, 'l'),
        SfdPoint(0, 0, 'l'),
    ]
)
font = SfdFont(
    glyphs=[
        SfdGlyph(
            name='A',
            glyph_id=0,
            encoding=65,
            unicode=65,
            width=600,
            layers=[SfdLayer(index=1, contours=[contour])],
        ),
    ]
)
font.metadata.font_name = 'OutlineExample'
font.save('outlines.sfd')
```

See `examples/create_outlines.py` for a complete example.

### Load and save

```python
from examples import ASSETS_DIR, BUILD_DIR
from sfdfont import SfdFont

font = SfdFont.load(ASSETS_DIR.joinpath('fontforge', 'Ambrosia.sfd'))
outputs_dir = BUILD_DIR.joinpath('load_save')
outputs_dir.mkdir(parents=True, exist_ok=True)
font.save(outputs_dir.joinpath('Ambrosia.sfd'))
```

See `examples/load_save.py` for a complete example using the upstream Ambrosia font.

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

### Mark attachment classes and filtering sets

`SfdMarkClasses` and `SfdMarkSets` read and write the counted multiline
`MarkAttachClasses:` and `MarkAttachSets:` records. Each `SfdMarkGroup` contains
a display name and a list of existing glyph names.

```python
from sfdfont import SfdMarkClasses, SfdMarkGroup, SfdMarkSets

classes = SfdMarkClasses([SfdMarkGroup('above', ['acutecomb', 'gravecomb'])])
sets = SfdMarkSets([SfdMarkGroup('acute-only', ['acutecomb'])])
class_record = classes.to_record()
set_record = sets.to_record()
```

The classes list omits implicit class 0: its first group has index 1. The first
filtering set has index 0. Lookup flags select a class with `class_index << 8`,
or a filtering set with `0x10 | (set_index << 16)`. Class members must be disjoint;
filtering sets may overlap. References and table duplication are checked when
validating the font. Names and group order remain protected while other opaque
data is retained, and existing groups' membership can be edited.

These models also use `from_record()` / `to_record()` with explicit replacement
in `font.metadata.records`. See `examples/create_mark_filter.py` for a complete
example that writes empty combining glyphs and a filtered substitution lookup.

### Edit glyph positioning and anchors

`SfdPosition` and `SfdPairPosition` contain `SfdPositionValue` objects with offsets,
advances and device adjustments. `SfdSubstitution` covers single, multiple,
alternate and ligature substitutions. `SfdKerningPairs` / `SfdKerningPair` cover
horizontal and vertical pair lists; `SfdLigatureCarets` stores insertion positions.
These models target the modern records with a `2` suffix, in SFD 2.0 and later.
Legacy SFD 1.0 records have separate models described below; no implicit format
conversion is performed.

```python
from sfdfont import SfdPairPosition, SfdPositionValue, SfdSubstitution

pair = SfdPairPosition(
    'kern-subtable',
    'V',
    first=SfdPositionValue(x_advance=-80, x_advance_adjustments={12: 1, 13: 0}),
)
replacement = SfdSubstitution('Substitution2:', 'smallcaps-subtable', ['a.sc'])
pair_record = pair.to_record()
substitution_record = replacement.to_record()
```

Referenced lookup subtables and target glyphs must already exist in the font.
Use `SfdAnchor` for `AnchorPoint:` records in either legacy or modern SFD:

```python
from sfdfont import SfdAnchor

anchor = SfdAnchor.from_record(anchor_record)
anchor.y += 20
updated_record = anchor.to_record()
```

Replace the original entry in `glyph.records` or the corresponding `layer.records`
to apply the change. Anchors retain their role, ligature component index, device
adjustments and optional TrueType point index. `SfdAnchorClasses` /
`SfdAnchorClass` describe modern class definitions in `font.metadata.records`.
See `examples/edit_anchors.py` for a complete edit using DejaVuSerif.

### Edit legacy SFD 1.0 layout

`SfdScriptLanguages` reads the counted `ScriptLang:` table as `lists` of
`SfdScriptLanguage(script, languages)` entries. Tags contain exactly four ASCII
characters, including padding spaces such as `'SRB '`. Both historical bare tags
and quoted tags are accepted. An explicit table is checked against legacy
layout indices, with `0xfffe` / `0xffff` retained as special values. Missing
tables are not synthesized. Existing table bindings remain protected when
uninterpreted dependencies are retained; this is not a migration to modern lookups.

`SfdLegacyPst` covers `Position:`, `PairPos:`, substitution/ligature records and
`LCarets:`. Its `SfdLegacyBinding` retains optional flags, script/language index,
and either a four-byte tag or a Mac feature/setting pair. `positions` contains
one or two `SfdPositionValue` objects; `glyphs` and `carets` retain the appropriate
record's tokens or insertion positions.

```python
from sfdfont import SfdLegacyPst

pair = SfdLegacyPst.from_record(pair_record)
pair.positions[0].y_offset += 10
updated_record = pair.to_record()
```

`SfdLegacyKerningPairs` / `SfdLegacyKerningPair` support `Kerns:`, `KernsSLI:`,
`KernsSLIF:`, `VKernsSLIF:`, `KernsSLIFO:` and `VKernsSLIFO:`. The `SLIFO` forms
use glyph IDs; the other forms use encoding slots. `SfdLegacyAnchorClasses` /
`SfdLegacyAnchorClass` retain old feature tags, flags, script/language indices,
merge fields and optional class types.

Omitted fields remain omitted. A later optional numeric field requires all its
preceding fields. Caret records need a tag or both numeric prefix fields to make
the count unambiguous. Old `PairPos:` records preserve an explicit `|` separator
when present. Existing bindings and targets remain protected after loading while
legacy or other opaque dependencies are retained; positioning, kerning, caret and
device-adjustment values can be changed. Historical unresolved glyph targets are
preserved without repair or promotion to modern lookups.

See `examples/edit_legacy_layout.py` for a complete edit of the original VKern font.

### Edit font information

`SfdGaspTable` contains a `version` and ordered `SfdGaspRange(ppem, flags)` entries.
Each ppem value is an inclusive upper limit; limits must strictly increase.
Unknown flag bits are retained. Empty tables and lists without a final `65535`
limit are preserved without adding ranges.

```python
from sfdfont import SfdGaspRange, SfdGaspTable

gasp = SfdGaspTable([SfdGaspRange(8, 2), SfdGaspRange(65535, 3)], version=0)
gasp_record = gasp.to_record()
```

Use `from_record()` / `to_record()` and replace the entry in
`font.metadata.records` when editing. The library checks counts and integer bounds;
it does not render glyphs or apply the grid-fitting flags.

`SfdDesignSize(size, range=None, style_id=None, names=None)` retains the optical
design size in tenths of a point. A range is a `(bottom, top)` pair with an exclusive
lower and inclusive upper bound; it must be supplied together with `style_id`.
Optional `SfdStyleName(language, name)` entries use Windows language IDs and SFD
UTF-7 text. Omitted fields remain omitted; names require a range/style group.
Both the historical space-separated range and the usual `bottom-top` form can be
read; writing uses the latter. The library does not infer style names or compile
the OpenType size feature.

`SfdFontMetric(keyword, value)` covers PFM family, weight/width, line gaps, OS/2
and hhea metrics, offset flags, styles, embedding flags and OS/2 version fields.

```python
from sfdfont import SfdFontMetric

font.metadata.set_metric(SfdFontMetric('TTFWeight:', 500))
ascent = font.metadata.find_metric('OS2TypoAscent:')
```

`find_metric()` returns an independent object or `None`; apply edits with
`set_metric()`. Historical `PfmWeight:` and `HHead*` aliases are recognized.
Signed 16-bit fields decode unsigned bit patterns to their native signed value;
PFM family uses an unsigned byte and boolean fields use integers 0/1. StyleMap
accepts the hexadecimal forms FontForge writes. Values and offset flags remain
separate: the library does not compute absolute metrics from outline bounds or
validate the font for OpenType generation.

`SfdFontRealMetric(keyword, value)` covers ItalicAngle, UnderlinePosition,
UnderlineWidth, StrokeWidth, UFOAscent and UFODescent. These use the same
`find_metric()` / `set_metric()` helpers. Values must be finite; decimal points,
historical decimal commas and exponents are accepted when reading, and writing
uses decimal points. No outline transformation or metric scaling is applied.

`SfdPanose.values` contains ten unsigned byte values, defaulting to ten zeros;
legacy signed-byte spellings are also accepted when reading. `SfdOs2Mask`
represents `OS2CodePages:` or `OS2UnicodeRanges:` as one unsigned integer with
64 or 128 bits. SFD stores the least significant 32-bit word first; unknown bits
are retained. `SfdOs2Vendor.vendor` contains exactly four bytes, including any
historical NUL padding. It is a fixed byte field rather than UTF-7 text.
These models also use explicit `from_record()` / `to_record()` conversions.

See `examples/create_font_info.py` for a complete example.

Header information also uses `SfdFontMetric`: CreationTime and ModificationTime
retain signed 64-bit seconds since 1970, UniqueID uses signed 32-bit storage, and
UseUniqueID, UseXUID and NeedsXUIDChange are integer 0/1 flags. Timestamps are not
refreshed and identifiers are not generated automatically. `SfdSfntRevision.value`
retains the raw unsigned 32-bit pattern of the 16.16 revision field, including
FontForge's `0x44445555` unset sentinel; it is independent of the version string.
See `examples/create_font_header.py`.

### Edit WOFF metadata

`SfdWoffMetadata(text)` reads and writes the `woffMetadata:` SFD UTF-7 string,
retaining XML text, significant whitespace and line breaks without parsing or
executing XML. Use explicit `from_record()` / `to_record()` replacement in
`font.metadata.records`.

WOFF version components use `SfdFontMetric('woffMajor:', value)` and
`SfdFontMetric('woffMinor:', value)` with `metadata.find_metric()` / `set_metric()`.
Their signed 32-bit stored values remain independent, including FontForge's
`0x4455` unset sentinel; missing components are not inferred. This preserves SFD
data and does not check a generated WOFF header. While metadata text is retained,
the existing protection for glyph identities and outlines remains in effect.
See `examples/create_woff_metadata.py` for a complete example.

### Retain legacy style mapping names

`SfdStyleMapName(keyword, name, quoted=True)` reads and writes `OS2StyleName:`,
`StyleMapFamilyName:` and `OS2FamilyName:`. Both SFD UTF-7 strings and older
unquoted text are supported, with the original form retained. Ordered legacy
records and repeated names are retained; no StyleMap fallback or name-table
migration is applied automatically.

Family-name prefixes before a `LangName:` are stored in that
`SfdLanguageNames.style_map_family_names` list as `SfdStyleMapName` objects and
written immediately before it.
Prefixes after the last language record remain in `font.metadata.records`.
This preserves the ordering needed by FontForge's legacy interpretation while
keeping the language's own name values unchanged. FontForge may normalize or
discard legacy fields on import. See `examples/create_legacy_names.py`.

### Retain UFO groups and raw kerning

`SfdGlyphGroup(name, glyphs)` reads and writes `Group:`; `SfdGroupKerningPair`
stores a `GroupKern:` or `GroupVKern:` record with `left`, `right` and a signed
32-bit `offset`. Names use SFD UTF-7. These are raw UFO preservation records;
they do not create or update native kerning classes or glyph kerning pairs.

Use explicit `from_record()` / `to_record()` replacement in `font.metadata.records`.
Historical unresolved names, duplicate records and their order are retained
without repair. Existing group membership, pair targets and referenced native
class names remain protected while these bindings are retained; raw offsets can
be edited. UFO export may prefer FontForge's native kerning data over raw offsets.
See `examples/create_groups.py` for a complete example.

### Edit TeX data

`SfdTexData(kind, design_size, parameters)` retains the font-level `TeXData:`
record: kind 0/1/2/3 is unset/text/math-symbol/math-extension, followed by a raw
design size and exactly 22 signed 32-bit parameters. Design size uses 20 fractional
bits in points; other parameters retain their stored fixed-point values.
Parameters default to 22 zeros.

`SfdTexMetrics(height, depth, legacy=None)` stores a glyph's two signed 16-bit
metrics; `32767` is the undefined sentinel. The optional two-value `legacy`
tuple retains the obsolete four-value form. Historical zero-value fixups are
not applied, and the library does not synchronize TeXData with DesignSize.
FontForge may recompute redundant sizes or apply its old metric fixups on import.

Both models use explicit `from_record()` / `to_record()` replacement in font
metadata or glyph/layer records, respectively. The library does not produce TFM
files or evaluate TeX layout. See `examples/create_tex.py`.

### Edit baselines

`SfdBaselines` reads and writes `BaseHoriz:` / `BaseVert:` records. Its `tags`
list defines the order of each `SfdBaselineScript.positions` list;
`default_baseline` selects an index in that list.

```python
from sfdfont import SfdBaselines

baselines = SfdBaselines.from_record(baseline_record)
baselines.scripts[0].positions[0] += 10
updated_record = baselines.to_record()
```

Replace the original entry in `font.metadata.records` to apply the change.
`SfdBaselineExtent` stores optional language/feature tags and descent/ascent
ranges. Extents form an ordered list: depth 0 starts a language range, depth 1
starts a feature range inside it; larger depths retain further nesting.
While opaque dependencies are retained, tags, script order and extent hierarchy
remain protected; coordinates, ranges and the default baseline can be edited.
See `examples/create_baselines.py` for a complete example.

### Edit justification

`SfdJustification` contains `SfdJustificationScript` objects with optional extender
glyph lists and `SfdJustificationLanguage` objects. Each language has an ordered
list of `SfdJustificationPriority` objects with six optional lookup-name lists:
`enable_shrink`, `disable_shrink`, `max_shrink`, `enable_extend`, `disable_extend`
and `max_extend`. `None` omits a list; `[]` retains an explicitly empty list.

```python
from sfdfont import SfdJustification

justification = SfdJustification.from_record(justification_record)
justification.scripts[0].languages[0].priorities[0].max_extend = ['expand']
updated_record = justification.to_record()
```

Replace the entry in `font.metadata.records` to apply changes. Extenders must name
existing glyphs and actions must name existing lookups. Maximum shrink/extend
lists require OpenType positioning lookups. Script/language tags and their order
remain protected while opaque dependencies are retained; priorities, actions and
extender membership can be edited. No justification algorithm is executed.
See `examples/create_justification.py` for a complete example.

### Edit Mac feature names

`SfdMacFeatures` contains `SfdMacFeature` objects with a feature number, `is_mutex`
flag, byte-sized `default_setting`, names and `SfdMacSetting` objects. Features
and settings each require at least one `SfdMacName`; an empty name is allowed.

```python
from sfdfont import SfdMacFeatures

features = SfdMacFeatures.from_record(mac_feature_record)
features.features[0].names[0].data = b'Ligatures'
updated_record = features.to_record()
```

Replace the entry in `font.metadata.records` to apply changes. `SfdMacName.data`
contains bytes in its declared Macintosh encoding, not SFD UTF-7. Octal escapes
retain control bytes, high bytes, quotes and backslashes; NUL is rejected.
Feature/setting numbers and name encoding/language order remain protected while
opaque dependencies are retained; name bytes, mutex flags and defaults can be
edited. Feature defaults may refer to built-in settings outside this name table.
See `examples/create_mac_features.py` for a complete example.

The library preserves escaped name bytes on roundtrip. FontForge 20251009 drops
octal-escaped Mac name bytes when importing SFD; names using plain ASCII without
escapes avoid this FontForge limitation.

### Edit OpenType feature names

`SfdFeatureNames(tag, names, trailer=None)` describes an `OtfFeatName:` record.
Each `SfdFeatureName` contains a Windows language ID and a label. Simple labels
work for stylistic sets and historical character variants. Extended `cv` labels
also contain `tooltip`, `sample` and a counted `parameters` list; an empty list
is distinct from an omitted list.

```python
from sfdfont import SfdFeatureName, SfdFeatureNames

labels = SfdFeatureNames('ss01', [SfdFeatureName(0x0409, 'Round a')])
feature_name_record = labels.to_record()
```

Use explicit `from_record()` / `to_record()` replacement in `font.metadata.records`.
Tags, language order, parameter counts and the reserved character-variant trailer
remain protected while opaque dependencies are retained. Labels, tooltips, sample
text and existing parameter names can be edited. The trailer is preserved without
interpreting it as character mappings. See `examples/create_feature_names.py`.

FontForge 20251009 only retains simple character-variant labels on import;
extended fields require a newer FontForge implementation.

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

### Edit PostScript hints

`SfdStemHints` / `SfdStemHint` describe `HStem:` and `VStem:` records, including
ghost flags and activation intervals. `SfdDiagonalHints` / `SfdDiagonalHint`
retain old eight-coordinate `DStem:` or six-coordinate `DStem2:` records; only
the latter can contain activation intervals. Coordinates and intervals are
preserved without recomputing the hints.

```python
from sfdfont import SfdStemHints

hints = SfdStemHints.from_record(stem_record)
hints.hints[0].start += 1
updated_record = hints.to_record()
```

Replace the original entry in `glyph.records` or `layer.records` to apply the
change. `SfdCounterMasks` stores masks as byte strings, each one to twelve bytes.
`SfdMinimumDistances` / `SfdMinimumDistance` retain obsolete axis and point-pair
bindings, including the `-1` sentinel; they do not resolve or apply those distances.
While dependent data is retained after loading, hint counts, minimum-distance
bindings and outlines remain protected. Existing stem/diagonal coordinates,
activation intervals and counter-mask bytes can be edited.

See `examples/edit_hints.py` for a complete edit of Ambrosia.

### Edit Private dictionaries and ShortTable words

`SfdPrivateDict` contains ordered `SfdPrivateEntry` objects. Keys are ASCII tokens;
values are bytes containing PostScript source, with significant whitespace retained.
Decoding removes SFD line continuations before counting value bytes. Duplicate keys
and empty values retain their position; values are not interpreted or executed.

```python
from sfdfont import SfdPrivateDict

private = SfdPrivateDict.from_record(private_record)
private.entries[0].value = b'[-20 0 502 517 750 768]'
updated_record = private.to_record()
```

`SfdShortTable` stores a four-character `tag` and ordered `SfdShortTableWord`
objects. Each word has a `value` in `-32768..65535` and an optional `name` for
the `cvt ` table. Word values retain their written signed or unsigned form;
the models do not validate or execute TrueType programs.

Both models use explicit replacement in `font.metadata.records`. Existing values
and CVT names can be edited after loading. Private key order, table tags and word
counts remain protected while dependent data is retained. Literal backslash-newline
sequences cannot be represented in a Private value and are rejected when writing.
See `examples/edit_private.py` for an edit of Ambrosia's blue zones.

## Supported formats and boundaries

- SFD versions 1.0, 2.0, 3.0, 3.1 and 3.2, with standard-library-only runtime code.
- Font names, language names, comments, SFD UTF-7, UTF-8 and legacy text fields.
- Editable GaspTable ranges and versions, with count, ppem order and integer checks.
- Optical DesignSize, optional ranges/style IDs and multilingual style names.
- Editable OS/2, PFM and hhea numeric metrics, styles, offset flags and legacy aliases.
- Finite real-valued italic angle, underline, stroke-width and UFO metrics.
- Raw sfnt revision bits, signed 64-bit timestamps and identifier values/flags,
  without automatic timestamp or identifier updates.
- PANOSE byte values, OS/2 Unicode/code-page bitmasks and fixed four-byte vendor IDs.
- OpenType feature labels and extended character-variant names, with language and
  parameter count checks and explicit preservation of reserved trailer text.
- Font-level TeX parameters and modern/legacy glyph TeX metrics, with fixed counts,
  native integer bounds and preservation of undefined sentinels.
- UFO glyph groups and raw horizontal/vertical kerning records, preserving unresolved
  bindings and keeping them separate from native kerning tables.
- WOFF version components and metadata text, without XML parsing or automatic
  version defaulting.
- Legacy style mapping names and their ordering relative to language name records,
  without applying legacy fallback or migration rules.
- Layer definitions, m/l/c operations, point flags, control coordinates, hint masks
  and TrueType point indices. Curve order is defined by the layer, including c
  commands in quadratic layers. Closing endpoints are retained without rewriting.
- Named points/contours, clipping path flags, path start offsets and Spiro control
  points. Spiro coordinates are preserved; this library does not regenerate curves.
- PostScript horizontal, vertical and diagonal hints, ghost flags and activation
  intervals have editable models. Counter masks and obsolete minimum-distance
  bindings are retained and checked. Point and counter masks are limited to 96 bits;
  hints are not generated or applied to outlines.
- Glyph encodings, alternate Unicode/variation mappings, DupEnc encoding aliases,
  vector references and guideline contours. `encoding_aliases` maps additional
  encoding slots to glyph IDs; `find_glyph_by_encoding()` also searches these aliases.
- Glyph state flags through `glyph.flags`. Newly constructed glyphs default to `W`
  (explicit width), so FontForge retains blank glyphs such as spaces. Loaded flags,
  including their absence, are preserved.
- Bitmap strikes with 1/2/4/8-bit sample depths, properties and bitmap references.
  Grayscale data uses one byte per sample; monochrome rows use packed bits.
- Old Image and PNG Image2 payloads, TrueType binary tables and instructions are
  retained as bytes. Obsolete `OrigType1:` charstrings and `BeginSubrs:` subroutines
  are also retained in `glyph.payloads` and `font.payloads`, respectively. These
  blocks use an empty payload terminator and stop at their declared decoded length;
  subroutine counts/lengths are normalized in the header. Images are not rendered
  and instructions/charstrings are not executed.
- Editable lookup definitions, contextual/chained/reverse substitution and
  positioning, horizontal/vertical kerning classes (legacy, version 2 and version 3),
  and AAT state machines. Mark attachment classes/filtering sets include counted
  multiline parsing, membership editing and lookup flag index validation. Glyph positioning, substitutions, pair kerning, ligature
  carets and anchors also have editable models. Separate legacy models retain
  SFD 1.0 bindings and permit numeric layout edits. Lookup ownership, glyph references and dependency cycles
  are checked. Shaping is outside the scope of the library.
- BASE baselines, language/feature extents, JSTF justification and Mac feature names
  have editable models, including extender glyph and lookup dependency checks.
  Editable MATH models cover
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
  are checked within each subfont. BASE, JSTF and Mac feature definitions also belong
  in the container. `iter_glyphs()` and name/Unicode queries include
  the subfonts in stored order. Encoding queries return the first matching subfont.
- SFD 3.1/3.2 undo/redo history is retained in the corresponding layer's `records`,
  with operation boundaries, nested outlines and binary payloads checked. Historical
  points and payloads count toward read limits. Undo operations are not executed.
- Counted Private dictionary values and ShortTable words have editable models;
  significant whitespace, embedded text and optional CVT names are preserved.
- Known terminated text blocks and ordinary additional records are retained without
  interpreting their semantics. Pickled data and MM PostScript subroutines are
  preserved without execution or unpickling.

Versions 0/4, sfdir directories and asfd recovery files are not supported.
Unsupported structures raise `SfdUnsupportedError`; malformed structures raise
`SfdParseError`. Accepting a version header does not imply every extension is supported.

Writing normalizes whitespace and numeric formatting; it does not promise
byte-for-byte reproduction. For loaded fonts retaining uninterpreted records or
payloads, metadata text, glyph advances/flags, bitmap pixels, guidelines, paint
settings, Private values, ShortTable words/names and validated layout/MATH/hint,
baseline, justification and Mac feature name
parameters can be edited. Glyph identities, outlines,
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

`SfdReadLimits` configures document byte, glyph, point, hint and cumulative
binary-payload budgets. Glyph/point/hint limits apply across a whole MM/CID document,
including history. `max_hints` counts stem/diagonal entries, activation intervals,
counter masks and minimum-distance entries. Exceeding a budget raises `SfdLimitError`,
a subclass of `SfdParseError`.

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
