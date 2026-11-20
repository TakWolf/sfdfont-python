from __future__ import annotations

from copy import copy, deepcopy
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sfdfont.font import SfdFont


class SfdMacName:
    encoding: int
    language: int
    data: bytes

    def __init__(
        self,
        encoding: int = 0,
        language: int = 0,
        data: bytes = b'',
    ) -> None:
        self.encoding = encoding
        self.language = language
        self.data = data

    def __copy__(self) -> SfdMacName:
        return SfdMacName(
            self.encoding,
            self.language,
            self.data,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdMacName:
        result = copy(self)
        memo[id(self)] = result
        result.encoding = deepcopy(self.encoding, memo)
        result.language = deepcopy(self.language, memo)
        result.data = deepcopy(self.data, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdMacName):
            return NotImplemented
        return self.encoding == other.encoding and self.language == other.language and self.data == other.data

    def copy(self) -> SfdMacName:
        return copy(self)

    def deepcopy(self) -> SfdMacName:
        return deepcopy(self)


class SfdAxisMap:
    points: list[tuple[float, float]]
    names: list[SfdMacName]

    def __init__(
        self,
        points: list[tuple[float, float]] | None = None,
        names: list[SfdMacName] | None = None,
    ) -> None:
        self.points = points if points is not None else []
        self.names = names if names is not None else []

    def __copy__(self) -> SfdAxisMap:
        return SfdAxisMap(
            self.points,
            self.names,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdAxisMap:
        result = copy(self)
        memo[id(self)] = result
        result.points = deepcopy(self.points, memo)
        result.names = deepcopy(self.names, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdAxisMap):
            return NotImplemented
        return self.points == other.points and self.names == other.names

    def copy(self) -> SfdAxisMap:
        return copy(self)

    def deepcopy(self) -> SfdAxisMap:
        return deepcopy(self)


class SfdNamedInstance:
    coordinates: list[float]
    names: list[SfdMacName]

    def __init__(
        self,
        coordinates: list[float] | None = None,
        names: list[SfdMacName] | None = None,
    ) -> None:
        self.coordinates = coordinates if coordinates is not None else []
        self.names = names if names is not None else []

    def __copy__(self) -> SfdNamedInstance:
        return SfdNamedInstance(
            self.coordinates,
            self.names,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdNamedInstance:
        result = copy(self)
        memo[id(self)] = result
        result.coordinates = deepcopy(self.coordinates, memo)
        result.names = deepcopy(self.names, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdNamedInstance):
            return NotImplemented
        return self.coordinates == other.coordinates and self.names == other.names

    def copy(self) -> SfdNamedInstance:
        return copy(self)

    def deepcopy(self) -> SfdNamedInstance:
        return deepcopy(self)


class SfdMultipleMaster:
    axes: list[str]
    positions: list[list[float]]
    weights: list[float]
    axis_maps: list[SfdAxisMap]
    instances: list[SfdFont]
    apple: bool
    named_instances: list[SfdNamedInstance]
    cdv: bytes | None
    ndv: bytes | None

    def __init__(
        self,
        axes: list[str] | None = None,
        positions: list[list[float]] | None = None,
        weights: list[float] | None = None,
        axis_maps: list[SfdAxisMap] | None = None,
        instances: list[SfdFont] | None = None,
        apple: bool = False,
        named_instances: list[SfdNamedInstance] | None = None,
        cdv: bytes | None = None,
        ndv: bytes | None = None,
    ) -> None:
        self.axes = axes if axes is not None else []
        self.positions = positions if positions is not None else []
        self.weights = weights if weights is not None else []
        self.axis_maps = axis_maps if axis_maps is not None else []
        self.instances = instances if instances is not None else []
        self.apple = apple
        self.named_instances = named_instances if named_instances is not None else []
        self.cdv = cdv
        self.ndv = ndv

    def __copy__(self) -> SfdMultipleMaster:
        return SfdMultipleMaster(
            self.axes,
            self.positions,
            self.weights,
            self.axis_maps,
            self.instances,
            self.apple,
            self.named_instances,
            self.cdv,
            self.ndv,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdMultipleMaster:
        result = copy(self)
        memo[id(self)] = result
        result.axes = deepcopy(self.axes, memo)
        result.positions = deepcopy(self.positions, memo)
        result.weights = deepcopy(self.weights, memo)
        result.axis_maps = deepcopy(self.axis_maps, memo)
        result.instances = deepcopy(self.instances, memo)
        result.apple = deepcopy(self.apple, memo)
        result.named_instances = deepcopy(self.named_instances, memo)
        result.cdv = deepcopy(self.cdv, memo)
        result.ndv = deepcopy(self.ndv, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdMultipleMaster):
            return NotImplemented
        return (
            self.axes == other.axes
            and self.positions == other.positions
            and self.weights == other.weights
            and self.axis_maps == other.axis_maps
            and self.instances == other.instances
            and self.apple == other.apple
            and self.named_instances == other.named_instances
            and self.cdv == other.cdv
            and self.ndv == other.ndv
        )

    def copy(self) -> SfdMultipleMaster:
        return copy(self)

    def deepcopy(self) -> SfdMultipleMaster:
        return deepcopy(self)
