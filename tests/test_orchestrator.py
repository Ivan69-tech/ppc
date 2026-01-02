"""
Tests unitaires pour le module core/orchestrator.
"""

import pytest
from unittest.mock import Mock
from datamodel.datamodel import SystemObs, Command, EquipmentType
from core.orchestrator import Orchestrator


class TestOrchestrator:
    """Tests pour la classe Orchestrator."""

    @pytest.fixture
    def mock_control_function1(self):
        """Crée une fonction de contrôle mock."""
        func = Mock()
        func.compute.return_value = [
            Command(pSp=100.0, qSp=50.0, equipment_type=EquipmentType.BESS)
        ]
        return func

    @pytest.fixture
    def mock_control_function2(self):
        """Crée une deuxième fonction de contrôle mock."""
        func = Mock()
        func.compute.return_value = [
            Command(pSp=200.0, qSp=0.0, equipment_type=EquipmentType.PV)
        ]
        return func

    @pytest.fixture
    def orchestrator(self, mock_control_function1, mock_control_function2):
        """Crée un Orchestrator avec des fonctions mock."""
        return Orchestrator(functions=[mock_control_function1, mock_control_function2])

    def test_orchestrator_initialization(
        self, orchestrator, mock_control_function1, mock_control_function2
    ):
        """Test l'initialisation de l'Orchestrator."""
        assert len(orchestrator.functions) == 2
        assert orchestrator.functions[0] == mock_control_function1
        assert orchestrator.functions[1] == mock_control_function2

    def test_step_single_function(self, mock_control_function1):
        """Test step avec une seule fonction."""
        orchestrator = Orchestrator(functions=[mock_control_function1])
        system_obs = SystemObs()

        commands = orchestrator.step(system_obs)

        mock_control_function1.compute.assert_called_once_with(system_obs)
        assert len(commands) == 1
        assert commands[0].pSp == 100.0

    def test_step_multiple_functions(
        self, orchestrator, mock_control_function1, mock_control_function2
    ):
        """Test step avec plusieurs fonctions."""
        system_obs = SystemObs()

        commands = orchestrator.step(system_obs)

        mock_control_function1.compute.assert_called_once_with(system_obs)
        mock_control_function2.compute.assert_called_once_with(system_obs)
        assert len(commands) == 2
        assert commands[0].equipment_type == EquipmentType.BESS
        assert commands[1].equipment_type == EquipmentType.PV

    def test_step_function_returns_multiple_commands(self):
        """Test step quand une fonction retourne plusieurs commandes."""
        func = Mock()
        func.compute.return_value = [
            Command(pSp=100.0, qSp=50.0, equipment_type=EquipmentType.BESS),
            Command(pSp=150.0, qSp=75.0, equipment_type=EquipmentType.BESS),
        ]

        orchestrator = Orchestrator(functions=[func])
        system_obs = SystemObs()

        commands = orchestrator.step(system_obs)

        assert len(commands) == 2

    def test_step_empty_functions_list(self):
        """Test step avec une liste vide de fonctions."""
        orchestrator = Orchestrator(functions=[])
        system_obs = SystemObs()

        commands = orchestrator.step(system_obs)

        assert len(commands) == 0

    def test_step_function_returns_empty_list(self):
        """Test step quand une fonction retourne une liste vide."""
        func = Mock()
        func.compute.return_value = []

        orchestrator = Orchestrator(functions=[func])
        system_obs = SystemObs()

        commands = orchestrator.step(system_obs)

        assert len(commands) == 0
