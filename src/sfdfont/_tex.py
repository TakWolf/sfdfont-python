from sfdfont._layout import LayoutReader
from sfdfont._metrics import signed_short
from sfdfont._reader import Reader
from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.record import SfdRecord
from sfdfont.tex import SfdTexData, SfdTexMetrics

TEX_GLYPH_KEYS = {'TeX:'}


def decode_tex_data(item):
    if item.keyword != 'TeXData:':
        raise SfdParseError('unexpected TeX data record kind')
    reader = Reader(item.value)
    stream = LayoutReader(reader)
    kind = stream.integer(maximum=3)
    design_size = stream.integer(-0x80000000, 0x7FFFFFFF)
    parameters = [stream.integer(-0x80000000, 0x7FFFFFFF) for _ in range(22)]
    if stream.peek():
        reader.fail('trailing TeX data parameters')
    return SfdTexData(kind, design_size, parameters)


def decode_tex_metrics(item):
    if item.keyword != 'TeX:':
        raise SfdParseError('unexpected TeX metric record kind')
    reader = Reader(item.value)
    stream = LayoutReader(reader)
    height, depth = (signed_short(stream.integer(-32768, 65535)) for _ in range(2))
    legacy = None
    if stream.peek():
        legacy = tuple(signed_short(stream.integer(-32768, 65535)) for _ in range(2))
    if stream.peek():
        reader.fail('TeX metrics require two or four values')
    return SfdTexMetrics(height, depth, legacy)


def checked(item, value, decode):
    try:
        if decode(item) != value:
            raise SfdValidationError('TeX fields would change interpretation when written')
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
    return item


def encode_tex_data(value):
    from sfdfont._validation import check, number

    number(value.kind, 'TeX data kind', 0, 3)
    number(value.design_size, 'TeX design size', -0x80000000, 0x7FFFFFFF)
    check(len(value.parameters) == 22, 'TeX data requires 22 parameters')
    for parameter in value.parameters:
        number(parameter, 'TeX parameter', -0x80000000, 0x7FFFFFFF)
    data = b' '.join(str(parameter).encode() for parameter in [value.kind, value.design_size, *value.parameters])
    return checked(SfdRecord('TeXData:', data), value, decode_tex_data)


def encode_tex_metrics(value):
    from sfdfont._validation import check, number

    values = [value.height, value.depth]
    if value.legacy is not None:
        check(len(value.legacy) == 2, 'legacy TeX metrics require two extra values')
        values.extend(value.legacy)
    for entry in values:
        number(entry, 'TeX metric', -32768, 32767)
    data = b' '.join(str(entry).encode() for entry in values)
    return checked(SfdRecord('TeX:', data), value, decode_tex_metrics)


def tex_record(reader, key):
    item = SfdRecord(key, reader.line())
    decode_tex_metrics(item)
    return item


def validate_tex(font):
    try:
        for glyph in font.glyphs:
            seen = False
            for item in [*glyph.records, *(record for layer in glyph.layers for record in layer.records)]:
                if item.keyword == 'TeX:':
                    if seen:
                        raise SfdValidationError('duplicate TeX metrics in glyph')
                    seen = True
                    decode_tex_metrics(item)
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
