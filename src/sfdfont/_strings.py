"""FontForge's UTF-7 dialect, including full Base64-group zero padding."""

import base64
import binascii

from sfdfont.error import SfdParseError, SfdValidationError

_BASE64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'


def decode_utf7(value: bytes) -> str:
    try:
        text = value.decode('ascii')
    except UnicodeDecodeError as error:
        raise SfdParseError('non-ASCII data in SFD UTF-7 string') from error
    result = []
    index = 0
    while index < len(text):
        if text[index] != '+':
            result.append(text[index])
            index += 1
            continue
        index += 1
        if text[index : index + 1] == '-':
            result.append('+')
            index += 1
            continue
        start = index
        while index < len(text) and text[index] in _BASE64:
            index += 1
        block = text[start:index]
        try:
            if not block:
                raise ValueError('empty shift sequence')
            raw = base64.b64decode(block + '=' * (-len(block) % 4), validate=True)
            # SFD pads to complete 24-bit groups; UTF-16 uses 16-bit units.
            if len(raw) % 2:
                if raw[-1] != 0:
                    raise ValueError('nonzero UTF-7 padding')
                raw = raw[:-1]
            if raw.endswith(b'\0\0'):
                raw = raw[:-2]
            decoded = raw.decode('utf-16-be')
            if '\0' in decoded:
                raise ValueError('embedded NUL')
            result.append(decoded)
        except (ValueError, binascii.Error, UnicodeError) as error:
            raise SfdParseError('invalid SFD UTF-7 shift sequence') from error
        if text[index : index + 1] == '-':
            index += 1
    decoded = ''.join(result)
    if '\0' in decoded:
        raise SfdParseError('embedded NUL in string')
    return decoded


def encode_utf7(value: str) -> bytes:
    if '\0' in value:
        raise SfdValidationError('SFD strings cannot contain NUL')
    result: list[str] = []
    run: list[str] = []

    def flush(next_char: str = '') -> None:
        if run:
            try:
                raw = ''.join(run).encode('utf-16-be')
            except UnicodeEncodeError as error:
                raise SfdValidationError('unpaired Unicode surrogate') from error
            raw += b'\0' * (-len(raw) % 3)
            result.append('+' + base64.b64encode(raw).decode('ascii'))
            if next_char and next_char in _BASE64 + '-':
                result.append('-')
            run.clear()

    for char in value:
        if ord(char) < 127 and char not in '\n\r\\~+="':
            flush(char)
            result.append(char)
        elif char == '+' and not run:
            result.append('+-')
        else:
            run.append(char)
    flush()
    return ''.join(result).encode('ascii')


def quote(value: str) -> bytes:
    return b'"' + encode_utf7(value) + b'"'


def decode_text(value: bytes) -> str:
    try:
        return value.decode('utf-8')
    except UnicodeDecodeError:
        return value.decode('latin-1')
