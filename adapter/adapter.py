from datamodel.datamodel import SystemObs
from datamodel.standard_data import Bess, Pv
from datamodel.project_data import ProjectData


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
        accumulated_project_data: list[ProjectData] = []
        # Parcourir tous les SystemObs des drivers
        for system_obs in self.driver_outputs:
            # Accumuler les bess
            if system_obs.bess:
                accumulated_bess.extend(system_obs.bess)

            # Accumuler les pv
            if system_obs.pv:
                accumulated_pv.extend(system_obs.pv)

            if system_obs.project_data:
                accumulated_project_data.extend(system_obs.project_data)

        # Créer le SystemObs global avec les données accumulées
        self.global_system_obs = SystemObs(
            bess=accumulated_bess,
            pv=accumulated_pv,
            project_data=accumulated_project_data,
        )

        return self.global_system_obs
