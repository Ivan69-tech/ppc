from abc import ABC, abstractmethod
from datamodel.datamodel import DataModel, Command


class ControlFunction(ABC):
    @abstractmethod
    def compute(self, datamodel: DataModel) -> Command:
        pass
