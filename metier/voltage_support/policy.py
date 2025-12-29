from datamodel.datamodel import SystemObs, Command
from metier.voltage_support.state_machine import StateMachine
from metier.voltage_support.law import Law


class Policy:
    def __init__(self, system_obs: SystemObs, state_machine: StateMachine):
        self.state_machine = state_machine
        self.system_obs = system_obs
        self.law = Law()

    def define_law(self) -> list[Command]:
        if self.state_machine.is_auto():
            print("auto")
            return self.law.normal_law(self.system_obs)
        else:
            print("error")
            return self.law.error_law(self.system_obs)
