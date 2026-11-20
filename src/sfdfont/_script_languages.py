from sfdfont._layout import LayoutReader
from sfdfont._layout_models import tag
from sfdfont._reader import Reader
from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.record import SfdRecord
from sfdfont.script_languages import SfdScriptLanguage, SfdScriptLanguages


def script_tag(stream):
    if stream.peek() == b"'":
        value = stream.tag()
    else:
        data = b''.join(stream.reader.char() for _ in range(4))
        try:
            value = data.decode('ascii')
        except UnicodeDecodeError:
            stream.reader.fail('non-ASCII script language tag')
    if len(value) != 4 or not all(32 <= ord(char) <= 126 for char in value):
        stream.reader.fail('script language tag requires four printable ASCII bytes')
    return value


def read_script_languages(reader):
    stream = LayoutReader(reader)
    result = SfdScriptLanguages()
    for _ in range(stream.integer(maximum=32767)):
        scripts = []
        for _ in range(stream.count()):
            script = script_tag(stream)
            languages = [script_tag(stream) for _ in range(stream.count())]
            scripts.append(SfdScriptLanguage(script, languages))
        result.lists.append(scripts)
    return result


def script_languages_record(reader, key):
    start = reader.pos
    read_script_languages(reader)
    return SfdRecord(key, reader.data[start : reader.pos].lstrip())


def decode_script_languages(item):
    if item.keyword != 'ScriptLang:':
        raise SfdParseError('unexpected script language record kind')
    reader = Reader(item.value)
    result = read_script_languages(reader)
    if reader.word():
        reader.fail('trailing script language data')
    return result


def encode_script_languages(value):
    from sfdfont._validation import number

    number(len(value.lists), 'script language list count', 0, 32767)
    data = [str(len(value.lists)).encode()]
    for scripts in value.lists:
        parts = [str(len(scripts)).encode()]
        for entry in scripts:
            parts.extend([tag(entry.script), str(len(entry.languages)).encode()])
            parts.extend(tag(language) for language in entry.languages)
        data.append(b' '.join(parts))
    result = SfdRecord('ScriptLang:', b'\n'.join(data))
    try:
        if decode_script_languages(result) != value:
            raise SfdValidationError('script language fields would change interpretation')
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
    return result


def validate_script_languages(font, contexts, kerns, psts):
    from sfdfont._legacy_layout import LEGACY_KERN_KEYS, decode_anchor_classes, decode_pairs

    items = [item for item in font.metadata.records if item.keyword == 'ScriptLang:']
    if len(items) > 1:
        raise SfdValidationError('duplicate ScriptLang table')
    if not items:
        return
    table = decode_script_languages(items[0])
    indices = [value.binding.script_language_index for value in psts if value.keyword != 'LCarets:']
    indices.extend(value.script_language_index for value in [*contexts, *kerns] if value.subtable is None)
    for item in font.metadata.records:
        if item.keyword == 'AnchorClass:':
            indices.extend(entry.script_language_index for entry in decode_anchor_classes(item).classes)
    for glyph in font.iter_glyphs():
        for item in [*glyph.records, *(r for layer in glyph.layers for r in layer.records)]:
            if item.keyword in LEGACY_KERN_KEYS:
                indices.extend(pair.script_language_index for pair in decode_pairs(item).pairs)
    if any(index is not None and index not in (0xFFFE, 0xFFFF) and index >= len(table.lists) for index in indices):
        raise SfdValidationError('script language index outside ScriptLang table')
