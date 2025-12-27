# core/orchestrator.py
from typing import List
from metier.interface import ControlFunction
from datamodel.datamodel import Command, DataModel


class Orchestrator:
    """
    Coordonne l'exécution des fonctions métier sur les mesures
    et fusionne les commandes en une liste prête à envoyer.
    """

    def __init__(self, functions: List[ControlFunction]):
        self.functions = functions

    def step(self, datamodel: DataModel) -> Command:
        """
        Exécute toutes les fonctions métier sur le snapshot fourni
        et retourne la liste des commandes.
        """
        cmd = Command(0, 0)

        for func in self.functions:
            cmd = func.compute(datamodel)

        return cmd
