class SfdError(Exception):
    """Base exception for SFD operations."""


class SfdParseError(SfdError):
    def __init__(self, message: str, *, offset: int | None = None, line: int | None = None) -> None:
        self.offset = offset
        self.line = line
        location = f' at line {line}, byte {offset}' if line is not None else ''
        super().__init__(message + location)


class SfdUnsupportedError(SfdParseError):
    """The input uses an unimplemented format or structure."""


class SfdValidationError(SfdError, ValueError):
    """The current model cannot be written as supported SFD."""


class SfdLimitError(SfdParseError):
    """A configured resource limit was exceeded."""
