"""
Tests unitaires pour le module metier/voltage_support/policy.
"""

import pytest
import time
from datamodel.datamodel import SystemObs, Command, EquipmentType
from datamodel.project_data import ProjectData
from metier.voltage_support.policy import Policy
from metier.voltage_support.state_machine import StateMachine, State
from keys.keys import Keys


class TestPolicy:
    """Tests pour la classe Policy."""

    @pytest.fixture
    def state_machine_auto(self):
        """Crée une StateMachine en état AUTO."""
        sm = StateMachine(timeout_seconds=10.0, min_heartbeat_interval=0.1)
        # Mettre en état AUTO
        obs1 = SystemObs(
            project_data=[
                ProjectData(
                    name=Keys.WATCHDOG_BESS_KEY, value=1.0, timestamp=time.time()
                )
            ]
        )
        sm.update(obs1)
        time.sleep(0.01)
        obs2 = SystemObs(
            project_data=[
                ProjectData(
                    name=Keys.WATCHDOG_BESS_KEY, value=2.0, timestamp=time.time()
                )
            ]
        )
        sm.update(obs2)
        return sm

    @pytest.fixture
    def state_machine_error(self):
        """Crée une StateMachine en état ERROR."""
        return StateMachine(timeout_seconds=1.0, min_heartbeat_interval=0.1)

    @pytest.fixture
    def system_obs_with_setpoint(self):
        """Crée un SystemObs avec un setpoint BESS."""
        return SystemObs(
            project_data=[
                ProjectData(name=Keys.BESS_SETPOINT_KEY, value=150.0, timestamp=0.0)
            ]
        )

    @pytest.fixture
    def system_obs_without_setpoint(self):
        """Crée un SystemObs sans setpoint BESS."""
        return SystemObs()

    def test_define_law_auto_with_setpoint(
        self, state_machine_auto, system_obs_with_setpoint
    ):
        """Test define_law en état AUTO avec setpoint."""
        policy = Policy(system_obs_with_setpoint, state_machine_auto)
        commands = policy.define_law()

        assert len(commands) == 1
        assert commands[0].pSp == 150.0
        assert commands[0].qSp == 0.0
        assert commands[0].equipment_type == EquipmentType.BESS

    def test_define_law_auto_without_setpoint(
        self, state_machine_auto, system_obs_without_setpoint
    ):
        """Test define_law en état AUTO sans setpoint."""
        policy = Policy(system_obs_without_setpoint, state_machine_auto)
        commands = policy.define_law()

        assert len(commands) == 1
        assert commands[0].pSp == 0.0
        assert commands[0].qSp == 0.0
        assert commands[0].equipment_type == EquipmentType.BESS

    def test_define_law_error(self, state_machine_error, system_obs_with_setpoint):
        """Test define_law en état ERROR."""
        policy = Policy(system_obs_with_setpoint, state_machine_error)
        commands = policy.define_law()

        assert len(commands) == 1
        assert commands[0].pSp == 0.0
        assert commands[0].qSp == 0.0
        assert commands[0].equipment_type == EquipmentType.BESS

    def test_define_law_error_ignores_setpoint(self, state_machine_error):
        """Test que define_law en état ERROR ignore le setpoint."""
        obs_with_setpoint = SystemObs(
            project_data=[
                ProjectData(name=Keys.BESS_SETPOINT_KEY, value=200.0, timestamp=0.0)
            ]
        )
        policy = Policy(obs_with_setpoint, state_machine_error)
        commands = policy.define_law()

        # Même avec un setpoint, devrait retourner 0,0
        assert commands[0].pSp == 0.0
