from sfdfont._layout import LayoutReader
from sfdfont._reader import Reader
from sfdfont.error import SfdLimitError, SfdUnsupportedError
from sfdfont.record import SfdRecord


def history_layer(record: SfdRecord) -> int:
    stream = LayoutReader(Reader(record.value))
    stream.keyword('Layer:')
    return stream.integer()


def history_record(reader: Reader, key: str) -> SfdRecord:
    from sfdfont._binary import payload
    from sfdfont._parser import integer, record, reference, spline_set

    start = reader.pos
    stream = LayoutReader(reader)
    stream.keyword('Layer:')
    stream.integer()

    def marker(value):
        stream.keyword(value)
        if reader.line():
            reader.fail(f'unexpected data after {value}')

    for group, operation in [('Undoes', 'Undo'), ('Redoes', 'Redo')]:
        marker(group)
        index = 0
        while True:
            token = reader.word()
            if token == 'End' + group:
                if reader.line():
                    reader.fail('unexpected history group terminator data')
                break
            if token != operation + 'Operation':
                reader.fail(f'expected {operation}Operation or End{group}')
            if reader.line():
                reader.fail('unexpected operation marker data')
            for field in ('Index:', 'Type:', 'WasModified:', 'WasOrder2:'):
                stream.keyword(field)
                value = integer(reader.line())
                if field == 'Index:' and value != index:
                    reader.fail('history operation index mismatch')
                if field == 'Type:' and not 0 <= value <= 18:
                    reader.fail('unsupported undo operation type', SfdUnsupportedError)
                if field in ('WasModified:', 'WasOrder2:') and value not in (0, 1):
                    reader.fail('invalid history flag')
            index += 1
            seen = set()
            while True:
                token = reader.word()
                if token == 'End' + operation + 'Operation':
                    if reader.line():
                        reader.fail('unexpected operation terminator data')
                    break
                if not token:
                    reader.fail('unterminated history operation')
                if token in ('Layer:', 'Width:', 'VWidth:', 'LBearingChange:', 'UnicodeEnc:', 'InstructionsLength:'):
                    if token in seen:
                        reader.fail(f'duplicate history field {token}')
                    seen.add(token)
                    value = integer(reader.line())
                    if token == 'Layer:' and not 0 <= value <= 65535:
                        reader.fail('invalid operation layer')
                    if token == 'InstructionsLength:' and not 0 <= value <= reader.limits.max_payload_bytes:
                        reader.fail('history instruction length exceeds budget', SfdLimitError)
                elif token in ('Charname:', 'Comment:'):
                    stream.expect(b'"')
                    while True:
                        char = reader.char()
                        if char == b'"':
                            break
                        if not char:
                            reader.fail('unterminated history string')
                        if char == b'\0':
                            reader.fail('NUL in history string')
                    if reader.line():
                        reader.fail('trailing history string data')
                elif token in ('Refer:', 'Ref:'):
                    reference(reader, token == 'Ref:')
                elif token in ('Image:', 'Image2:', 'TtfInstrs:'):
                    payload(reader, token)
                elif token == 'SplineSet':
                    spline_set(reader)
                elif token in ('AnchorPoint:', 'HStem:', 'VStem:', 'DStem:', 'DStem2:', 'TtInstrs:', 'CopiedFrom:'):
                    record(reader, token)
                else:
                    reader.fail(f'unsupported history field {token!r}', SfdUnsupportedError)
    marker('EndUndoRedoHistory')
    return SfdRecord(key, reader.data[start : reader.pos].strip())
