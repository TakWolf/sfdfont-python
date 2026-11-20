"""Read layout record boundaries using counts and lengths from FontForge's SFD grammar.

Records retain their encoded contents. This module validates their structure;
it does not resolve lookup dependencies or apply shaping rules.
"""

import re

from sfdfont._reader import Reader
from sfdfont._strings import decode_utf7
from sfdfont.error import SfdLimitError
from sfdfont.record import SfdRecord

CONTEXT_KEYS = {
    'ContextPos:',
    'ContextSub:',
    'ChainPos:',
    'ChainSub:',
    'ReverseChain:',
    'ContextPos2:',
    'ContextSub2:',
    'ChainPos2:',
    'ChainSub2:',
    'ReverseChain2:',
}
KERN_CLASS_KEYS = {
    'KernClass:',
    'VKernClass:',
    'KernClass2:',
    'VKernClass2:',
    'KernClass3:',
    'VKernClass3:',
}
AAT_KEYS = {
    f'Mac{kind}{suffix}:'
    for kind in ('Indic', 'Context', 'Ligature', 'Simple', 'Kern', 'Insert')
    for suffix in ('', '2')
}
SUBSTITUTION_KEYS = {'Substitution2:', 'MultipleSubs2:', 'AlternateSubs2:', 'Ligature2:'}
PST_KEYS = SUBSTITUTION_KEYS | {'Position2:', 'PairPos2:', 'LCarets2:'}
LAYOUT_KEYS = CONTEXT_KEYS | KERN_CLASS_KEYS | AAT_KEYS | {'Lookup:', 'TableOrder:', 'AnchorClass2:'}


def version_matches(key: str, version: str) -> bool:
    if key in PST_KEYS | {'Lookup:', 'AnchorClass2:'}:
        return version != '1.0'
    if key in {key.replace('2:', ':') for key in PST_KEYS} | {'AnchorClass:'}:
        return version == '1.0'
    if key == 'TableOrder:':
        return version == '1.0'
    if key in CONTEXT_KEYS | KERN_CLASS_KEYS | AAT_KEYS:
        modern = key.endswith(('2:', '3:'))
        return modern == (version != '1.0')
    return True


