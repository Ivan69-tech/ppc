from datamodel.datamodel import SystemObs, Command, EquipmentType
from metier.interface import ControlFunction
from keys.keys import Keys
from metier.voltage_support.state_machine import StateMachine


class VoltageSupport(ControlFunction):
    def __init__(self, state_machine: StateMachine = StateMachine()):
        self.state_machine = state_machine

    def compute(self, system_obs: SystemObs) -> list[Command]:
        self.state_machine.update(system_obs)
        bess_sp = system_obs.get_project_data(Keys.BESS_SETPOINT_KEY)
        if bess_sp is None:
            return [Command(pSp=0, qSp=0, equipment_type=EquipmentType.BESS)]

        if self.state_machine.get_state() == "auto":
            return [
                Command(pSp=bess_sp.value, qSp=0, equipment_type=EquipmentType.BESS),
            ]
        else:
            return [Command(pSp=0, qSp=0, equipment_type=EquipmentType.BESS)]
