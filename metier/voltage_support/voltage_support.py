from datamodel.datamodel import SystemObs, Command, EquipmentType
from metier.interface import ControlFunction


class VoltageSupport(ControlFunction):
    def compute(self, system_obs: SystemObs) -> list[Command]:
        if system_obs.pv:
            pv0 = system_obs.pv[0]
            p = pv0.p * 10
            q = pv0.q * 100
            equipment_type = EquipmentType.PV
        else:
            p = 0.0
            q = 0.0
            equipment_type = EquipmentType.PV  # Par défaut, même si pas de données
        return [
            Command(pSp=p, qSp=q, equipment_type=equipment_type),
            Command(pSp=20, qSp=50, equipment_type=EquipmentType.BESS),
        ]
