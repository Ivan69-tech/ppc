import datamodel.standard_data as std_data
import time
from communication.interface import Driver
from datamodel.datamodel import SystemObs, Command, EquipmentType


class BessDriver(Driver):
    def read(self) -> SystemObs:
        current_second = time.localtime().tm_sec
        bess = std_data.Bess(p=current_second, q=20, soc=50, timestamp=time.time())
        return SystemObs(bess=[bess])

    def write(self, command: Command):
        print(f"Écriture commande BESS: pSp={command.pSp}, qSp={command.qSp}")

    def get_equipment_type(self) -> EquipmentType:
        return EquipmentType.BESS
