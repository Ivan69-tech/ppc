# main.py
from typing import List

from communication.driver.modbus import Modbus
from metier.voltage_support.voltage_support import VoltageSupport
from metier.interface import ControlFunction
from core.orchestrator import Orchestrator
from application.application import Application


def main():
    """Point d'entrée principal de l'application."""
    # Initialisation des dépendances
    functions: List[ControlFunction] = [VoltageSupport()]
    orchestrator = Orchestrator(functions)
    driver = Modbus()

    # Création et lancement de l'application
    app = Application(
        driver=driver,
        orchestrator=orchestrator,
        communication_interval=1.0,
        process_interval=5.0,
    )

    app.run()


if __name__ == "__main__":
    main()
