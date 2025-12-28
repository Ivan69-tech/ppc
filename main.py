# main.py
import logging
from typing import List

from communication.driver.bess_driver import BessDriver
from communication.driver.pv_driver import PvDriver
from communication.interface import Driver, Server
from communication.server.modbus_server import ModbusServer
from metier.voltage_support.voltage_support import VoltageSupport
from metier.interface import ControlFunction
from core.orchestrator import Orchestrator
from application.application import Application

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def main():
    """Point d'entrée principal de l'application."""
    # Initialisation des dépendances
    functions: List[ControlFunction] = [VoltageSupport()]
    orchestrator = Orchestrator(functions)

    # Créer uniquement le driver Modbus
    drivers: List[Driver] = [BessDriver(), PvDriver()]
    server: Server = ModbusServer()

    # Création et lancement de l'application
    app = Application(
        drivers=drivers,
        server=server,
        orchestrator=orchestrator,
        communication_interval=1.0,
        process_interval=1.0,
    )

    app.run()


if __name__ == "__main__":
    main()