class LayoutReader:
    def __init__(self, reader: Reader) -> None:
        self.reader = reader

    def peek(self) -> bytes:
        self.reader.whitespace()
        return self.reader.data[self.reader.pos : self.reader.pos + 1]

    def expect(self, value: bytes) -> None:
        self.reader.whitespace()
        for char in value:
            if self.reader.char() != bytes([char]):
                self.reader.fail(f'expected {value!r} in layout record')

    def keyword(self, value: str) -> None:
        if self.reader.word() != value:
            self.reader.fail(f'expected {value} in layout record')

    def integer(self, minimum: int = 0, maximum: int = 65535) -> int:
        self.reader.whitespace()
        match = re.match(rb'[+-]?\d{1,12}(?!\d)', self.reader.data[self.reader.pos : self.reader.pos + 13])
        if match is None:
            self.reader.fail('expected integer in layout record')
        self.reader.pos += len(match[0])
        value = int(match[0])
        if not minimum <= value <= maximum:
            self.reader.fail('layout integer out of range')
        return value

    def count(self) -> int:
        value = self.integer(maximum=0x7FFFFFFF)
        if value > self.reader.limits.max_bytes:
            self.reader.fail('layout count exceeds max_bytes', SfdLimitError)
        return value

    def counted_text(self) -> bytes:
        length = self.count()
        separator = self.reader.char()
        if separator not in (b' ', b'\t') and not (length == 0 and separator in (b'\r', b'\n')):
            self.reader.fail('missing separator before counted layout string')
        end = self.reader.pos + length
        if end > len(self.reader.data):
            self.reader.fail('truncated counted layout string')
        value = self.reader.data[self.reader.pos : end]
        self.reader.pos = end
        if b'\0' in value:
            self.reader.fail('NUL in layout string')
        return value

    def quoted(self) -> str:
        self.expect(b'"')
        start = self.reader.pos
        end = self.reader.data.find(b'"', start)
        if end == -1:
            self.reader.fail('unterminated layout string')
        self.reader.pos = end + 1
        return decode_utf7(self.reader.data[start:end])

    def tag(self) -> str:
        self.expect(b"'")
        result = bytearray()
        for _ in range(4):
            char = self.reader.char()
            if char in (b'', b'\r', b'\n'):
                self.reader.fail('incomplete layout tag')
            result.extend(char)
        if self.reader.char() != b"'":
            self.reader.fail('layout tag must contain exactly four bytes')
        try:
            return result.decode('ascii')
        except UnicodeDecodeError:
            self.reader.fail('non-ASCII layout tag')
        raise AssertionError

    def device_table(self) -> dict[int, int]:
        if self.peek() != b'{':
            return {}
        self.expect(b'{')
        if self.peek() == b'}':
            self.expect(b'}')
            return {}
        first = self.integer()
        self.expect(b'-')
        last = self.integer(minimum=first)
        result = {}
        for size in range(first, last + 1):
            if self.peek() == b',':
                self.expect(b',')
            result[size] = self.integer(minimum=-128, maximum=127)
        self.expect(b'}')
        return result

    def kern_class_entry(self) -> tuple[int, str | None, str | None]:
        flags = self.integer(maximum=0x7FFFFFFF)
        strings = []
        for _ in range(2):
            while self.reader.data[self.reader.pos : self.reader.pos + 1] in (b' ', b'\t'):
                self.reader.pos += 1
            if self.reader.data[self.reader.pos : self.reader.pos + 1] != b'"':
                break
            strings.append(self.quoted())
        while self.reader.data[self.reader.pos : self.reader.pos + 1] in (b' ', b'\t'):
            self.reader.pos += 1
        if self.reader.data[self.reader.pos : self.reader.pos + 1] not in (b'\r', b'\n', b''):
            self.reader.fail('unexpected data in kerning class entry')
        strings += [None] * (2 - len(strings))
        return flags, strings[0], strings[1]


def context_record(reader: Reader, key: str) -> SfdRecord:
    start = reader.pos
    stream = LayoutReader(reader)
    form = reader.word()
    if form not in ('glyph', 'class', 'coverage', 'revcov'):
        reader.fail(f'unknown context format {form!r}')
    modern = key.endswith('2:')
    if modern:
        stream.quoted()
    else:
        stream.integer()
        stream.integer()
        if stream.peek() == b"'":
            stream.tag()
    counts = [stream.integer() for _ in range(3)]
    rule_count = stream.count()
    saved = reader.pos
    if counts[0] and reader.word() == 'Class0:':
        stream.counted_text()
    else:
        reader.pos = saved
    for count, label in zip(counts, ('Class:', 'BClass:', 'FClass:'), strict=True):
        for _ in range(1, count):
            stream.keyword(label)
            stream.counted_text()
    for _ in range(rule_count):
        if form == 'glyph':
            input_count = 0
            for index, label in enumerate(('String:', 'BString:', 'FString:')):
                stream.keyword(label)
                value = stream.counted_text()
                if index == 0:
                    input_count = len(value.split())
        else:
            sizes = [stream.count() for _ in range(3)]
            input_count = sizes[0]
            if form == 'class':
                for size, class_count, label in zip(sizes, counts, ('ClsList:', 'BClsList:', 'FClsList:'), strict=True):
                    stream.keyword(label)
                    for _ in range(size):
                        stream.integer(maximum=class_count - 1)
            else:
                for size, label in zip(sizes, ('Coverage:', 'BCoverage:', 'FCoverage:'), strict=True):
                    for _ in range(size):
                        stream.keyword(label)
                        stream.counted_text()
        if form == 'revcov':
            stream.keyword('Replace:')
            stream.counted_text()
        else:
            for _ in range(stream.count()):
                stream.keyword('SeqLookup:')
                stream.integer(maximum=input_count - 1)
                if stream.peek() == b'~':
                    stream.expect(b'~')
                elif modern:
                    stream.quoted()
                else:
                    stream.tag()
    labels = dict(zip(('ClassNames:', 'BClassNames:', 'FClassNames:'), counts, strict=True))
    seen = set()
    while True:
        token = reader.word()
        if token == 'EndFPST':
            break
        if token not in labels or token in seen:
            reader.fail('expected class names or EndFPST')
        seen.add(token)
        for _ in range(labels[token]):
            stream.quoted()
    return SfdRecord(key, reader.data[start : reader.pos].strip())


