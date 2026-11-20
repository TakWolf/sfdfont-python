from typing import BinaryIO

from sfdfont.error import SfdLimitError, SfdParseError
from sfdfont.limits import SfdReadLimits


class Reader:
    def __init__(self, stream: bytes | bytearray | BinaryIO, limits: SfdReadLimits | None = None) -> None:
        self.limits = limits or SfdReadLimits()
        if isinstance(stream, (bytes, bytearray)):
            if len(stream) > self.limits.max_bytes:
                raise SfdLimitError('max_bytes exceeded')
            self.data = bytes(stream)
        else:
            parts = []
            size = 0
            while True:
                part = stream.read(min(65536, self.limits.max_bytes + 1 - size))
                if not isinstance(part, bytes):
                    raise TypeError('SFD input must be a binary stream')
                if not part:
                    break
                parts.append(part)
                size += len(part)
                if size > self.limits.max_bytes:
                    raise SfdLimitError('max_bytes exceeded')
            self.data = b''.join(parts)
        if len(self.data) > self.limits.max_bytes:
            raise SfdLimitError('max_bytes exceeded')
        self.pos = 0
        self.payload_bytes = 0
        self.point_count = 0
        self.glyph_count = 0
        self.next_gid = 0

    def fail(self, message: str, kind: type[SfdParseError] = SfdParseError) -> None:
        raise kind(message, offset=self.pos, line=self.data.count(b'\n', 0, self.pos) + 1)

    def char(self) -> bytes:
        while self.data[self.pos : self.pos + 2] == b'\\\n':
            self.pos += 2
        value = self.data[self.pos : self.pos + 1]
        self.pos += bool(value)
        return value

    def whitespace(self) -> None:
        while self.pos < len(self.data):
            if self.data[self.pos : self.pos + 2] == b'\\\n':
                self.pos += 2
            elif self.data[self.pos] in b' \t\r\n\f\v':
                self.pos += 1
            else:
                break

    def word(self) -> str:
        self.whitespace()
        result = bytearray()
        while self.pos < len(self.data):
            if self.data[self.pos : self.pos + 2] == b'\\\n':
                self.pos += 2
            elif self.data[self.pos] in b' \t\r\n\f\v':
                break
            else:
                result.append(self.data[self.pos])
                self.pos += 1
        try:
            return result.decode('ascii')
        except UnicodeDecodeError:
            self.fail('non-ASCII keyword')
        raise AssertionError

    def line(self) -> bytes:
        result = bytearray()
        while True:
            char = self.char()
            if char in (b'', b'\n'):
                break
            result.extend(char)
        return bytes(result).rstrip(b'\r').strip(b' \t')

    def inline_word(self) -> str:
        saved = self.pos
        while self.pos < len(self.data) and self.data[self.pos] in b' \t':
            self.pos += 1
        if self.pos == len(self.data) or self.data[self.pos] in b'\r\n':
            self.pos = saved
            return ''
        return self.word()

    def escaped_line(self) -> bytes:
        result = bytearray()
        while True:
            char = self.char()
            if char in (b'', b'\r', b'\n'):
                break
            if char == b'\\':
                # An escaped backslash before a newline is literal, not a wrap.
                char = self.data[self.pos : self.pos + 1]
                if not char:
                    self.fail('truncated line escape')
                self.pos += 1
                char = b'\n' if char == b'n' else char
            result.extend(char)
        return bytes(result).lstrip(b' \t')

    def ascii85(self, length: int) -> bytes:
        if length < 0:
            self.fail('negative payload length')
        self.payload_bytes += length
        if self.payload_bytes > self.limits.max_payload_bytes:
            self.fail('max_payload_bytes exceeded', SfdLimitError)
        result = bytearray()

        def digit() -> int:
            # Deliberately bypass char(): backslashes are ASCII85 digits.
            while self.pos < len(self.data) and self.data[self.pos] in b' \t\r\n\f\v':
                self.pos += 1
            if self.pos == len(self.data):
                self.fail('truncated ASCII85 payload')
            value = self.data[self.pos]
            self.pos += 1
            return value

        while len(result) < length:
            first = digit()
            if first == ord('z'):
                block = b'\0' * 4
            else:
                digits = [first] + [digit() for _ in range(4)]
                if any(not 33 <= value <= 117 for value in digits):
                    self.fail('invalid ASCII85 digit')
                number = 0
                for value in digits:
                    number = number * 85 + value - 33
                if number > 0xFFFFFFFF:
                    self.fail('ASCII85 group overflow')
                block = number.to_bytes(4, 'big')
            result.extend(block)
        return bytes(result[:length])


def encode_ascii85(data: bytes) -> bytes:
    import base64

    padded = data + b'\0' * (-len(data) % 4)
    return base64.a85encode(padded, wrapcol=75)
