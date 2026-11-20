from sfdfont._layout import LayoutReader
from sfdfont._reader import Reader
from sfdfont._strings import quote
from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.record import SfdRecord
from sfdfont.size import SfdDesignSize, SfdStyleName


def decode_design_size(item):
    if item.keyword != 'DesignSize:':
        raise SfdParseError('unexpected design size record kind')
    reader = Reader(item.value)
    stream = LayoutReader(reader)
    result = SfdDesignSize(stream.integer())
    if stream.peek():
        bottom = stream.integer()
        if stream.peek() == b'-':
            stream.expect(b'-')
        top = stream.integer()
        if bottom > top:
            reader.fail('reversed design size range')
        result.range = (bottom, top)
        result.style_id = stream.integer()
        seen = set()
        while stream.peek():
            language = stream.integer()
            if language in seen:
                reader.fail('duplicate design style language')
            seen.add(language)
            result.names.append(SfdStyleName(language, stream.quoted()))
    return result


def encode_design_size(value):
    from sfdfont._validation import check, number

    number(value.size, 'design size', 0, 65535)
    data = [str(value.size).encode()]
    if value.range is None:
        check(value.style_id is None and not value.names, 'design style fields require a range')
    else:
        check(len(value.range) == 2, 'invalid design size range')
        bottom, top = value.range
        number(bottom, 'design size lower bound', 0, 65535)
        number(top, 'design size upper bound', bottom, 65535)
        number(value.style_id, 'design style ID', 0, 65535)
        data.extend([f'{bottom}-{top}'.encode(), str(value.style_id).encode()])
        for name in value.names:
            number(name.language, 'design style language', 0, 65535)
            data.extend([str(name.language).encode(), quote(name.name)])
    result = SfdRecord('DesignSize:', b' '.join(data))
    try:
        if decode_design_size(result) != value:
            raise SfdValidationError('design style fields would change interpretation when written')
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
    return result
