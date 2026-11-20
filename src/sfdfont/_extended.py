from sfdfont._layout import LayoutReader
from sfdfont._reader import Reader
from sfdfont._strings import decode_text
from sfdfont.record import SfdRecord

BASE_KEYS = {'BaseHoriz:', 'BaseVert:'}
EXTENDED_KEYS = BASE_KEYS | {'Justify:', 'MacFeat:'}
JSTF_LOOKUPS = {
    'JstfEnableShrink:',
    'JstfDisableShrink:',
    'JstfMaxShrink:',
    'JstfEnableExtend:',
    'JstfDisableExtend:',
    'JstfMaxExtend:',
}


def finish(stream: LayoutReader) -> None:
    if stream.peek():
        stream.reader.fail('trailing extended record data')


def base_record(reader: Reader, key: str) -> SfdRecord:
    from sfdfont._baselines import baseline_record

    return baseline_record(reader, key)


def read_justify(reader: Reader):
    glyphs = []
    lookups = []
    key = 'Justify:'
    language = None
    count = priorities = 0
    actions = set()
    scripts = set()
    languages = set()
    while True:
        if key in ('Justify:', 'JstfLang:', 'EndJustify') and priorities != count:
            reader.fail('JSTF priority count mismatch')
        if key == 'EndJustify':
            return glyphs, lookups
        if key == 'Justify:':
            stream = LayoutReader(Reader(reader.line(), reader.limits))
            tag = stream.tag()
            if tag in scripts:
                reader.fail('duplicate JSTF script')
            scripts.add(tag)
            finish(stream)
            language = None
            languages = set()
            count = priorities = 0
        elif key == 'JstfExtender:' and language is None:
            glyphs.extend(decode_text(reader.line()).split())
        elif key == 'JstfLang:':
            stream = LayoutReader(Reader(reader.line(), reader.limits))
            language = stream.tag()
            if language in languages:
                reader.fail('duplicate JSTF language')
            languages.add(language)
            count = stream.count()
            finish(stream)
            priorities = 0
        elif key == 'JstfPrio:' and language is not None:
            if reader.line():
                reader.fail('unexpected JSTF priority header data')
            priorities += 1
            if priorities > count:
                reader.fail('too many JSTF priorities')
            actions = set()
        elif key in JSTF_LOOKUPS and language is not None and priorities:
            if key in actions:
                reader.fail('duplicate JSTF lookup action')
            actions.add(key)
            stream = LayoutReader(Reader(reader.line(), reader.limits))
            while stream.peek():
                lookups.append((stream.quoted(), key.startswith('JstfMax')))
        else:
            reader.fail(f'unexpected JSTF record {key!r}')
        key = reader.word()
        if not key:
            reader.fail('missing EndJustify')


def justify_record(reader: Reader, key: str) -> SfdRecord:
    start = reader.pos
    read_justify(reader)
    return SfdRecord(key, reader.data[start : reader.pos].strip())


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
