import logging
from dataclasses import fields
from typing import Any, List
from datamodel.datamodel import SystemObs, Command
from communication.interface import Driver, Server


logger = logging.getLogger(__name__)


class Adapter:
    """
    Adapte entre le monde externe (drivers) et le domaine applicatif.
    Responsable de la lecture des drivers, de l'agrégation des données
    et de l'envoi des commandes aux drivers appropriés.
    """

    def __init__(self, drivers: List[Driver], server: Server):
        """
        Initialise l'Adapter avec la liste des drivers.

        Args:
            drivers: Liste des drivers de communication (Modbus, etc.)
        """
        self.drivers = drivers
        self.server = server
        self.global_system_obs = SystemObs()

    def read_and_aggregate(self) -> SystemObs:
        """
        Lit les données de tous les drivers, les agrège et retourne un SystemObs global.

        Returns:
            SystemObs agrégé contenant toutes les données des drivers
        """
        # Lire les données de tous les drivers
        external_outputs: list[SystemObs] = []

        for driver in self.drivers:
            try:
                system_obs = driver.read()
                external_outputs.append(system_obs)
            except Exception as e:
                logger.error(
                    f"Erreur lors de la lecture du driver {type(driver).__name__}: {e}",
                    exc_info=True,
                )

        external_outputs.append(self.server.fill_system_obs())  # data from server

        # Agrégation des données
        aggregated_system_obs = self._aggregate(external_outputs)
        self.global_system_obs = aggregated_system_obs
        return aggregated_system_obs

    def send_commands(self, commands: List[Command]) -> None:
        """
        Envoie les commandes aux drivers appropriés selon leur type d'équipement.

        Args:
            commands: Liste des commandes à envoyer
        """
        for cmd in commands:
            for driver in self.drivers:
                try:
                    # Vérifier si le driver gère le type d'équipement de la commande
                    if driver.get_equipment_type() == cmd.equipment_type:
                        driver.write(cmd)
                        logger.debug(
                            f"Commande envoyée à {type(driver).__name__}: "
                            f"pSp={cmd.pSp}, qSp={cmd.qSp}"
                        )
                        break  # Une commande envoyée, passer à la suivante
                except Exception as e:
                    logger.error(
                        f"Erreur lors de l'écriture au driver {type(driver).__name__}: {e}",
                        exc_info=True,
                    )

    def _aggregate(self, external_outputs: list[SystemObs]) -> SystemObs:
        """
        Agrège les sorties de tous les drivers dans un SystemObs global.
        Accumule automatiquement tous les champs de type liste (sauf timestamp).
        Cette méthode est générique et s'adapte automatiquement aux évolutions de SystemObs.

        Args:
            external_outputs: Liste des SystemObs provenant des drivers et du serveur

        Returns:
            SystemObs agrégé
        """
        # Obtenir tous les champs du dataclass SystemObs
        system_obs_fields = fields(SystemObs)

        # Dictionnaire pour stocker les valeurs accumulées de chaque champ
        accumulated_values: dict[str, Any] = {}

        # Pour chaque champ de SystemObs (sauf timestamp)
        for field_info in system_obs_fields:
            field_name = field_info.name
            # Exclure le champ timestamp s'il existe
            if field_name == "timestamp":
                continue

            # Initialiser la liste accumulée pour ce champ
            accumulated_list: list[Any] = []

            # Parcourir tous les SystemObs des drivers
            for system_obs in external_outputs:
                field_value = getattr(system_obs, field_name)
                if field_value:
                    accumulated_list.extend(field_value)

            accumulated_values[field_name] = accumulated_list

        return SystemObs(**accumulated_values)

    def sync_server(self):
        self.server.expose_server(self.global_system_obs)
