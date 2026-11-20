from sfdfont._layout import LayoutReader
from sfdfont._layout_models import tag
from sfdfont._reader import Reader
from sfdfont.baselines import SfdBaselineExtent, SfdBaselines, SfdBaselineScript
from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.record import SfdRecord

BASE_KEYS = {'BaseHoriz:', 'BaseVert:'}


def finish(stream):
    if stream.peek():
        stream.reader.fail('trailing baseline data')


def read_baselines(reader, key):
    stream = LayoutReader(Reader(reader.line(), reader.limits))
    count = stream.integer()
    tags = [stream.tag() for _ in range(count)]
    if len(set(tags)) != len(tags):
        reader.fail('duplicate baseline tag')
    finish(stream)
    result = SfdBaselines(key, tags)
    scripts = set()
    while True:
        saved = reader.pos
        if reader.word() != 'BaseScript:':
            reader.pos = saved
            break
        stream = LayoutReader(Reader(reader.line(), reader.limits))
        script = SfdBaselineScript(stream.tag(), stream.integer(maximum=max(0, count - 1)))
        if script.tag in scripts:
            reader.fail('duplicate baseline script')
        scripts.add(script.tag)
        script.positions = [stream.integer(-32768, 32767) for _ in range(count)]
        depth = 0
        while stream.peek():
            if stream.peek() == b'{':
                stream.expect(b'{')
                extent = SfdBaselineExtent(stream.tag() if stream.peek() == b"'" else None)
                extent.descent = stream.integer(-32768, 32767)
                extent.ascent = stream.integer(-32768, 32767)
                extent.depth = depth
                script.extents.append(extent)
                depth += 1
            elif stream.peek() == b'}' and depth:
                stream.expect(b'}')
                depth -= 1
            else:
                reader.fail('invalid baseline language extent')
        if depth:
            reader.fail('unclosed baseline language extent')
        result.scripts.append(script)
    return result


def baseline_record(reader, key):
    start = reader.pos
    read_baselines(reader, key)
    return SfdRecord(key, reader.data[start : reader.pos].strip())


def decode_baselines(item):
    if item.keyword not in BASE_KEYS:
        raise SfdParseError('unexpected baseline record kind')
    reader = Reader(item.value)
    result = read_baselines(reader, item.keyword)
    if reader.word():
        reader.fail('trailing baseline data')
    return result


def encode_baselines(value):
    from sfdfont._validation import check, number

    check(value.keyword in BASE_KEYS, 'invalid baseline keyword')
    number(len(value.tags), 'baseline count', 0, 65535)
    parts = [b' '.join([str(len(value.tags)).encode(), *(tag(item) for item in value.tags)])]
    for script in value.scripts:
        number(script.default_baseline, 'default baseline', 0, max(0, len(value.tags) - 1))
        check(len(script.positions) == len(value.tags), 'baseline position count mismatch')
        data = [b'BaseScript:', tag(script.tag), str(script.default_baseline).encode()]
        for position in script.positions:
            number(position, 'baseline position', -32768, 32767)
            data.append(str(position).encode())
        depth = 0
        for extent in script.extents:
            number(extent.depth, 'baseline extent depth', 0, depth)
            while depth > extent.depth:
                data.append(b'}')
                depth -= 1
            data.append(b'{')
            if extent.tag is not None:
                data.append(tag(extent.tag))
            number(extent.descent, 'baseline descent', -32768, 32767)
            number(extent.ascent, 'baseline ascent', -32768, 32767)
            data.extend([str(extent.descent).encode(), str(extent.ascent).encode()])
            depth += 1
        data.extend([b'}'] * depth)
        parts.append(b' '.join(data))
    item = SfdRecord(value.keyword, b'\n'.join(parts))
    try:
        parsed = decode_baselines(item)
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
    if parsed != value:
        raise SfdValidationError('baseline fields would change interpretation when written')
    return item


def baseline_identity(item):
    value = decode_baselines(item)
    return (
        item.keyword,
        value.tags,
        [(script.tag, [(extent.tag, extent.depth) for extent in script.extents]) for script in value.scripts],
    )


def validate_baselines(font):
    seen = set()
    try:
        for item in font.metadata.records:
            if item.keyword in BASE_KEYS:
                if item.keyword in seen:
                    raise SfdValidationError('duplicate baseline table')
                seen.add(item.keyword)
                decode_baselines(item)
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
