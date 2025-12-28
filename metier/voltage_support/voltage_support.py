from datamodel.datamodel import SystemObs, Command, EquipmentType
from metier.interface import ControlFunction
from keys.keys import Keys


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

        # Initialiser pSp et qSp avec des valeurs par défaut
        p_bess_sp = 0.0

        # Récupérer le project_data avec la clé BESS_SETPOINT_KEY s'il existe
        if system_obs.project_data:
            for project_data in system_obs.project_data:
                if project_data.name == Keys.BESS_SETPOINT_KEY:
                    p_bess_sp = project_data.value
                    print(f"p_bess_sp: {p_bess_sp}")
                    break

        return [
            Command(pSp=p, qSp=q, equipment_type=equipment_type),
            Command(pSp=p_bess_sp, qSp=0, equipment_type=EquipmentType.BESS),
        ]
