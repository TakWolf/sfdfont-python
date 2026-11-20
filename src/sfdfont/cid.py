from __future__ import annotations

from copy import copy, deepcopy
from typing import Any


class SfdCidInfo:
    registry: str
    ordering: str
    supplement: int
    version: float

    def __init__(
        self,
        registry: str = 'Adobe',
        ordering: str = 'Identity',
        supplement: int = 0,
        version: float = 0,
    ) -> None:
        self.registry = registry
        self.ordering = ordering
        self.supplement = supplement
        self.version = version

    def __copy__(self) -> SfdCidInfo:
        return SfdCidInfo(self.registry, self.ordering, self.supplement, self.version)

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdCidInfo:
        result = copy(self)
        memo[id(self)] = result
        result.registry = deepcopy(self.registry, memo)
        result.ordering = deepcopy(self.ordering, memo)
        result.supplement = deepcopy(self.supplement, memo)
        result.version = deepcopy(self.version, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdCidInfo):
            return NotImplemented
        return (
            self.registry == other.registry
            and self.ordering == other.ordering
            and self.supplement == other.supplement
            and self.version == other.version
        )

    def copy(self) -> SfdCidInfo:
        return copy(self)

    def deepcopy(self) -> SfdCidInfo:
        return deepcopy(self)
