from datamodel.datamodel import DataModel, Command
from metier.interface import ControlFunction


class VoltageSupport(ControlFunction):
    def compute(self, datamodel: DataModel) -> Command:
        p = datamodel.bess.p * 10
        q = datamodel.bess.q * 100
        return Command(p, q)
