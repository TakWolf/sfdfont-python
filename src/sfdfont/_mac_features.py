from sfdfont._family import encode_mac_name, mac_name
from sfdfont._layout import LayoutReader
from sfdfont._reader import Reader
from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.mac_features import SfdMacFeature, SfdMacFeatures, SfdMacSetting
from sfdfont.record import SfdRecord


def finish(stream):
    if stream.peek():
        stream.reader.fail('trailing Mac feature header data')


def read_mac_features(reader):
    result = SfdMacFeatures()
    key = 'MacFeat:'
    names = None
    feature = None
    features = set()
    settings = set()
    while True:
        if key in ('MacFeat:', 'MacSetting:', 'EndMacFeatures') and names is not None and not names:
            reader.fail('Mac feature or setting requires a name')
        if key == 'EndMacFeatures':
            return result
        if key == 'MacFeat:':
            stream = LayoutReader(Reader(reader.line(), reader.limits))
            feature = SfdMacFeature(stream.integer(), bool(stream.integer(maximum=1)), stream.integer(maximum=255))
            if feature.feature in features:
                reader.fail('duplicate Mac feature number')
            features.add(feature.feature)
            finish(stream)
            result.features.append(feature)
            names = feature.names
            settings = set()
        elif key == 'MacSetting:' and feature is not None:
            stream = LayoutReader(Reader(reader.line(), reader.limits))
            setting = SfdMacSetting(stream.integer())
            if setting.setting in settings:
                reader.fail('duplicate Mac setting number')
            settings.add(setting.setting)
            finish(stream)
            feature.settings.append(setting)
            names = setting.names
        elif key == 'MacName:' and names is not None:
            names.append(mac_name(reader.line()))
        else:
            reader.fail(f'unexpected Mac feature record {key!r}')
        key = reader.word()
        if not key:
            reader.fail('missing EndMacFeatures')


def mac_features_record(reader, key):
    start = reader.pos
    read_mac_features(reader)
    return SfdRecord(key, reader.data[start : reader.pos].strip())


def decode_mac_features(item):
    if item.keyword != 'MacFeat:':
        raise SfdParseError('unexpected Mac feature record kind')
    reader = Reader(item.value)
    result = read_mac_features(reader)
    if reader.word():
        reader.fail('trailing Mac feature data')
    return result


def encode_mac_features(value):
    from sfdfont._validation import check, number

    check(bool(value.features), 'Mac feature table requires at least one feature')
    parts = []
    for feature in value.features:
        number(feature.feature, 'Mac feature', 0, 65535)
        number(feature.default_setting, 'Mac default setting', 0, 255)
        check(isinstance(feature.is_mutex, bool), 'invalid Mac feature mutex flag')
        parts.append(
            (b'MacFeat: ' if parts else b'')
            + f'{feature.feature} {int(feature.is_mutex)} {feature.default_setting}'.encode()
        )
        parts.extend(b'MacName: ' + encode_mac_name(name) for name in feature.names)
        for setting in feature.settings:
            number(setting.setting, 'Mac setting', 0, 65535)
            parts.append(b'MacSetting: ' + str(setting.setting).encode())
            parts.extend(b'MacName: ' + encode_mac_name(name) for name in setting.names)
    parts.append(b'EndMacFeatures')
    item = SfdRecord('MacFeat:', b'\n'.join(parts))
    try:
        parsed = decode_mac_features(item)
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
    if parsed != value:
        raise SfdValidationError('Mac feature fields would change interpretation when written')
    return item


def mac_features_identity(item):
    value = decode_mac_features(item)

    def names(items):
        return [(name.encoding, name.language) for name in items]

    return (
        'MacFeat:',
        [
            (
                feature.feature,
                names(feature.names),
                [(setting.setting, names(setting.names)) for setting in feature.settings],
            )
            for feature in value.features
        ],
    )


def validate_mac_features(font):
    seen = False
    try:
        for item in font.metadata.records:
            if item.keyword == 'MacFeat:':
                if seen:
                    raise SfdValidationError('duplicate Mac feature table')
                seen = True
                decode_mac_features(item)
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
