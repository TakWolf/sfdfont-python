from sfdfont._gasp import decode_gasp
from sfdfont._size import decode_design_size
from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.record import SfdRecord

INFO_KEYS = {'GaspTable:', 'DesignSize:'}


def decode_info(item):
    if item.keyword == 'GaspTable:':
        return decode_gasp(item)
    if item.keyword == 'DesignSize:':
        return decode_design_size(item)
    raise SfdParseError('unexpected font information record kind')


def info_record(reader, key):
    item = SfdRecord(key, reader.line())
    decode_info(item)
    return item


def validate_info(records):
    seen = set()
    try:
        for item in records:
            if item.keyword in INFO_KEYS:
                if item.keyword in seen:
                    raise SfdValidationError(f'duplicate font information record {item.keyword}')
                seen.add(item.keyword)
                decode_info(item)
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
