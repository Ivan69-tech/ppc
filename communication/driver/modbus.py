from context.context import Context
import datamodel.standard_data as std_data
from keys.keys import Keys
import time
from communication.interface import Driver


class Modbus(Driver):
    def read(self, context: Context):
        current_second = time.localtime().tm_sec
        print(f"seconde actuelle {current_second}")
        bess = std_data.Bess(p=current_second, q=0, soc=50, timestamp=time.time())
        context.set(Keys.BESSKEY, bess)
        return

    def write(self, context: Context):
        pass
