from sfdfont._layout import LayoutReader
from sfdfont._layout_models import name_text, tag
from sfdfont._reader import Reader
from sfdfont._strings import decode_text, quote
from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.justification import (
    SfdJustification,
    SfdJustificationLanguage,
    SfdJustificationPriority,
    SfdJustificationScript,
)
from sfdfont.record import SfdRecord

JSTF_ACTIONS = {
    'JstfEnableShrink:': 'enable_shrink',
    'JstfDisableShrink:': 'disable_shrink',
    'JstfMaxShrink:': 'max_shrink',
    'JstfEnableExtend:': 'enable_extend',
    'JstfDisableExtend:': 'disable_extend',
    'JstfMaxExtend:': 'max_extend',
}


def finish(stream):
    if stream.peek():
        stream.reader.fail('trailing justification header data')


def read_justification(reader):
    result = SfdJustification()
    key = 'Justify:'
    script = language = priority = None
    count = 0
    scripts = set()
    languages = set()
    actions = set()
    while True:
        if key in ('Justify:', 'JstfLang:', 'EndJustify') and language is not None:
            if len(language.priorities) != count:
                reader.fail('JSTF priority count mismatch')
        if key == 'EndJustify':
            return result
        if key == 'Justify:':
            stream = LayoutReader(Reader(reader.line(), reader.limits))
            script = SfdJustificationScript(stream.tag())
            if script.tag in scripts:
                reader.fail('duplicate JSTF script')
            scripts.add(script.tag)
            finish(stream)
            result.scripts.append(script)
            language = priority = None
            languages = set()
        elif key == 'JstfExtender:' and language is None:
            if script.extenders is not None:
                reader.fail('duplicate JSTF extender list')
            script.extenders = decode_text(reader.line()).split()
        elif key == 'JstfLang:':
            stream = LayoutReader(Reader(reader.line(), reader.limits))
            language = SfdJustificationLanguage(stream.tag())
            if language.tag in languages:
                reader.fail('duplicate JSTF language')
            languages.add(language.tag)
            count = stream.count()
            finish(stream)
            script.languages.append(language)
            priority = None
        elif key == 'JstfPrio:' and language is not None:
            if reader.line():
                reader.fail('unexpected JSTF priority header data')
            if len(language.priorities) >= count:
                reader.fail('too many JSTF priorities')
            priority = SfdJustificationPriority()
            language.priorities.append(priority)
            actions = set()
        elif key in JSTF_ACTIONS and priority is not None:
            if key in actions:
                reader.fail('duplicate JSTF lookup action')
            actions.add(key)
            stream = LayoutReader(Reader(reader.line(), reader.limits))
            values = []
            while stream.peek():
                values.append(stream.quoted())
            setattr(priority, JSTF_ACTIONS[key], values)
        else:
            reader.fail(f'unexpected JSTF record {key!r}')
        key = reader.word()
        if not key:
            reader.fail('missing EndJustify')


def justification_record(reader, key):
    start = reader.pos
    read_justification(reader)
    return SfdRecord(key, reader.data[start : reader.pos].strip())


def decode_justification(item):
    if item.keyword != 'Justify:':
        raise SfdParseError('unexpected justification record kind')
    reader = Reader(item.value)
    result = read_justification(reader)
    if reader.word():
        reader.fail('trailing justification data')
    return result


def encode_justification(value):
    if not value.scripts:
        raise SfdValidationError('justification requires at least one script')
    parts = []
    for script in value.scripts:
        parts.append((b'Justify: ' if parts else b'') + tag(script.tag))
        if script.extenders is not None:
            parts.append(b'JstfExtender: ' + name_text(script.extenders))
        for language in script.languages:
            parts.append(b'JstfLang: ' + tag(language.tag) + b' ' + str(len(language.priorities)).encode())
            for priority in language.priorities:
                parts.append(b'JstfPrio:')
                for key, attribute in JSTF_ACTIONS.items():
                    names = getattr(priority, attribute)
                    if names is not None:
                        parts.append(key.encode() + b' ' + b' '.join(quote(name) for name in names))
    parts.append(b'EndJustify')
    item = SfdRecord('Justify:', b'\n'.join(parts))
    try:
        parsed = decode_justification(item)
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
    if parsed != value:
        raise SfdValidationError('justification fields would change interpretation when written')
    return item


def justification_references(value):
    glyphs = []
    lookups = []
    for script in value.scripts:
        glyphs.extend(script.extenders or [])
        for language in script.languages:
            for priority in language.priorities:
                for key, attribute in JSTF_ACTIONS.items():
                    lookups.extend((name, key.startswith('JstfMax')) for name in getattr(priority, attribute) or [])
    return glyphs, lookups


def justification_identity(item):
    value = decode_justification(item)
    return ('Justify:', [(script.tag, [lang.tag for lang in script.languages]) for script in value.scripts])
