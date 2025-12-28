import datamodel.standard_data as std_data
import time
from communication.interface import Driver
from datamodel.datamodel import SystemObs, Command, EquipmentType
from keys.keys import Keys
from datamodel.project_data import ProjectData


class PvDriver(Driver):
    def __init__(self):
        self.n = 0

    def read(self) -> SystemObs:
        self.n += 1
        pv = std_data.Pv(p=self.n, q=self.n * 10, timestamp=time.time())
        return SystemObs(
            pv=[pv],
            project_data=[
                ProjectData(
                    name=Keys.IRRADIANCE_KEY, value=1000.0, timestamp=time.time()
                )
            ],
        )

    def write(self, command: Command):
        pass

    def get_equipment_type(self) -> EquipmentType:
        return EquipmentType.PV
