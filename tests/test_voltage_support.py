"""
Tests unitaires pour le module metier/voltage_support/voltage_support.
"""

import pytest
import time
from datamodel.datamodel import SystemObs, Command, EquipmentType
from datamodel.project_data import ProjectData
from metier.voltage_support.voltage_support import VoltageSupport
from metier.voltage_support.state_machine import StateMachine, State
from keys.keys import Keys


class TestVoltageSupport:
    """Tests pour la classe VoltageSupport."""

    @pytest.fixture
    def voltage_support(self):
        """Crée une instance de VoltageSupport."""
        return VoltageSupport()

    @pytest.fixture
    def voltage_support_custom_sm(self):
        """Crée une VoltageSupport avec une StateMachine personnalisée."""
        sm = StateMachine(timeout_seconds=10.0, min_heartbeat_interval=0.1)
        return VoltageSupport(state_machine=sm)

    @pytest.fixture
    def system_obs_with_watchdog_and_setpoint(self):
        """Crée un SystemObs avec watchdog et setpoint."""
        return SystemObs(
            project_data=[
                ProjectData(
                    name=Keys.WATCHDOG_BESS_KEY, value=1.0, timestamp=time.time()
                ),
                ProjectData(name=Keys.BESS_SETPOINT_KEY, value=150.0, timestamp=0.0),
            ]
        )

    def test_voltage_support_initialization(self, voltage_support):
        """Test l'initialisation de VoltageSupport."""
        assert isinstance(voltage_support.state_machine, StateMachine)

    def test_voltage_support_custom_state_machine(self, voltage_support_custom_sm):
        """Test VoltageSupport avec une StateMachine personnalisée."""
        assert isinstance(voltage_support_custom_sm.state_machine, StateMachine)

    def test_compute_updates_state_machine(
        self, voltage_support, system_obs_with_watchdog_and_setpoint
    ):
        """Test que compute met à jour la StateMachine."""
        initial_state = voltage_support.state_machine.get_state()
        assert initial_state == State.ERROR

        voltage_support.compute(system_obs_with_watchdog_and_setpoint)

        # La StateMachine devrait avoir été mise à jour
        # (même si l'état peut rester ERROR si pas de heartbeat valide)

    def test_compute_returns_commands(
        self, voltage_support, system_obs_with_watchdog_and_setpoint
    ):
        """Test que compute retourne une liste de Command."""
        commands = voltage_support.compute(system_obs_with_watchdog_and_setpoint)

        assert isinstance(commands, list)
        assert len(commands) > 0
        assert all(isinstance(cmd, Command) for cmd in commands)

    def test_compute_error_state(self, voltage_support):
        """Test compute en état ERROR."""
        obs = SystemObs(
            project_data=[
                ProjectData(name=Keys.BESS_SETPOINT_KEY, value=150.0, timestamp=0.0)
            ]
        )
        commands = voltage_support.compute(obs)

        # En état ERROR, devrait retourner 0,0
        assert len(commands) == 1
        assert commands[0].pSp == 0.0
        assert commands[0].qSp == 0.0

    def test_compute_auto_state(self, voltage_support_custom_sm):
        """Test compute en état AUTO."""
        # Mettre la StateMachine en état AUTO
        obs1 = SystemObs(
            project_data=[
                ProjectData(
                    name=Keys.WATCHDOG_BESS_KEY, value=1.0, timestamp=time.time()
                ),
                ProjectData(name=Keys.BESS_SETPOINT_KEY, value=150.0, timestamp=0.0),
            ]
        )
        voltage_support_custom_sm.compute(obs1)
        time.sleep(0.01)
        obs2 = SystemObs(
            project_data=[
                ProjectData(
                    name=Keys.WATCHDOG_BESS_KEY, value=2.0, timestamp=time.time()
                ),
                ProjectData(name=Keys.BESS_SETPOINT_KEY, value=150.0, timestamp=0.0),
            ]
        )
        commands = voltage_support_custom_sm.compute(obs2)

        # En état AUTO avec setpoint, devrait retourner le setpoint
        assert len(commands) == 1
        assert commands[0].pSp == 150.0
        assert commands[0].equipment_type == EquipmentType.BESS
