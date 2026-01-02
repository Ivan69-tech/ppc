"""
Tests unitaires pour le module metier/voltage_support/state_machine.
"""

import pytest
import time
from datamodel.datamodel import SystemObs
from datamodel.project_data import ProjectData
from metier.voltage_support.state_machine import StateMachine, State
from metier.utils.watchog import WatchdogState
from keys.keys import Keys


class TestStateMachine:
    """Tests pour la classe StateMachine."""

    @pytest.fixture
    def state_machine(self):
        """Crée une StateMachine avec timeout court pour les tests."""
        return StateMachine(timeout_seconds=1.0, min_heartbeat_interval=0.1)

    @pytest.fixture
    def system_obs_with_watchdog(self):
        """Crée un SystemObs avec un watchdog."""
        return SystemObs(
            project_data=[
                ProjectData(
                    name=Keys.WATCHDOG_BESS_KEY, value=1.0, timestamp=time.time()
                )
            ]
        )

    @pytest.fixture
    def system_obs_without_watchdog(self):
        """Crée un SystemObs sans watchdog."""
        return SystemObs()

    def test_state_machine_initialization(self, state_machine):
        """Test l'initialisation de la StateMachine."""
        # L'état initial est "error" car le watchdog n'a pas encore reçu de heartbeat
        assert state_machine.get_state() == State.ERROR

    def test_update_with_watchdog_connected(
        self, state_machine, system_obs_with_watchdog
    ):
        """Test update avec watchdog connecté."""
        # Premier update : pas de heartbeat valide, reste en ERROR
        state_machine.update(system_obs_with_watchdog)
        assert state_machine.get_state() == State.ERROR

        # Deuxième update avec valeur différente : heartbeat valide, passe en AUTO
        time.sleep(0.01)
        new_obs = SystemObs(
            project_data=[
                ProjectData(
                    name=Keys.WATCHDOG_BESS_KEY, value=2.0, timestamp=time.time()
                )
            ]
        )
        state_machine.update(new_obs)
        assert state_machine.get_state() == State.AUTO

    def test_update_with_watchdog_disconnected(self, state_machine):
        """Test update avec watchdog déconnecté."""
        # Mettre d'abord en état AUTO
        obs1 = SystemObs(
            project_data=[
                ProjectData(
                    name=Keys.WATCHDOG_BESS_KEY, value=1.0, timestamp=time.time()
                )
            ]
        )
        state_machine.update(obs1)
        time.sleep(0.01)
        obs2 = SystemObs(
            project_data=[
                ProjectData(
                    name=Keys.WATCHDOG_BESS_KEY, value=2.0, timestamp=time.time()
                )
            ]
        )
        state_machine.update(obs2)
        assert state_machine.get_state() == State.AUTO

        # Attendre le timeout
        time.sleep(1.1)
        obs3 = SystemObs(
            project_data=[
                ProjectData(
                    name=Keys.WATCHDOG_BESS_KEY, value=2.0, timestamp=time.time()
                )
            ]
        )
        state_machine.update(obs3)
        assert state_machine.get_state() == State.ERROR

    def test_update_without_watchdog(self, state_machine, system_obs_without_watchdog):
        """Test update sans watchdog dans le SystemObs."""
        state_machine.update(system_obs_without_watchdog)
        # Devrait rester en ERROR car pas de watchdog
        assert state_machine.get_state() == State.ERROR

    def test_is_error(self, state_machine):
        """Test is_error."""
        assert state_machine.is_error() is True
        assert state_machine.is_auto() is False

    def test_is_auto(self, state_machine, system_obs_with_watchdog):
        """Test is_auto."""
        # Mettre en état AUTO
        state_machine.update(system_obs_with_watchdog)
        time.sleep(0.01)
        new_obs = SystemObs(
            project_data=[
                ProjectData(
                    name=Keys.WATCHDOG_BESS_KEY, value=2.0, timestamp=time.time()
                )
            ]
        )
        state_machine.update(new_obs)

        assert state_machine.is_auto() is True
        assert state_machine.is_error() is False

    def test_transition_error_to_auto(self, state_machine):
        """Test la transition ERROR -> AUTO."""
        assert state_machine.get_state() == State.ERROR

        # Mettre le watchdog en ligne
        obs1 = SystemObs(
            project_data=[
                ProjectData(
                    name=Keys.WATCHDOG_BESS_KEY, value=1.0, timestamp=time.time()
                )
            ]
        )
        state_machine.update(obs1)
        time.sleep(0.01)
        obs2 = SystemObs(
            project_data=[
                ProjectData(
                    name=Keys.WATCHDOG_BESS_KEY, value=2.0, timestamp=time.time()
                )
            ]
        )
        state_machine.update(obs2)

        assert state_machine.get_state() == State.AUTO

    def test_transition_auto_to_error(self, state_machine):
        """Test la transition AUTO -> ERROR."""
        # Mettre d'abord en AUTO
        obs1 = SystemObs(
            project_data=[
                ProjectData(
                    name=Keys.WATCHDOG_BESS_KEY, value=1.0, timestamp=time.time()
                )
            ]
        )
        state_machine.update(obs1)
        time.sleep(0.01)
        obs2 = SystemObs(
            project_data=[
                ProjectData(
                    name=Keys.WATCHDOG_BESS_KEY, value=2.0, timestamp=time.time()
                )
            ]
        )
        state_machine.update(obs2)
        assert state_machine.get_state() == State.AUTO

        # Attendre le timeout pour déconnecter
        time.sleep(1.1)
        obs3 = SystemObs(
            project_data=[
                ProjectData(
                    name=Keys.WATCHDOG_BESS_KEY, value=2.0, timestamp=time.time()
                )
            ]
        )
        state_machine.update(obs3)
        assert state_machine.get_state() == State.ERROR

    def test_is_watchdog_disconnected(self, state_machine):
        """Test is_watchdog_disconnected."""
        assert state_machine.is_watchdog_disconnected() is True

        # Mettre le watchdog en ligne
        obs1 = SystemObs(
            project_data=[
                ProjectData(
                    name=Keys.WATCHDOG_BESS_KEY, value=1.0, timestamp=time.time()
                )
            ]
        )
        state_machine.update(obs1)
        time.sleep(0.01)
        obs2 = SystemObs(
            project_data=[
                ProjectData(
                    name=Keys.WATCHDOG_BESS_KEY, value=2.0, timestamp=time.time()
                )
            ]
        )
        state_machine.update(obs2)
        assert state_machine.is_watchdog_disconnected() is False

    def test_is_watchdog_connected(self, state_machine):
        """Test is_watchdog_connected."""
        assert state_machine.is_watchdog_connected() is False

        # Mettre le watchdog en ligne
        obs1 = SystemObs(
            project_data=[
                ProjectData(
                    name=Keys.WATCHDOG_BESS_KEY, value=1.0, timestamp=time.time()
                )
            ]
        )
        state_machine.update(obs1)
        time.sleep(0.01)
        obs2 = SystemObs(
            project_data=[
                ProjectData(
                    name=Keys.WATCHDOG_BESS_KEY, value=2.0, timestamp=time.time()
                )
            ]
        )
        state_machine.update(obs2)
        assert state_machine.is_watchdog_connected() is True
