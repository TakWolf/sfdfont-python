from sfdfont._reader import Reader
from sfdfont.record import SfdRecord

BASE_KEYS = {'BaseHoriz:', 'BaseVert:'}
EXTENDED_KEYS = BASE_KEYS | {'Justify:', 'MacFeat:'}


def base_record(reader: Reader, key: str) -> SfdRecord:
    from sfdfont._baselines import baseline_record

    return baseline_record(reader, key)


def justify_record(reader: Reader, key: str) -> SfdRecord:
    from sfdfont._justification import justification_record

    return justification_record(reader, key)


def mac_features_record(reader: Reader, key: str) -> SfdRecord:
    from sfdfont._mac_features import mac_features_record as read_record

    return read_record(reader, key)
