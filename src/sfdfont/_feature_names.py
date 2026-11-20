from sfdfont._layout import LayoutReader
from sfdfont._layout_models import tag
from sfdfont._reader import Reader
from sfdfont._strings import quote
from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.feature_names import SfdFeatureName, SfdFeatureNames
from sfdfont.record import SfdRecord


def decode_feature_names(item):
    if item.keyword != 'OtfFeatName:':
        raise SfdParseError('unexpected feature name record kind')
    reader = Reader(item.value)
    stream = LayoutReader(reader)
    result = SfdFeatureNames(stream.tag())
    variant = result.tag.startswith('cv')
    seen = set()
    forms = set()
    while stream.peek() and stream.peek() != b'"':
        language = stream.integer()
        if language in seen:
            reader.fail('duplicate feature name language')
        seen.add(language)
        name = SfdFeatureName(language, stream.quoted())
        if variant and stream.peek() == b'"':
            name.tooltip = stream.quoted()
            name.sample = stream.quoted()
            count = stream.integer(maximum=32767)
            name.parameters = [stream.quoted() for _ in range(count)]
        forms.add(name.parameters is not None)
        result.names.append(name)
    if not result.names:
        reader.fail('feature name record requires a language name')
    if len(forms) > 1:
        reader.fail('mixed simple and extended character variant names')
    if variant and True in forms and stream.peek() == b'"':
        result.trailer = stream.quoted()
    if stream.peek():
        reader.fail('trailing feature name data')
    return result


def encode_feature_names(value):
    from sfdfont._validation import check, number

    data = [tag(value.tag)]
    check(bool(value.names), 'feature name record requires a language name')
    variant = value.tag.startswith('cv') and any(
        name.tooltip is not None or name.sample is not None or name.parameters is not None for name in value.names
    )
    for name in value.names:
        number(name.language, 'feature name language', 0, 65535)
        data.extend([str(name.language).encode(), quote(name.name)])
        if variant:
            check(name.tooltip is not None and name.sample is not None, 'character variant requires tooltip and sample')
            check(name.parameters is not None, 'character variant requires a parameter name list')
            number(len(name.parameters), 'feature parameter count', 0, 32767)
            data.extend([quote(name.tooltip), quote(name.sample), str(len(name.parameters)).encode()])
            data.extend(quote(parameter) for parameter in name.parameters)
        else:
            check(
                name.tooltip is None and name.sample is None and name.parameters is None,
                'only character variants can contain extra name fields',
            )
    if value.trailer is not None:
        check(variant, 'only extended character variants can contain a reserved trailer')
        data.append(quote(value.trailer))
    result = SfdRecord('OtfFeatName:', b' '.join(data))
    try:
        if decode_feature_names(result) != value:
            raise SfdValidationError('feature names would change interpretation when written')
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
    return result


def feature_names_identity(item):
    value = decode_feature_names(item)
    return (
        'OtfFeatName:',
        value.tag,
        [(name.language, len(name.parameters) if name.parameters is not None else None) for name in value.names],
        value.trailer,
    )


def feature_names_opaque(records):
    return any(
        item.keyword == 'OtfFeatName:' and decode_feature_names(item).trailer not in (None, '') for item in records
    )
