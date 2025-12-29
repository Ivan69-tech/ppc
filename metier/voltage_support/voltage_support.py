from datamodel.datamodel import SystemObs, Command
from metier.interface import ControlFunction
from metier.voltage_support.state_machine import StateMachine
from metier.voltage_support.policy import Policy


class VoltageSupport(ControlFunction):
    def __init__(self, state_machine: StateMachine = StateMachine()):
        self.state_machine = state_machine

    def compute(self, system_obs: SystemObs) -> list[Command]:
        self.state_machine.update(system_obs)
        return Policy(system_obs, self.state_machine).define_law()
