from sfdfont._feature_names import decode_feature_names
from sfdfont._gasp import decode_gasp
from sfdfont._metrics import SCALAR_KEYS, decode_metric, metric_key
from sfdfont._os2 import OS2_KEYS, decode_os2, vendor_record
from sfdfont._size import decode_design_size
from sfdfont._tex import decode_tex_data
from sfdfont._woff import decode_woff_metadata
from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.record import SfdRecord

INFO_KEYS = SCALAR_KEYS | OS2_KEYS | {'GaspTable:', 'DesignSize:', 'OtfFeatName:', 'TeXData:', 'woffMetadata:'}


def decode_info(item):
    if item.keyword == 'woffMetadata:':
        return decode_woff_metadata(item)
    if item.keyword == 'TeXData:':
        return decode_tex_data(item)
    if item.keyword == 'OtfFeatName:':
        return decode_feature_names(item)
    if item.keyword == 'GaspTable:':
        return decode_gasp(item)
    if item.keyword == 'DesignSize:':
        return decode_design_size(item)
    if item.keyword in SCALAR_KEYS:
        return decode_metric(item)
    if item.keyword in OS2_KEYS:
        return decode_os2(item)
    raise SfdParseError('unexpected font information record kind')


def info_record(reader, key):
    if key == 'OS2Vendor:':
        return vendor_record(reader, key)
    item = SfdRecord(key, reader.line())
    decode_info(item)
    return item


def validate_info(records):
    seen = set()
    try:
        for item in records:
            if item.keyword in INFO_KEYS:
                key = metric_key(item.keyword)
                if item.keyword == 'OtfFeatName:':
                    key = (key, decode_feature_names(item).tag)
                if key in seen:
                    raise SfdValidationError(f'duplicate font information record {item.keyword}')
                seen.add(key)
                decode_info(item)
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
