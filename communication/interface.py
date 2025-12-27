from abc import ABC, abstractmethod
from datamodel.datamodel import SystemObs, Command, EquipmentType


class Driver(ABC):
    @abstractmethod
    def read(self) -> SystemObs:
        pass

    @abstractmethod
    def write(self, command: Command):
        pass

    def get_equipment_type(self) -> EquipmentType:
        """
        Retourne le type d'équipement géré par ce driver.
        Par défaut, détermine le type en fonction des données retournées par read().
        Peut être surchargé par les sous-classes pour une meilleure performance.
        """
        system_obs = self.read()
        if system_obs.bess is not None and len(system_obs.bess) > 0:
            return EquipmentType.BESS
        elif system_obs.pv is not None and len(system_obs.pv) > 0:
            return EquipmentType.PV
        else:
            # Par défaut, retourne BESS si aucune donnée
            return EquipmentType.BESS
