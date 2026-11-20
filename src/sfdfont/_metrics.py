import re

from sfdfont.error import SfdParseError
from sfdfont.metrics import SfdFontMetric
from sfdfont.record import SfdRecord

SIGNED_KEYS = {
    'TTFWeight:',
    'TTFWidth:',
    'LineGap:',
    'VLineGap:',
    'FSType:',
    'MacStyle:',
    'OS2Version:',
    'HheadAscent:',
    'HheadDescent:',
    'OS2TypoAscent:',
    'OS2TypoDescent:',
    'OS2TypoLinegap:',
    'OS2WinAscent:',
    'OS2WinDescent:',
    'OS2SubXSize:',
    'OS2SubYSize:',
    'OS2SubXOff:',
    'OS2SubYOff:',
    'OS2SupXSize:',
    'OS2SupYSize:',
    'OS2SupXOff:',
    'OS2SupYOff:',
    'OS2StrikeYSize:',
    'OS2StrikeYPos:',
    'OS2CapHeight:',
    'OS2XHeight:',
    'OS2FamilyClass:',
}
BOOL_KEYS = {
    'OS2_WeightWidthSlopeOnly:',
    'OS2_UseTypoMetrics:',
    'HheadAOffset:',
    'HheadDOffset:',
    'OS2TypoAOffset:',
    'OS2TypoDOffset:',
    'OS2WinAOffset:',
    'OS2WinDOffset:',
}
ALIASES = {
    'PfmWeight:': 'TTFWeight:',
    'HHeadAscent:': 'HheadAscent:',
    'HHeadDescent:': 'HheadDescent:',
    'HHeadAOffset:': 'HheadAOffset:',
    'HHeadDOffset:': 'HheadDOffset:',
}
INT32_KEYS = {'woffMajor:', 'woffMinor:'}
SCALAR_KEYS = SIGNED_KEYS | BOOL_KEYS | INT32_KEYS | set(ALIASES) | {'PfmFamily:', 'StyleMap:'}


def metric_key(key):
    return ALIASES.get(key, key)


def signed_short(value):
    if -32768 <= value <= 32767:
        return value
    if 32768 <= value <= 65535:
        return value - 65536
    raise SfdParseError('font metric exceeds 16-bit storage')


def decode_metric(item):
    from sfdfont._parser import integer

    if item.keyword not in SCALAR_KEYS:
        raise SfdParseError('unexpected font metric kind')
    key = metric_key(item.keyword)
    data = item.value.strip()
    if key == 'StyleMap:':
        if not re.fullmatch(rb'#?[+-]?(?:0[xX])?[0-9a-fA-F]{1,8}', data):
            raise SfdParseError('invalid StyleMap hexadecimal value')
        value = int(data.lstrip(b'#'), 16)
        if 0xFFFF8000 <= value <= 0xFFFFFFFF:
            value -= 0x100000000
        value = signed_short(value)
    else:
        value = integer(data)
        if key in SIGNED_KEYS:
            value = signed_short(value)
        elif key in BOOL_KEYS and value not in (0, 1):
            raise SfdParseError('font metric flag must be 0 or 1')
        elif key == 'PfmFamily:':
            if not -128 <= value <= 255:
                raise SfdParseError('PFM family exceeds byte storage')
            value &= 255
        elif key in INT32_KEYS and not -0x80000000 <= value <= 0x7FFFFFFF:
            raise SfdParseError('font metric exceeds 32-bit storage')
    return SfdFontMetric(item.keyword, value)


def encode_metric(value):
    from sfdfont._validation import check, number

    check(value.keyword in SCALAR_KEYS, 'invalid font metric keyword')
    key = metric_key(value.keyword)
    low, high = (-32768, 32767) if key in SIGNED_KEYS | {'StyleMap:'} else (0, 255 if key == 'PfmFamily:' else 1)
    if key in INT32_KEYS:
        low, high = -0x80000000, 0x7FFFFFFF
    number(value.value, 'font metric value', low, high)
    data = f'0x{value.value & 0xFFFFFFFF:04x}'.encode() if key == 'StyleMap:' else str(value.value).encode()
    return SfdRecord(value.keyword, data)
