# main.py
from typing import List

from communication.driver.bess_driver import BessDriver
from communication.driver.pv_driver import PvDriver
from communication.interface import Driver
from metier.voltage_support.voltage_support import VoltageSupport
from metier.interface import ControlFunction
from core.orchestrator import Orchestrator
from application.application import Application


def main():
    """Point d'entrée principal de l'application."""
    # Initialisation des dépendances
    functions: List[ControlFunction] = [VoltageSupport()]
    orchestrator = Orchestrator(functions)

    # Créer uniquement le driver Modbus
    drivers: List[Driver] = [BessDriver(), PvDriver()]

    # Création et lancement de l'application
    app = Application(
        drivers=drivers,
        orchestrator=orchestrator,
        communication_interval=1.0,
        process_interval=1.0,
    )

    app.run()


if __name__ == "__main__":
    main()
