from dataclasses import fields
from typing import Any
from datamodel.datamodel import SystemObs


class Adapter:
    def __init__(self, driver_outputs: list[SystemObs]):
        self.driver_outputs = driver_outputs
        self.global_system_obs = SystemObs()

    def aggregate(self):
        """
        Agrège les sorties de tous les drivers dans un SystemObs global.
        Accumule automatiquement tous les champs de type liste (sauf timestamp).
        Cette méthode est générique et s'adapte automatiquement aux évolutions de SystemObs.
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
            for system_obs in self.driver_outputs:
                field_value = getattr(system_obs, field_name)
                if field_value:
                    accumulated_list.extend(field_value)  # type: ignore[arg-type]

            accumulated_values[field_name] = accumulated_list

        self.global_system_obs = SystemObs(**accumulated_values)  # type: ignore[arg-type]

        return self.global_system_obs
