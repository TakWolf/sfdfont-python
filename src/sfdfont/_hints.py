import math
import re

from sfdfont._layout import LayoutReader
from sfdfont._reader import Reader
from sfdfont.error import SfdLimitError, SfdParseError, SfdValidationError
from sfdfont.hints import (
    SfdCounterMasks,
    SfdDiagonalHint,
    SfdDiagonalHints,
    SfdMinimumDistance,
    SfdMinimumDistances,
    SfdStemHint,
    SfdStemHints,
)
from sfdfont.record import SfdRecord

STEM_KEYS = {'HStem:', 'VStem:'}
DIAGONAL_KEYS = {'DStem:', 'DStem2:'}
HINT_KEYS = STEM_KEYS | DIAGONAL_KEYS | {'CounterMasks:', 'MinimumDistance:'}
_REAL_TOKEN = re.compile(rb'[^\s<>G]+')


class HintReader(LayoutReader):
    def budget(self):
        self.reader.hint_count += 1
        if self.reader.hint_count > self.reader.limits.max_hints:
            self.reader.fail('max_hints exceeded', SfdLimitError)

    def real(self):
        from sfdfont._parser import real

        self.reader.whitespace()
        match = _REAL_TOKEN.match(self.reader.data, self.reader.pos, self.reader.pos + 129)
        if match is None:
            self.reader.fail('expected hint coordinate')
        self.reader.pos += len(match[0])
        return real(match[0])

    def instances(self):
        if self.peek() != b'<':
            return []
        self.expect(b'<')
        values = []
        while self.peek() != b'>':
            self.budget()
            values.append((self.real(), self.real()))
        self.expect(b'>')
        return values


def parse_hints(reader: Reader, key: str):
    stream = HintReader(reader)
    if key in STEM_KEYS:
        result = SfdStemHints(key)
        while stream.peek():
            stream.budget()
            start, width = stream.real(), stream.real()
            ghost = stream.peek() == b'G'
            if ghost:
                stream.expect(b'G')
            result.hints.append(SfdStemHint(start, width, ghost, stream.instances()))
        return result
    if key in DIAGONAL_KEYS:
        result = SfdDiagonalHints(key)
        while stream.peek():
            stream.budget()
            coordinates = tuple(stream.real() for _ in range(8 if key == 'DStem:' else 6))
            instances = stream.instances() if key == 'DStem2:' else []
            result.hints.append(SfdDiagonalHint(coordinates, instances))
        return result
    if key == 'CounterMasks:':
        count = stream.count()
        masks = []
        for _ in range(count):
            stream.budget()
            value = reader.word()
            if not re.fullmatch(r'(?:[0-9a-fA-F]{2}){1,12}', value):
                reader.fail('counter mask must contain 1 to 12 bytes')
            masks.append(bytes.fromhex(value))
        return SfdCounterMasks(masks)
    if key == 'MinimumDistance:':
        result = SfdMinimumDistances()
        while stream.peek():
            stream.budget()
            axis = reader.char()
            if axis not in (b'x', b'y'):
                reader.fail('invalid minimum distance axis')
            first = stream.integer(-1, 0x7FFFFFFF)
            stream.expect(b',')
            second = stream.integer(-1, 0x7FFFFFFF)
            result.distances.append(SfdMinimumDistance(axis.decode(), first, second))
        return result
    reader.fail('unexpected hint record kind')


def decode(record, keys):
    if record.keyword not in keys:
        raise SfdParseError('unexpected hint record kind')
    reader = Reader(record.value)
    value = parse_hints(reader, record.keyword)
    if reader.word():
        reader.fail('trailing hint data')
    return value


def hint_record(reader: Reader, key: str) -> SfdRecord:
    record = SfdRecord(key, reader.line())
    nested = Reader(record.value, reader.limits)
    nested.hint_count = reader.hint_count
    try:
        parse_hints(nested, key)
        if nested.word():
            nested.fail('trailing hint data')
    except SfdLimitError:
        reader.fail('max_hints exceeded', SfdLimitError)
    reader.hint_count = nested.hint_count
    return record


