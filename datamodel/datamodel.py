from dataclasses import dataclass
from .standard_data import Bess, Pv


@dataclass(frozen=True)
class DataModel:
    bess: Bess
    pv: Pv


@dataclass(frozen=True)
class Command:
    pSp: float
    qSp: float
