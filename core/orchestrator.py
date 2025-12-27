# core/orchestrator.py
from typing import List
from metier.interface import ControlFunction
from datamodel.datamodel import Command, SystemObs


class Orchestrator:
    """
    Coordonne l'exécution des fonctions métier sur les mesures
    et retourne une liste de commandes, une par fonction métier.
    """

    def __init__(self, functions: List[ControlFunction]):
        self.functions = functions

    def step(self, system_obs: SystemObs) -> List[Command]:
        """
        Exécute toutes les fonctions métier sur le snapshot fourni
        et retourne la liste des commandes générées.

        Returns:
            Liste des commandes, une par fonction métier exécutée.
        """
        commands: List[Command] = []

        for func in self.functions:
            cmd = func.compute(system_obs)
            commands.extend(cmd)

        return commands