def table_order_record(reader: Reader, key: str) -> SfdRecord:
    start = reader.pos
    stream = LayoutReader(reader)
    if stream.peek() == b"'":
        stream.tag()
    elif len(reader.word()) != 4:
        reader.fail('invalid table tag')
    for _ in range(stream.count()):
        if stream.peek() == b'<':
            stream.expect(b'<')
            stream.integer()
            stream.expect(b',')
            stream.integer()
            stream.expect(b'>')
        else:
            stream.tag()
    return SfdRecord(key, reader.data[start : reader.pos].strip())


def kern_class_record(reader: Reader, key: str) -> SfdRecord:
    start = reader.pos
    stream = LayoutReader(reader)
    first_count = stream.integer(minimum=1)
    class_start = 1
    if stream.peek() == b'+':
        stream.expect(b'+')
        class_start = 0
    second_count = stream.integer(minimum=1)
    if key in ('KernClass:', 'VKernClass:'):
        stream.integer()
        stream.integer()
    else:
        stream.quoted()
    cells = first_count * second_count
    if cells > reader.limits.max_bytes:
        reader.fail('kerning matrix exceeds max_bytes', SfdLimitError)
    version3 = key.endswith('3:')
    for _ in range(first_count - class_start + second_count - 1):
        if version3:
            stream.kern_class_entry()
        else:
            stream.counted_text()
    for _ in range(cells):
        if version3:
            stream.integer(maximum=0x7FFFFFFF)
        stream.integer(minimum=-32768, maximum=32767)
        stream.device_table()
    return SfdRecord(key, reader.data[start : reader.pos].strip())


def lookup_record(reader: Reader, key: str) -> SfdRecord:
    start = reader.pos
    stream = LayoutReader(reader)
    stream.integer()
    stream.integer(maximum=0xFFFFFFFF)
    stream.integer(maximum=1)
    if not stream.quoted():
        reader.fail('empty lookup name')
    if stream.peek() == b'{':
        stream.expect(b'{')
        while stream.peek() != b'}':
            if not stream.quoted():
                reader.fail('empty lookup subtable name')
            if stream.peek() == b'(':
                stream.expect(b'(')
                if stream.peek() == b'"':
                    stream.quoted()
                else:
                    stream.integer(maximum=1)
                stream.expect(b')')
            if stream.peek() == b'[':
                stream.expect(b'[')
                stream.integer(minimum=-32768, maximum=32767)
                stream.expect(b',')
                stream.integer(minimum=-32768, maximum=32767)
                stream.expect(b',')
                stream.integer(maximum=7)
                stream.expect(b']')
        stream.expect(b'}')
    if stream.peek() == b'[':
        stream.expect(b'[')
        while stream.peek() != b']':
            if stream.peek() == b'<':
                stream.expect(b'<')
                stream.integer()
                stream.expect(b',')
                stream.integer()
                stream.expect(b'>')
            else:
                stream.tag()
            stream.expect(b'(')
            while stream.peek() != b')':
                stream.tag()
                stream.expect(b'<')
                while stream.peek() != b'>':
                    stream.tag()
                stream.expect(b'>')
            stream.expect(b')')
        stream.expect(b']')
    return SfdRecord(key, reader.data[start : reader.pos].strip())
