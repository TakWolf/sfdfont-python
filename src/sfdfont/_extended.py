from sfdfont._layout import LayoutReader
from sfdfont._reader import Reader
from sfdfont.record import SfdRecord

BASE_KEYS = {'BaseHoriz:', 'BaseVert:'}
EXTENDED_KEYS = BASE_KEYS | {'Justify:', 'MacFeat:'}


def finish(stream: LayoutReader) -> None:
    if stream.peek():
        stream.reader.fail('trailing extended record data')


def base_record(reader: Reader, key: str) -> SfdRecord:
    from sfdfont._baselines import baseline_record

    return baseline_record(reader, key)


def read_justify(reader: Reader):
    from sfdfont._justification import justification_references, read_justification

    return justification_references(read_justification(reader))


def justify_record(reader: Reader, key: str) -> SfdRecord:
    from sfdfont._justification import justification_record

    return justification_record(reader, key)


def mac_features_record(reader: Reader, key: str) -> SfdRecord:
    from sfdfont._family import mac_name

    start = reader.pos
    named = True
    feature = False
    while True:
        if key in ('MacFeat:', 'MacSetting:', 'EndMacFeatures') and not named:
            reader.fail('Mac feature or setting requires a name')
        if key == 'EndMacFeatures':
            break
        if key == 'MacFeat:':
            stream = LayoutReader(Reader(reader.line(), reader.limits))
            stream.integer()
            stream.integer(maximum=1)
            stream.integer()
            finish(stream)
            named, feature = False, True
        elif key == 'MacSetting:' and feature:
            stream = LayoutReader(Reader(reader.line(), reader.limits))
            stream.integer()
            finish(stream)
            named = False
        elif key == 'MacName:' and feature:
            mac_name(reader.line())
            named = True
        else:
            reader.fail(f'unexpected Mac feature record {key!r}')
        key = reader.word()
        if not key:
            reader.fail('missing EndMacFeatures')
    return SfdRecord('MacFeat:', reader.data[start : reader.pos].strip())
