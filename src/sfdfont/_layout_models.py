from sfdfont._layout import (
    CONTEXT_KEYS,
    KERN_CLASS_KEYS,
    LayoutReader,
    context_record,
    kern_class_record,
    lookup_record,
)
from sfdfont._reader import Reader
from sfdfont._strings import decode_text, quote
from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.layout import (
    SfdContext,
    SfdContextRule,
    SfdKerningClass,
    SfdLookup,
    SfdLookupFeature,
    SfdLookupSubtable,
    SfdSequenceLookup,
)
from sfdfont.record import SfdRecord


def checked_reader(record: SfdRecord, keys: set[str]) -> LayoutReader:
    if record.keyword not in keys:
        raise SfdParseError(f'wrong layout record type: {record.keyword}')
    reader = Reader(record.value)
    parser = (
        lookup_record
        if record.keyword == 'Lookup:'
        else (context_record if record.keyword in CONTEXT_KEYS else kern_class_record)
    )
    parser(reader, record.keyword)
    if reader.word():
        reader.fail('trailing data in layout record')
    return LayoutReader(Reader(record.value))


def decode_lookup(record: SfdRecord) -> SfdLookup:
    stream = checked_reader(record, {'Lookup:'})
    kind, flags, afm = stream.integer(), stream.integer(maximum=0xFFFFFFFF), stream.integer(maximum=1)
    result = SfdLookup(kind, stream.quoted(), flags, bool(afm))
    if stream.peek() == b'{':
        stream.expect(b'{')
        while stream.peek() != b'}':
            subtable = SfdLookupSubtable(stream.quoted())
            if stream.peek() == b'(':
                stream.expect(b'(')
                if stream.peek() == b'"':
                    subtable.suffix = stream.quoted()
                else:
                    subtable.vertical = bool(stream.integer(maximum=1))
                stream.expect(b')')
            if stream.peek() == b'[':
                stream.expect(b'[')
                subtable.separation = stream.integer(-32768, 32767)
                stream.expect(b',')
                subtable.minimum_kerning = stream.integer(-32768, 32767)
                stream.expect(b',')
                subtable.kerning_flags = stream.integer(maximum=7)
                stream.expect(b']')
            result.subtables.append(subtable)
        stream.expect(b'}')
    if stream.peek() == b'[':
        stream.expect(b'[')
        while stream.peek() != b']':
            if stream.peek() == b'<':
                stream.expect(b'<')
                first = stream.integer()
                stream.expect(b',')
                tag = (first, stream.integer())
                stream.expect(b'>')
            else:
                tag = stream.tag()
            feature = SfdLookupFeature(tag)
            stream.expect(b'(')
            while stream.peek() != b')':
                script = stream.tag()
                stream.expect(b'<')
                languages = []
                while stream.peek() != b'>':
                    languages.append(stream.tag())
                stream.expect(b'>')
                if script in feature.scripts:
                    stream.reader.fail('duplicate script in lookup feature')
                feature.scripts[script] = languages
            stream.expect(b')')
            result.features.append(feature)
        stream.expect(b']')
    return result


def names(stream: LayoutReader) -> list[str]:
    return decode_text(stream.counted_text()).split()


