from sfdfont._layout import AAT_KEYS, LayoutReader
from sfdfont._reader import Reader
from sfdfont._strings import decode_text, quote
from sfdfont.aat import SfdState, SfdStateMachine
from sfdfont.error import SfdLimitError, SfdParseError, SfdValidationError
from sfdfont.record import SfdRecord


def parse_machine(reader: Reader, key: str) -> SfdStateMachine:
    stream = LayoutReader(reader)
    machine = SfdStateMachine(keyword=key)
    if key.endswith('2:'):
        machine.subtable = stream.quoted()
    else:
        machine.feature = stream.integer()
        stream.expect(b',')
        machine.setting = stream.integer()
    machine.flags = stream.integer()
    class_count = stream.integer(minimum=4)
    state_count = stream.integer(minimum=2)
    if class_count * state_count > reader.limits.max_bytes:
        reader.fail('AAT state matrix exceeds document budget', SfdLimitError)
    machine.classes = [None] * 4
    for _ in range(4, class_count):
        stream.keyword('Class:')
        machine.classes.append(decode_text(stream.counted_text()).split())
    for _ in range(state_count):
        row = []
        for _ in range(class_count):
            state = SfdState(stream.integer(maximum=state_count - 1), stream.integer())
            if key.startswith('MacContext'):
                values = []
                for _ in range(2):
                    if stream.peek() == b'~':
                        stream.expect(b'~')
                        values.append(None)
                    else:
                        values.append(stream.quoted() if key.endswith('2:') else stream.tag())
                state.mark_lookup, state.current_lookup = values
            elif key.startswith('MacInsert'):
                for attr in ('mark_insert', 'current_insert'):
                    length = stream.count()
                    if length:
                        separator = reader.char()
                        if separator not in (b' ', b'\t'):
                            reader.fail('missing separator before AAT insertion')
                        end = reader.pos + length
                        if end > len(reader.data):
                            reader.fail('truncated AAT insertion')
                        value = reader.data[reader.pos : end]
                        if b'\0' in value:
                            reader.fail('NUL in AAT insertion')
                        reader.pos = end
                        setattr(state, attr, decode_text(value).split())
            elif key.startswith('MacKern'):
                state.kern_values = [stream.integer(-32768, 32767) for _ in range(stream.count())]
            row.append(state)
        machine.states.append(row)
    stream.keyword('EndASM')
    return machine


def machine_record(reader: Reader, key: str) -> SfdRecord:
    start = reader.pos
    parse_machine(reader, key)
    return SfdRecord(key, reader.data[start : reader.pos].strip())


def decode_machine(record: SfdRecord) -> SfdStateMachine:
    if record.keyword not in AAT_KEYS:
        raise SfdParseError('not an AAT state machine record')
    reader = Reader(record.value)
    result = parse_machine(reader, record.keyword)
    if reader.word():
        reader.fail('trailing AAT state machine data')
    return result


def encode_machine(machine: SfdStateMachine) -> SfdRecord:
    from sfdfont._validation import check, number
    from sfdfont._writer import plain

    check(machine.keyword in AAT_KEYS, 'invalid AAT state machine keyword')
    modern = machine.keyword.endswith('2:')
    check((machine.subtable is not None) == modern, 'AAT subtable/version mismatch')
    check(len(machine.classes) >= 4 and machine.classes[:4] == [None] * 4, 'AAT needs four implicit classes')
    check(all(group is not None for group in machine.classes[4:]), 'undefined AAT class')
    number(machine.flags, 'AAT flags', 0, 65535)
    if modern:
        check(bool(machine.subtable), 'empty AAT subtable')
        header = quote(machine.subtable)
    else:
        number(machine.feature, 'AAT feature', 0, 65535)
        number(machine.setting, 'AAT setting', 0, 65535)
        header = f'{machine.feature},{machine.setting}'.encode()
    lines = [header + f' {machine.flags} {len(machine.classes)} {len(machine.states)}\n'.encode()]
    for group in machine.classes[4:]:
        text = plain(' '.join(group))
        lines.append(f'Class: {len(text)} '.encode() + text + b'\n')
    for row in machine.states:
        check(len(row) == len(machine.classes), 'AAT state matrix dimensions mismatch')
        for state in row:
            number(state.next_state, 'AAT next state', 0, len(machine.states) - 1)
            number(state.flags, 'AAT state flags', 0, 65535)
            line = f'{state.next_state} {state.flags}'.encode()
            context, insert, kern = (machine.keyword.startswith('Mac' + name) for name in ('Context', 'Insert', 'Kern'))
            check(
                context or (state.mark_lookup is None and state.current_lookup is None), 'unexpected AAT lookup action'
            )
            check(insert or not (state.mark_insert or state.current_insert), 'unexpected AAT insertion action')
            check(kern or not state.kern_values, 'unexpected AAT kerning action')
            if context:
                for name in (state.mark_lookup, state.current_lookup):
                    if name is None:
                        line += b' ~'
                    elif modern:
                        line += b' ' + quote(name)
                    else:
                        tag = plain(name)
                        check(len(tag) == 4 and b"'" not in tag, 'invalid legacy AAT lookup tag')
                        line += b" '" + tag + b"'"
            if insert:
                for group in (state.mark_insert, state.current_insert):
                    text = plain(' '.join(group))
                    line += f' {len(text)}'.encode() + (b' ' + text if text else b'')
            if kern:
                line += f' {len(state.kern_values)}'.encode()
                for value in state.kern_values:
                    number(value, 'AAT kerning', -32768, 32767)
                    line += f' {value}'.encode()
            lines.append(line + b'\n')
    result = SfdRecord(machine.keyword, b''.join([*lines, b'EndASM']))
    try:
        decode_machine(result)
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
    return result
