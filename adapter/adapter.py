from datamodel.datamodel import SystemObs
from datamodel.standard_data import Bess, Pv


class Adapter:
    def __init__(self, driver_outputs: list[SystemObs]):
        self.driver_outputs = driver_outputs
        self.global_system_obs = SystemObs()

    def aggregate(self):
        """
        Agrège les sorties de tous les drivers dans un SystemObs global.
        Accumule les listes de bess et pv de tous les drivers.
        """
        accumulated_bess: list[Bess] = []
        accumulated_pv: list[Pv] = []

        # Parcourir tous les SystemObs des drivers
        for system_obs in self.driver_outputs:
            # Accumuler les bess
            if system_obs.bess is not None:
                accumulated_bess.extend(system_obs.bess)

            # Accumuler les pv
            if system_obs.pv is not None:
                accumulated_pv.extend(system_obs.pv)

        # Créer le SystemObs global avec les données accumulées
        self.global_system_obs = SystemObs(
            bess=accumulated_bess if accumulated_bess else None,
            pv=accumulated_pv if accumulated_pv else None,
        )

        return self.global_system_obs
