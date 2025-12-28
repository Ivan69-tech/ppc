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


class Server(ABC):
    @abstractmethod
    def expose_server(
        self, system_obs: SystemObs
    ):  # synchronise le serve avec le SystemObs actuel
        pass

    @abstractmethod
    def fill_system_obs(
        self,
    ) -> SystemObs:  # remplit le SystemObs avec les données du serveur
        pass
