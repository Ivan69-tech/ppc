from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum
from .standard_data import Bess, Pv


class EquipmentType(Enum):
    """Type d'équipement cible pour une commande."""

    BESS = "bess"
    PV = "pv"


@dataclass(frozen=True)
class SystemObs:
    bess: Optional[List[Bess]] = field(default_factory=list)  # type: ignore
    pv: Optional[List[Pv]] = field(default_factory=list)  # type: ignore


@dataclass(frozen=True)
class Command:
    pSp: float
    qSp: float
    equipment_type: EquipmentType