def decode_stems(record):
    return decode(record, STEM_KEYS)


def decode_diagonals(record):
    return decode(record, DIAGONAL_KEYS)


def decode_counter_masks(record):
    return decode(record, {'CounterMasks:'})


def decode_minimum_distances(record):
    return decode(record, {'MinimumDistance:'})


def instances_data(instances):
    from sfdfont._writer import scalar

    if not instances:
        return b''
    values = []
    for pair in instances:
        if len(pair) != 2 or not all(math.isfinite(v) for v in pair):
            raise SfdValidationError('invalid hint instance range')
        values.extend(scalar(v) for v in pair)
    return b'<' + b' '.join(values) + b'>'


def checked(key, data, value):
    result = SfdRecord(key, data)
    try:
        parsed = decode(result, HINT_KEYS)
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
    if parsed != value:
        raise SfdValidationError('hint fields would change interpretation when written')
    return result


def encode_stems(value):
    from sfdfont._validation import check
    from sfdfont._writer import scalar

    check(value.keyword in STEM_KEYS, 'invalid stem hint keyword')
    parts = []
    for hint in value.hints:
        check(math.isfinite(hint.start) and math.isfinite(hint.width), 'nonfinite stem hint')
        check(isinstance(hint.ghost, bool), 'invalid ghost hint flag')
        parts.append(
            scalar(hint.start)
            + b' '
            + scalar(hint.width)
            + (b'G' if hint.ghost else b'')
            + instances_data(hint.instances)
        )
    return checked(value.keyword, b' '.join(parts), value)


def encode_diagonals(value):
    from sfdfont._validation import check
    from sfdfont._writer import scalar

    check(value.keyword in DIAGONAL_KEYS, 'invalid diagonal hint keyword')
    parts = []
    for hint in value.hints:
        check(len(hint.coordinates) == (8 if value.keyword == 'DStem:' else 6), 'invalid diagonal coordinate count')
        check(all(math.isfinite(v) for v in hint.coordinates), 'nonfinite diagonal hint')
        check(value.keyword != 'DStem:' or not hint.instances, 'old DStem cannot contain hint instances')
        parts.append(b' '.join(scalar(v) for v in hint.coordinates) + instances_data(hint.instances))
    return checked(value.keyword, b' '.join(parts), value)


def encode_counter_masks(value):
    for mask in value.masks:
        if not isinstance(mask, bytes) or not 1 <= len(mask) <= 12:
            raise SfdValidationError('counter mask must contain 1 to 12 bytes')
    data = b' '.join([str(len(value.masks)).encode(), *(mask.hex().encode() for mask in value.masks)])
    return checked('CounterMasks:', data, value)


def encode_minimum_distances(value):
    from sfdfont._validation import check, number

    parts = []
    for distance in value.distances:
        check(distance.axis in ('x', 'y'), 'invalid minimum distance axis')
        number(distance.first, 'minimum distance point', -1)
        number(distance.second, 'minimum distance point', -1)
        parts.append(f'{distance.axis}{distance.first},{distance.second}'.encode())
    return checked('MinimumDistance:', b' '.join(parts), value)


def hint_identity(records):
    result = []
    for record in records:
        if record.keyword in STEM_KEYS | DIAGONAL_KEYS:
            value = decode(record, HINT_KEYS)
            result.append((record.keyword, len(value.hints)))
        elif record.keyword == 'CounterMasks:':
            value = decode_counter_masks(record)
            result.append((record.keyword, len(value.masks)))
        elif record.keyword == 'MinimumDistance:':
            value = decode_minimum_distances(record)
            result.append((record.keyword, value.distances))
    return result


def validate_hints(font):
    try:
        for record in font.metadata.records:
            if record.keyword in HINT_KEYS:
                raise SfdValidationError('glyph hint record in font metadata')
        for glyph in font.iter_glyphs():
            for record in [*glyph.records, *(r for layer in glyph.layers for r in layer.records)]:
                if record.keyword in HINT_KEYS:
                    decode(record, HINT_KEYS)
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
