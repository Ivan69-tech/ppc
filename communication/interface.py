from abc import ABC, abstractmethod
from datamodel.datamodel import SystemObs, Command, EquipmentType


class Driver(ABC):
    @abstractmethod
    def read(self) -> SystemObs:
        pass

    @abstractmethod
    def write(self, command: Command):
        pass

    @abstractmethod
    def get_equipment_type(self) -> EquipmentType:
        pass