def decode_context(record: SfdRecord) -> SfdContext:
    stream = checked_reader(record, CONTEXT_KEYS)
    reader = stream.reader
    result = SfdContext(record.keyword, reader.word())
    if record.keyword.endswith('2:'):
        result.subtable = stream.quoted()
    else:
        result.flags, result.script_language_index = stream.integer(), stream.integer()
        if stream.peek() == b"'":
            result.tag = stream.tag()
    counts = [stream.integer() for _ in range(3)]
    rule_count = stream.count()
    groups = [[None] * count for count in counts]
    saved = reader.pos
    if counts[0] and reader.word() == 'Class0:':
        groups[0][0] = names(stream)
    else:
        reader.pos = saved
    for group, label in zip(groups, ('Class:', 'BClass:', 'FClass:'), strict=True):
        for index in range(1, len(group)):
            stream.keyword(label)
            group[index] = names(stream)
    result.input_classes, result.backtrack_classes, result.lookahead_classes = groups
    for _ in range(rule_count):
        rule = SfdContextRule()
        values = []
        if result.form == 'glyph':
            for label in ('String:', 'BString:', 'FString:'):
                stream.keyword(label)
                values.append(names(stream))
        else:
            sizes = [stream.count() for _ in range(3)]
            if result.form == 'class':
                for size, label in zip(sizes, ('ClsList:', 'BClsList:', 'FClsList:'), strict=True):
                    stream.keyword(label)
                    values.append([stream.integer() for _ in range(size)])
            else:
                for size, label in zip(sizes, ('Coverage:', 'BCoverage:', 'FCoverage:'), strict=True):
                    group = []
                    for _ in range(size):
                        stream.keyword(label)
                        group.append(names(stream))
                    values.append(group)
        rule.inputs, rule.backtrack, rule.lookahead = values
        if result.form == 'revcov':
            stream.keyword('Replace:')
            rule.replacements = names(stream)
        else:
            for _ in range(stream.count()):
                stream.keyword('SeqLookup:')
                sequence = stream.integer()
                if stream.peek() == b'~':
                    stream.expect(b'~')
                    lookup = None
                else:
                    lookup = stream.quoted() if result.subtable is not None else stream.tag()
                rule.lookups.append(SfdSequenceLookup(sequence, lookup))
        result.rules.append(rule)
    while (key := reader.word()) != 'EndFPST':
        index = ('ClassNames:', 'BClassNames:', 'FClassNames:').index(key)
        value = [stream.quoted() for _ in range(counts[index])]
        setattr(result, ('input_class_names', 'backtrack_class_names', 'lookahead_class_names')[index], value)
    return result


def decode_kern_class(record: SfdRecord) -> SfdKerningClass:
    stream = checked_reader(record, KERN_CLASS_KEYS)
    first = stream.integer(minimum=1)
    start = 1
    if stream.peek() == b'+':
        stream.expect(b'+')
        start = 0
    second = stream.integer(minimum=1)
    result = SfdKerningClass(record.keyword, [None] * first, [None] * second)
    if record.keyword in ('KernClass:', 'VKernClass:'):
        result.script_language_index, result.flags = stream.integer(), stream.integer()
    else:
        result.subtable = stream.quoted()
    modern = record.keyword.endswith('3:')
    for group, begin, flag_attr, name_attr in (
        (result.first_classes, start, 'first_flags', 'first_names'),
        (result.second_classes, 1, 'second_flags', 'second_names'),
    ):
        flags, labels = [0] * len(group), [None] * len(group)
        for index in range(begin, len(group)):
            if modern:
                flags[index], labels[index], text = stream.kern_class_entry()
                group[index] = text.split() if text is not None else []
            else:
                group[index] = names(stream)
        if modern:
            setattr(result, flag_attr, flags)
            setattr(result, name_attr, labels)
    for row in range(first):
        offsets, flags = [], []
        for column in range(second):
            if modern:
                flags.append(stream.integer(maximum=0x7FFFFFFF))
            offsets.append(stream.integer(-32768, 32767))
            device = stream.device_table()
            if device:
                result.adjustments[row, column] = device
        result.offsets.append(offsets)
        if modern:
            result.offset_flags.append(flags)
    return result


def require(value: bool, message: str) -> None:
    if not value:
        raise SfdValidationError(message)


def tag(value: str | tuple[int, int]) -> bytes:
    if isinstance(value, tuple):
        require(len(value) == 2 and all(isinstance(v, int) and 0 <= v <= 65535 for v in value), 'invalid Mac feature')
        return f'<{value[0]},{value[1]}>'.encode()
    require(
        isinstance(value, str) and len(value) == 4 and all(32 <= ord(c) <= 126 for c in value), 'invalid layout tag'
    )
    return b"'" + value.encode('ascii') + b"'"


