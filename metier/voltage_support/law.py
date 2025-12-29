from datamodel.datamodel import SystemObs, Command, EquipmentType
from keys.keys import Keys


class Law:
    def normal_law(self, system_obs: SystemObs) -> list[Command]:
        bess_sp = system_obs.get_project_data(Keys.BESS_SETPOINT_KEY)
        print("bess_sp", bess_sp)
        if bess_sp is None:
            return [Command(pSp=0, qSp=0, equipment_type=EquipmentType.BESS)]
        else:
            return [
                Command(pSp=bess_sp.value, qSp=0, equipment_type=EquipmentType.BESS)
            ]

    def error_law(self, system_obs: SystemObs) -> list[Command]:
        return [Command(pSp=0, qSp=0, equipment_type=EquipmentType.BESS)]
