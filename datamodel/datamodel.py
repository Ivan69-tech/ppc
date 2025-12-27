from dataclasses import dataclass, field
from enum import Enum
from .standard_data import Bess, Pv
from .project_data import ProjectData


class EquipmentType(Enum):
    """Type d'équipement cible pour une commande."""

    BESS = "bess"
    PV = "pv"


@dataclass(frozen=True)
class SystemObs:
    bess: list[Bess] = field(default_factory=list)  # type: ignore
    pv: list[Pv] = field(default_factory=list)  # type: ignore
    project_data: list[ProjectData] = field(default_factory=list)  # type: ignore


@dataclass(frozen=True)
class Command:
    pSp: float
    qSp: float
    equipment_type: EquipmentType
