from __future__ import annotations

from collections.abc import Iterator
from copy import copy, deepcopy
from os import PathLike
from typing import Any, BinaryIO

from sfdfont.bitmap import SfdBitmapStrike
from sfdfont.cid import SfdCidInfo
from sfdfont.glyph import SfdGlyph
from sfdfont.layer import SfdLayerInfo
from sfdfont.layout import SfdLookup
from sfdfont.limits import SfdReadLimits
from sfdfont.metadata import SfdMetadata
from sfdfont.outline import SfdContour
from sfdfont.payload import SfdPayload
from sfdfont.variation import SfdMultipleMaster


class SfdFont:
    version: str
    metadata: SfdMetadata
    layer_infos: list[SfdLayerInfo]
    glyphs: list[SfdGlyph]
    encoding_size: int
    bitmap_strikes: list[SfdBitmapStrike]
    payloads: list[SfdPayload]
    guidelines: list[SfdContour]
    grid_quadratic: bool
    _snapshot: SfdFont | None
    encoding_aliases: dict[int, int]
    multilayer: bool
    multiple_master: SfdMultipleMaster | None
    cid: SfdCidInfo | None
    subfonts: list[SfdFont]

    def __init__(
        self,
        version: str = '3.2',
        metadata: SfdMetadata | None = None,
        layer_infos: list[SfdLayerInfo] | None = None,
        glyphs: list[SfdGlyph] | None = None,
        encoding_size: int = 0x110000,
        bitmap_strikes: list[SfdBitmapStrike] | None = None,
        payloads: list[SfdPayload] | None = None,
        guidelines: list[SfdContour] | None = None,
        grid_quadratic: bool = False,
        _snapshot: SfdFont | None = None,
        encoding_aliases: dict[int, int] | None = None,
        multilayer: bool = False,
        multiple_master: SfdMultipleMaster | None = None,
        cid: SfdCidInfo | None = None,
        subfonts: list[SfdFont] | None = None,
    ) -> None:
        self.version = version
        self.metadata = metadata if metadata is not None else SfdMetadata()
        self.layer_infos = (
            layer_infos if layer_infos is not None else [SfdLayerInfo(0, name='Back', background=True), SfdLayerInfo(1)]
        )
        self.glyphs = glyphs if glyphs is not None else []
        self.encoding_size = encoding_size
        self.bitmap_strikes = bitmap_strikes if bitmap_strikes is not None else []
        self.payloads = payloads if payloads is not None else []
        self.guidelines = guidelines if guidelines is not None else []
        self.grid_quadratic = grid_quadratic
        self._snapshot = _snapshot
        self.encoding_aliases = encoding_aliases if encoding_aliases is not None else {}
        self.multilayer = multilayer
        self.multiple_master = multiple_master
        self.cid = cid
        self.subfonts = subfonts if subfonts is not None else []

    def __copy__(self) -> SfdFont:
        return SfdFont(
            self.version,
            self.metadata,
            self.layer_infos,
            self.glyphs,
            self.encoding_size,
            self.bitmap_strikes,
            self.payloads,
            self.guidelines,
            self.grid_quadratic,
            self._snapshot,
            self.encoding_aliases,
            self.multilayer,
            self.multiple_master,
            self.cid,
            self.subfonts,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdFont:
        copied = copy(self)
        memo[id(self)] = copied
        copied.version = deepcopy(self.version, memo)
        copied.metadata = deepcopy(self.metadata, memo)
        copied.layer_infos = deepcopy(self.layer_infos, memo)
        copied.glyphs = deepcopy(self.glyphs, memo)
        copied.encoding_size = deepcopy(self.encoding_size, memo)
        copied.bitmap_strikes = deepcopy(self.bitmap_strikes, memo)
        copied.payloads = deepcopy(self.payloads, memo)
        copied.guidelines = deepcopy(self.guidelines, memo)
        copied.grid_quadratic = deepcopy(self.grid_quadratic, memo)
        copied._snapshot = deepcopy(self._snapshot, memo)
        copied.encoding_aliases = deepcopy(self.encoding_aliases, memo)
        copied.multilayer = deepcopy(self.multilayer, memo)
        copied.multiple_master = deepcopy(self.multiple_master, memo)
        copied.cid = deepcopy(self.cid, memo)
        copied.subfonts = deepcopy(self.subfonts, memo)
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
            and self.bitmap_strikes == other.bitmap_strikes
            and self.payloads == other.payloads
            and self.guidelines == other.guidelines
            and self.grid_quadratic == other.grid_quadratic
            and self.encoding_aliases == other.encoding_aliases
            and self.multilayer == other.multilayer
            and self.multiple_master == other.multiple_master
            and self.cid == other.cid
            and self.subfonts == other.subfonts
        )

    def __repr__(self) -> str:
        return (
            f'SfdFont('
            f'version={self.version!r}, '
            f'metadata={self.metadata!r}, '
            f'layer_infos={self.layer_infos!r}, '
            f'glyphs={self.glyphs!r}, '
            f'encoding_size={self.encoding_size!r}, '
            f'bitmap_strikes={self.bitmap_strikes!r}, '
            f'payloads={self.payloads!r}, '
            f'guidelines={self.guidelines!r}, '
            f'grid_quadratic={self.grid_quadratic!r}, '
            f'encoding_aliases={self.encoding_aliases!r}, '
            f'multilayer={self.multilayer!r}, '
            f'multiple_master={self.multiple_master!r}, '
            f'cid={self.cid!r}, '
            f'subfonts={self.subfonts!r}'
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

    def iter_glyphs(self) -> Iterator[SfdGlyph]:
        """Iterate ordinary glyphs or CID subfonts in their stored order."""
        if self.subfonts:
            for subfont in self.subfonts:
                yield from subfont.glyphs
        else:
            yield from self.glyphs

    def find_glyphs_by_unicode(self, unicode: int) -> list[SfdGlyph]:
        return [
            glyph
            for glyph in self.iter_glyphs()
            if glyph.unicode == unicode
            or any(alt.unicode == unicode and alt.variation_selector == -1 for alt in glyph.alternate_unicodes)
        ]

    def find_glyphs_by_name(self, name: str) -> list[SfdGlyph]:
        return [glyph for glyph in self.iter_glyphs() if glyph.name == name]

    def find_glyph_by_encoding(self, encoding: int) -> SfdGlyph | None:
        """Find an encoding slot, including DupEnc aliases; slots are not Unicode."""
        if self.subfonts:
            for subfont in self.subfonts:
                glyph = subfont.find_glyph_by_encoding(encoding)
                if glyph is not None:
                    return glyph
            return None
        if encoding in self.encoding_aliases:
            target = self.encoding_aliases[encoding]
            return next((glyph for glyph in self.iter_glyphs() if glyph.glyph_id == target), None)
        return next((glyph for glyph in self.iter_glyphs() if glyph.encoding == encoding and encoding != -1), None)

    def find_lookup(self, name: str) -> SfdLookup | None:
        """Decode an independent lookup value; use set_lookup() to apply edits."""
        for record in self.metadata.records:
            if record.keyword == 'Lookup:':
                lookup = SfdLookup.from_record(record)
                if lookup.name == name:
                    return lookup
        return None

    def set_lookup(self, lookup: SfdLookup) -> None:
        """Replace the named lookup or append a new definition, preserving other records."""
        replacement = lookup.to_record()
        for index, record in enumerate(self.metadata.records):
            if record.keyword == 'Lookup:' and SfdLookup.from_record(record).name == lookup.name:
                self.metadata.records[index] = replacement
                return
        self.metadata.records.append(replacement)

    def validate(self) -> None:
        from sfdfont._validation import validate

        validate(self)

    def dump_to_bytes(self) -> bytes:
        from sfdfont._writer import dump_font

        return dump_font(self)

    def dump(self, stream: BinaryIO) -> None:
        data = self.dump_to_bytes()
        position = 0
        while position < len(data):
            written = stream.write(data[position:])
            if written is None or written <= 0 or written > len(data) - position:
                raise OSError('binary stream made no write progress')
            position += written

    def save(self, file_path: str | PathLike[str]) -> None:
        # Complete validation/serialization before opening the destination.
        data = self.dump_to_bytes()
        with open(file_path, 'wb') as stream:
            stream.write(data)

    def copy(self) -> SfdFont:
        return copy(self)

    def deepcopy(self) -> SfdFont:
        return deepcopy(self)
