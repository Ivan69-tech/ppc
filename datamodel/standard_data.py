from dataclasses import dataclass

# Export explicite de toutes les classes du module
__all__ = ["Bess", "Pv", "StandardData"]


@dataclass(frozen=True)
class Bess:
    p: float
    q: float
    soc: float
    timestamp: float


@dataclass(frozen=True)
class Pv:
    p: float
    q: float
    timestamp: float


@dataclass(frozen=True)
class StandardData:
    bess: Bess
    pv: Pv