def name_text(values: list[str] | None) -> bytes:
    require(values is not None, 'only the implicit class zero may be None')
    require(
        all(isinstance(v, str) and v and not any(c.isspace() or c == '\0' for c in v) for v in values),
        'invalid glyph name in layout',
    )
    return ' '.join(values).encode('utf-8')


def counted(values: list[str] | None) -> bytes:
    encoded = name_text(values)
    return str(len(encoded)).encode() + b' ' + encoded


def encoded_record(key: str, value: bytes) -> SfdRecord:
    result = SfdRecord(key, value.strip())
    try:
        checked_reader(result, {key})
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
    return result


def encode_lookup(lookup: SfdLookup) -> SfdRecord:
    data = f'{lookup.lookup_type} {lookup.flags} {int(lookup.store_in_afm)} '.encode() + quote(lookup.name) + b' {'
    for sub in lookup.subtables:
        require(sub.suffix is None or sub.vertical is None, 'subtable cannot have both suffix and vertical flag')
        data += b' ' + quote(sub.name)
        if sub.suffix is not None:
            data += b' (' + quote(sub.suffix) + b')'
        elif sub.vertical is not None:
            data += f' ({int(sub.vertical)})'.encode()
        if sub.separation is not None or sub.minimum_kerning is not None:
            require(sub.separation is not None and sub.minimum_kerning is not None, 'incomplete autokerning parameters')
            data += f'[{sub.separation},{sub.minimum_kerning},{sub.kerning_flags}]'.encode()
        else:
            require(sub.kerning_flags == 0, 'kerning flags require autokerning parameters')
    data += b' } ['
    for feature in lookup.features:
        data += tag(feature.tag) + b' ('
        for script, languages in feature.scripts.items():
            data += tag(script) + b' <' + b' '.join(tag(language) for language in languages) + b'> '
        data += b') '
    return encoded_record('Lookup:', data + b']')


def encode_context(context: SfdContext) -> SfdRecord:
    require(context.keyword in CONTEXT_KEYS, 'invalid context keyword')
    modern = context.keyword.endswith('2:')
    data = context.form.encode() + b' '
    if modern:
        require(context.subtable is not None, 'modern context needs a subtable')
        data += quote(context.subtable)
    else:
        data += f'{context.flags} {context.script_language_index}'.encode()
        if context.tag is not None:
            data += b' ' + tag(context.tag)
    groups = (context.input_classes, context.backtrack_classes, context.lookahead_classes)
    data += f' {len(groups[0])} {len(groups[1])} {len(groups[2])} {len(context.rules)}\n'.encode()
    if groups[0] and groups[0][0] is not None:
        data += b'Class0: ' + counted(groups[0][0]) + b'\n'
    for group, label in zip(groups, (b'Class:', b'BClass:', b'FClass:'), strict=True):
        require(not group or group is groups[0] or group[0] is None, 'backtrack/lookahead class zero must be implicit')
        for names in group[1:]:
            data += label + b' ' + counted(names) + b'\n'
    for rule in context.rules:
        values = (rule.inputs, rule.backtrack, rule.lookahead)
        if context.form == 'glyph':
            for group, label in zip(values, (b'String:', b'BString:', b'FString:'), strict=True):
                data += label + b' ' + counted(group) + b'\n'
        else:
            data += f'{len(values[0])} {len(values[1])} {len(values[2])}\n'.encode()
            if context.form == 'class':
                for group, label in zip(values, (b'ClsList:', b'BClsList:', b'FClsList:'), strict=True):
                    data += label + b' ' + b' '.join(str(index).encode() for index in group) + b'\n'
            else:
                for group, label in zip(values, (b'Coverage:', b'BCoverage:', b'FCoverage:'), strict=True):
                    for coverage in group:
                        data += label + b' ' + counted(coverage) + b'\n'
        if context.form == 'revcov':
            require(not rule.lookups, 'reverse coverage cannot contain sequence lookups')
            data += b'Replace: ' + counted(rule.replacements) + b'\n'
        else:
            require(rule.replacements is None, 'only reverse coverage has replacements')
            data += f'{len(rule.lookups)}\n'.encode()
            for lookup in rule.lookups:
                target = b'~' if lookup.lookup is None else (quote(lookup.lookup) if modern else tag(lookup.lookup))
                data += f'SeqLookup: {lookup.sequence} '.encode() + target + b'\n'
    for labels, group, key in zip(
        (context.input_class_names, context.backtrack_class_names, context.lookahead_class_names),
        groups,
        (b'ClassNames:', b'BClassNames:', b'FClassNames:'),
        strict=True,
    ):
        if labels is not None:
            require(len(labels) == len(group), 'class name count mismatch')
            data += key + b' ' + b' '.join(quote(label) for label in labels) + b'\n'
    return encoded_record(context.keyword, data + b'EndFPST')


