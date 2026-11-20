from sfdfont._parser import decode_text, integer
from sfdfont._reader import Reader
from sfdfont.bitmap import SfdBitmapGlyph, SfdBitmapProperty, SfdBitmapReference, SfdBitmapStrike
from sfdfont.font import SfdFont


def bitmap(reader: Reader, font: SfdFont) -> SfdBitmapStrike:
    size, capacity, ascent, descent = (integer(reader.word()) for _ in range(4))
    if size <= 0 or min(capacity, ascent, descent) < 0:
        reader.fail('invalid bitmap strike dimensions')
    strike = SfdBitmapStrike(size, ascent, descent)
    saved = reader.pos
    optional = reader.inline_word()
    if optional in ('1', '2', '4', '8'):
        strike.depth = int(optional)
    else:
        reader.pos = saved
    saved = reader.pos
    optional = reader.inline_word()
    if optional and not optional.endswith(':'):
        strike.foundry = optional
    else:
        reader.pos = saved
    while True:
        key = reader.word()
        if key == 'EndBitmapFont':
            return strike
        if not key:
            reader.fail('unterminated bitmap strike')
        if key == 'BDFChar:':
            if len(strike.glyphs) >= reader.limits.max_glyphs:
                reader.fail('bitmap glyph limit exceeded')
            fields = [integer(value) for value in reader.line().split()]
            if len(fields) == 6:
                encoding = fields[0]
                matches = [glyph for glyph in font.glyphs if glyph.encoding == encoding]
                if len(matches) != 1:
                    reader.fail('legacy bitmap encoding has no unique glyph')
                fields.insert(0, matches[0].glyph_id)
            if len(fields) not in (7, 8):
                reader.fail('invalid BDFChar header')
            gid, encoding, advance, xmin, xmax, ymin, ymax = fields[:7]
            if gid < 0 or encoding < -1 or xmax < xmin or ymax < ymin:
                reader.fail('invalid BDFChar dimensions or identity')
            stride = (xmax - xmin + 8) // 8 if strike.depth == 1 else xmax - xmin + 1
            data = reader.ascii85(stride * (ymax - ymin + 1))
            strike.glyphs.append(
                SfdBitmapGlyph(
                    gid, encoding, advance, xmin, xmax, ymin, ymax, data, fields[7] if len(fields) == 8 else None
                )
            )
        elif key == 'BDFRefChar:':
            fields = reader.line().split()
            if len(fields) != 5 or fields[4] not in (b'N', b'S'):
                reader.fail('invalid BDFRefChar')
            strike.references.append(SfdBitmapReference(*(integer(value) for value in fields[:4]), fields[4] == b'S'))
        elif key == 'BDFStartProperties:':
            count = integer(reader.line())
            if count < 0 or count > reader.limits.max_bytes:
                reader.fail('invalid property count')
            for _ in range(count):
                name, kind = reader.word(), integer(reader.word())
                value = reader.line()
                if kind & ~0x10 in (0, 1):
                    if value.startswith(b'"'):
                        if not value.endswith(b'"'):
                            reader.fail('unterminated bitmap property')
                        value = value[1:-1]
                    parsed = decode_text(value)
                elif kind & ~0x10 in (2, 3):
                    parsed = integer(value)
                else:
                    reader.fail('unknown bitmap property type')
                strike.properties.append(SfdBitmapProperty(name, kind, parsed))
            if reader.word() != 'BDFEndProperties':
                reader.fail('missing BDFEndProperties')
        elif key == 'Resolution:':
            strike.resolution = integer(reader.line())
        else:
            reader.fail(f'unexpected bitmap record {key!r}')
