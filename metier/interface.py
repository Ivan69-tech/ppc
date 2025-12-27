from abc import ABC, abstractmethod
from datamodel.datamodel import SystemObs, Command


class ControlFunction(ABC):
    @abstractmethod
    def compute(self, system_obs: SystemObs) -> list[Command]:
        pass
