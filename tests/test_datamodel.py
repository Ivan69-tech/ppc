"""
Tests unitaires pour le module datamodel.
"""

import pytest
import time
from datamodel.datamodel import SystemObs, Command, EquipmentType
from datamodel.standard_data import Bess, Pv
from datamodel.project_data import ProjectData
from keys.keys import Keys


class TestEquipmentType:
    """Tests pour l'enum EquipmentType."""

    def test_equipment_type_values(self):
        """Vérifie que les valeurs de l'enum sont correctes."""
        assert EquipmentType.BESS.value == "bess"
        assert EquipmentType.PV.value == "pv"

    def test_equipment_type_enum(self):
        """Vérifie que l'enum fonctionne correctement."""
        assert EquipmentType.BESS != EquipmentType.PV
        assert EquipmentType.BESS == EquipmentType.BESS


class TestSystemObs:
    """Tests pour la classe SystemObs."""

    def test_system_obs_creation_empty(self):
        """Test la création d'un SystemObs vide."""
        obs = SystemObs()
        assert obs.bess == []
        assert obs.pv == []
        assert obs.project_data == []

    def test_system_obs_creation_with_data(
        self, sample_bess, sample_pv, sample_project_data
    ):
        """Test la création d'un SystemObs avec des données."""
        obs = SystemObs(
            bess=[sample_bess], pv=[sample_pv], project_data=[sample_project_data]
        )
        assert len(obs.bess) == 1
        assert len(obs.pv) == 1
        assert len(obs.project_data) == 1
        assert obs.bess[0] == sample_bess
        assert obs.pv[0] == sample_pv
        assert obs.project_data[0] == sample_project_data

    def test_system_obs_immutable(self, sample_bess):
        """Test que SystemObs est immutable (frozen dataclass)."""
        obs = SystemObs(bess=[sample_bess])
        with pytest.raises(Exception):  # TypeError pour frozen dataclass
            obs.bess = []  # type: ignore

    def test_get_project_data_existing(self, sample_system_obs):
        """Test get_project_data avec une clé existante."""
        result = sample_system_obs.get_project_data(Keys.BESS_SETPOINT_KEY)
        assert result is not None
        assert result.name == Keys.BESS_SETPOINT_KEY
        assert result.value == 150.0

    def test_get_project_data_nonexistent(self, sample_system_obs):
        """Test get_project_data avec une clé inexistante."""
        result = sample_system_obs.get_project_data("nonexistent_key")
        assert result is None

    def test_get_project_data_empty_obs(self):
        """Test get_project_data sur un SystemObs vide."""
        obs = SystemObs()
        result = obs.get_project_data(Keys.BESS_SETPOINT_KEY)
        assert result is None


class TestCommand:
    """Tests pour la classe Command."""

    def test_command_creation(self):
        """Test la création d'une Command."""
        cmd = Command(pSp=100.0, qSp=50.0, equipment_type=EquipmentType.BESS)
        assert cmd.pSp == 100.0
        assert cmd.qSp == 50.0
        assert cmd.equipment_type == EquipmentType.BESS

    def test_command_immutable(self):
        """Test que Command est immutable (frozen dataclass)."""
        cmd = Command(pSp=100.0, qSp=50.0, equipment_type=EquipmentType.BESS)
        with pytest.raises(Exception):  # TypeError pour frozen dataclass
            cmd.pSp = 200.0  # type: ignore

    def test_command_different_equipment_types(self):
        """Test la création de commandes pour différents types d'équipements."""
        cmd_bess = Command(pSp=100.0, qSp=50.0, equipment_type=EquipmentType.BESS)
        cmd_pv = Command(pSp=200.0, qSp=0.0, equipment_type=EquipmentType.PV)
        assert cmd_bess.equipment_type == EquipmentType.BESS
        assert cmd_pv.equipment_type == EquipmentType.PV
