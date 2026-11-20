from __future__ import annotations

from copy import copy, deepcopy
from os import PathLike
from typing import Any, BinaryIO

from sfdfont.glyph import SfdGlyph
from sfdfont.layer import SfdLayerInfo
from sfdfont.limits import SfdReadLimits
from sfdfont.metadata import SfdMetadata


class SfdFont:
    version: str
    metadata: SfdMetadata
    layer_infos: list[SfdLayerInfo]
    glyphs: list[SfdGlyph]
    encoding_size: int

    def __init__(
        self,
        version: str = '3.2',
        metadata: SfdMetadata | None = None,
        layer_infos: list[SfdLayerInfo] | None = None,
        glyphs: list[SfdGlyph] | None = None,
        encoding_size: int = 0x110000,
    ) -> None:
        self.version = version
        self.metadata = metadata if metadata is not None else SfdMetadata()
        self.layer_infos = (
            layer_infos if layer_infos is not None else [SfdLayerInfo(0, name='Back', background=True), SfdLayerInfo(1)]
        )
        self.glyphs = glyphs if glyphs is not None else []
        self.encoding_size = encoding_size

    def __copy__(self) -> SfdFont:
        return SfdFont(
            self.version,
            self.metadata,
            self.layer_infos,
            self.glyphs,
            self.encoding_size,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdFont:
        copied = copy(self)
        memo[id(self)] = copied
        copied.version = deepcopy(self.version, memo)
        copied.metadata = deepcopy(self.metadata, memo)
        copied.layer_infos = deepcopy(self.layer_infos, memo)
        copied.glyphs = deepcopy(self.glyphs, memo)
        copied.encoding_size = deepcopy(self.encoding_size, memo)
        return copied

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdFont):
            return NotImplemented
        return (
            self.version == other.version
            and self.metadata == other.metadata
            and self.layer_infos == other.layer_infos
            and self.glyphs == other.glyphs
            and self.encoding_size == other.encoding_size
        )

    def __repr__(self) -> str:
        return (
            f'SfdFont('
            f'version={self.version!r}, '
            f'metadata={self.metadata!r}, '
            f'layer_infos={self.layer_infos!r}, '
            f'glyphs={self.glyphs!r}, '
            f'encoding_size={self.encoding_size!r}'
            f')'
        )

    @staticmethod
    def parse(stream: bytes | bytearray | BinaryIO, *, limits: SfdReadLimits | None = None) -> SfdFont:
        from sfdfont._parser import parse_font

        return parse_font(stream, limits)

    @staticmethod
    def parse_text(text: str, *, limits: SfdReadLimits | None = None) -> SfdFont:
        return SfdFont.parse(text.encode('utf-8'), limits=limits)

    @staticmethod
    def load(file_path: str | PathLike[str], *, limits: SfdReadLimits | None = None) -> SfdFont:
        with open(file_path, 'rb') as stream:
            return SfdFont.parse(stream, limits=limits)

    def find_glyphs_by_unicode(self, unicode: int) -> list[SfdGlyph]:
        return [
            glyph
            for glyph in self.glyphs
            if glyph.unicode == unicode
            or any(alt.unicode == unicode and alt.variation_selector == -1 for alt in glyph.alternate_unicodes)
        ]

    def find_glyphs_by_name(self, name: str) -> list[SfdGlyph]:
        return [glyph for glyph in self.glyphs if glyph.name == name]

    def copy(self) -> SfdFont:
        return copy(self)

    def deepcopy(self) -> SfdFont:
        return deepcopy(self)
