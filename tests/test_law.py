"""
Tests unitaires pour le module metier/voltage_support/law.
"""

import pytest
from datamodel.datamodel import SystemObs, Command, EquipmentType
from datamodel.project_data import ProjectData
from metier.voltage_support.law import Law
from keys.keys import Keys


class TestLaw:
    """Tests pour la classe Law."""

    @pytest.fixture
    def law(self):
        """Crée une instance de Law."""
        return Law()

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

    def test_normal_law_with_setpoint(self, law, system_obs_with_setpoint):
        """Test normal_law avec un setpoint présent."""
        commands = law.normal_law(system_obs_with_setpoint)

        assert len(commands) == 1
        assert commands[0].pSp == 150.0
        assert commands[0].qSp == 0.0
        assert commands[0].equipment_type == EquipmentType.BESS

    def test_normal_law_without_setpoint(self, law, system_obs_without_setpoint):
        """Test normal_law sans setpoint."""
        commands = law.normal_law(system_obs_without_setpoint)

        assert len(commands) == 1
        assert commands[0].pSp == 0.0
        assert commands[0].qSp == 0.0
        assert commands[0].equipment_type == EquipmentType.BESS

    def test_error_law(self, law, system_obs_with_setpoint):
        """Test error_law."""
        commands = law.error_law(system_obs_with_setpoint)

        assert len(commands) == 1
        assert commands[0].pSp == 0.0
        assert commands[0].qSp == 0.0
        assert commands[0].equipment_type == EquipmentType.BESS

    def test_error_law_always_zero(self, law):
        """Test que error_law retourne toujours 0,0 indépendamment du SystemObs."""
        # Avec setpoint
        obs_with = SystemObs(
            project_data=[
                ProjectData(name=Keys.BESS_SETPOINT_KEY, value=200.0, timestamp=0.0)
            ]
        )
        commands_with = law.error_law(obs_with)

        # Sans setpoint
        obs_without = SystemObs()
        commands_without = law.error_law(obs_without)

        # Les deux devraient retourner 0,0
        assert commands_with[0].pSp == 0.0
        assert commands_without[0].pSp == 0.0