def encode_kern_class(kern: SfdKerningClass) -> SfdRecord:
    require(kern.keyword in KERN_CLASS_KEYS, 'invalid kerning class keyword')
    first, second = len(kern.first_classes), len(kern.second_classes)
    require(first > 0 and second > 0, 'empty kerning class dimensions')
    require(kern.second_classes[0] is None, 'second class zero must be implicit')
    require(len(kern.offsets) == first and all(len(row) == second for row in kern.offsets), 'kerning matrix dimensions')
    start = 0 if kern.first_classes[0] is not None else 1
    modern = kern.keyword.endswith('3:')
    data = f'{first}{"+" if start == 0 else ""} {second} '.encode()
    if kern.keyword in ('KernClass:', 'VKernClass:'):
        data += f'{kern.script_language_index} {kern.flags}\n'.encode()
    else:
        require(kern.subtable is not None, 'modern kerning class needs a subtable')
        data += quote(kern.subtable) + b'\n'
    for group, begin, flags, labels in (
        (kern.first_classes, start, kern.first_flags, kern.first_names),
        (kern.second_classes, 1, kern.second_flags, kern.second_names),
    ):
        require(not flags or len(flags) == len(group), 'kerning class flag count')
        require(not labels or len(labels) == len(group), 'kerning class name count')
        if not modern:
            require(not flags and not labels, 'class flags and names require version 3')
        for index in range(begin, len(group)):
            if modern:
                data += f'{flags[index] if flags else 0}'.encode()
                if labels and labels[index] is None:
                    require(not group[index], 'a nameless version 3 class cannot contain glyphs')
                    data += b'\n'
                else:
                    data += b' ' + quote(labels[index] if labels else '') + b' '
                    data += quote(name_text(group[index]).decode('utf-8')) + b'\n'
            else:
                data += counted(group[index]) + b'\n'
    require(
        not kern.offset_flags
        or (modern and len(kern.offset_flags) == first and all(len(row) == second for row in kern.offset_flags)),
        'invalid offset flags',
    )
    require(
        all(0 <= row < first and 0 <= column < second for row, column in kern.adjustments), 'device table cell index'
    )
    for row in range(first):
        for column in range(second):
            if modern:
                data += f'{kern.offset_flags[row][column] if kern.offset_flags else 0} '.encode()
            data += f'{kern.offsets[row][column]} '.encode()
            device = kern.adjustments.get((row, column), {})
            if device:
                sizes = sorted(device)
                require(sizes == list(range(sizes[0], sizes[-1] + 1)), 'device table sizes must be contiguous')
                data += f'{{{sizes[0]}-{sizes[-1]} '.encode()
                data += b','.join(str(device[size]).encode() for size in sizes) + b'} '
    return encoded_record(kern.keyword, data)
