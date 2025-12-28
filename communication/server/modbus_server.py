import threading
import time
import asyncio
from typing import Optional
from pymodbus.server import StartAsyncTcpServer  # type: ignore
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext,
)
from datamodel.datamodel import SystemObs
from communication.interface import Server
from datamodel.project_data import ProjectData
from keys.keys import Keys


class ModbusServer(Server):
    """
    Serveur Modbus qui expose :
    - Adresse 100 : SOC BESS (lecture)
    - Adresse 102 : P BESS (lecture)
    - Adresse 104 : Q BESS (lecture)
    - Adresse 500 : Setpoint BESS (écriture)
    """

    # Adresses des registres
    REG_SOC_BESS = 100
    REG_P_BESS = 102
    REG_Q_BESS = 104
    REG_SETPOINT_BESS = 500
    REG_WATCHDOG_BESS = 502

    def __init__(self, host: str = "localhost", port: int = 5020):
        """
        Initialise le serveur Modbus.

        Args:
            host: Adresse IP du serveur
            port: Port du serveur Modbus
        """
        self.host = host
        self.port = port
        self.current_system_obs: Optional[SystemObs] = None
        self.setpoint_value: Optional[float] = None
        self.setpoint_lock = threading.Lock()
        # Verrou pour protéger l'accès thread-safe au slave_context
        self.slave_context_lock = threading.Lock()
        self.server_thread: Optional[threading.Thread] = None
        self.server_running = False
        self.slave_context: ModbusSlaveContext = self._create_slave_context()
        # Avec single=True, on passe directement le ModbusSlaveContext (pas un dict)
        # Cela évite les problèmes de conversion dict lors de l'accès au contexte
        self.server_context: ModbusServerContext = ModbusServerContext(
            slaves=self.slave_context, single=True
        )

    def _create_slave_context(self) -> ModbusSlaveContext:
        """Crée le contexte de données Modbus."""
        return ModbusSlaveContext(
            hr=ModbusSequentialDataBlock(0, [0] * 10000),  # Holding Registers
            ir=ModbusSequentialDataBlock(0, [0] * 10000),  # Input Registers
        )

    def _update_holding_registers(self):
        """Met à jour les registres de holding avec les valeurs du SystemObs."""
        if self.current_system_obs is None:
            return

        bess_data = None
        if self.current_system_obs.bess and len(self.current_system_obs.bess) > 0:
            bess_data = self.current_system_obs.bess[0]

        # Protéger l'accès au slave_context avec un verrou
        with self.slave_context_lock:
            if bess_data:
                self.slave_context.setValues(
                    3, self.REG_SOC_BESS, [int(bess_data.soc * 100)]
                )
                self.slave_context.setValues(
                    3, self.REG_P_BESS, [int(bess_data.p * 100)]
                )
                self.slave_context.setValues(
                    3, self.REG_Q_BESS, [int(bess_data.q * 100)]
                )
            else:
                self.slave_context.setValues(3, self.REG_SOC_BESS, [0])
                self.slave_context.setValues(3, self.REG_P_BESS, [0])
                self.slave_context.setValues(3, self.REG_Q_BESS, [0])

    def expose_server(self, system_obs: SystemObs):
        """
        Démarre le serveur Modbus et expose les données du SystemObs.

        Args:
            system_obs: SystemObs contenant les données à exposer
        """
        self.current_system_obs = system_obs
        self._update_holding_registers()

        if not self.server_running:
            self.server_running = True
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()

    def _run_server(self):
        """Lance le serveur Modbus dans un thread séparé avec asyncio."""
        loop = None
        try:
            # Créer une nouvelle boucle d'événements pour ce thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Démarrer le serveur asynchrone
            # StartAsyncTcpServer est une coroutine qui tourne indéfiniment
            async def run_async_server():
                await StartAsyncTcpServer(
                    context=self.server_context,
                    address=(self.host, self.port),
                )

            # Lancer la coroutine dans la boucle
            loop.run_until_complete(run_async_server())
        except Exception as e:
            print(f"Error starting Modbus server: {e}")
            import traceback

            traceback.print_exc()
            self.server_running = False
        finally:
            if loop is not None:
                loop.close()

    def fill_system_obs(self) -> SystemObs:
        """
        Retourne un SystemObs avec le ProjectData créé à partir de la valeur
        écrite dans le registre 500 (BESS_SETPOINT_KEY).

        Returns:
            SystemObs contenant le ProjectData avec BESS_SETPOINT_KEY si une valeur a été écrite
        """
        # Protéger l'accès au slave_context avec un verrou pour éviter les race conditions
        # Le serveur Modbus peut écrire dans ce registre depuis un autre thread
        with self.slave_context_lock:
            try:
                bess_sp_values = self.slave_context.getValues(  # type: ignore
                    3, self.REG_SETPOINT_BESS, 1
                )
            except Exception:
                # En cas d'erreur, retourner une valeur par défaut
                bess_sp_values = [0]

            if bess_sp_values and len(bess_sp_values) > 0:  # type: ignore
                bess_sp: float = float(int(bess_sp_values[0]))  # type: ignore
            else:
                bess_sp: float = 0.0

        watchdog_bess_values = self.slave_context.getValues(  # type: ignore
            3, self.REG_WATCHDOG_BESS, 1
        )
        if watchdog_bess_values and len(watchdog_bess_values) > 0:  # type: ignore
            watchdog_bess: float = float(int(watchdog_bess_values[0]))  # type: ignore
        else:
            watchdog_bess: float = 0.0

        return SystemObs(
            project_data=[
                ProjectData(
                    name=Keys.BESS_SETPOINT_KEY,
                    value=bess_sp,
                    timestamp=time.time(),
                ),
                ProjectData(
                    name=Keys.WATCHDOG_BESS_KEY,
                    value=watchdog_bess,
                    timestamp=time.time(),
                ),
            ]
        )
