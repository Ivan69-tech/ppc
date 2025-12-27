from abc import ABC, abstractmethod
from context.context import Context


class Driver(ABC):
    @abstractmethod
    def read(self, context: Context):
        pass

    @abstractmethod
    def write(self, context: Context):
        pass
