# core/orchestrator.py
from typing import List
from metier.interface import ControlFunction
from datamodel.datamodel import Command, SystemObs, EquipmentType


class Orchestrator:
    """
    Coordonne l'exécution des fonctions métier sur les mesures
    et fusionne les commandes en une liste prête à envoyer.
    """

    def __init__(self, functions: List[ControlFunction]):
        self.functions = functions

    def step(self, system_obs: SystemObs) -> Command:
        """
        Exécute toutes les fonctions métier sur le snapshot fourni
        et retourne la liste des commandes.
        """
        # Commande par défaut (sera remplacée par la première fonction métier)
        cmd = Command(pSp=0.0, qSp=0.0, equipment_type=EquipmentType.BESS)

        for func in self.functions:
            cmd = func.compute(system_obs)

        return cmd
