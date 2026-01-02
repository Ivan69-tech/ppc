"""
Tests unitaires pour les drivers de communication.
"""

import pytest
from datamodel.datamodel import SystemObs, Command, EquipmentType
from communication.driver.bess_driver import BessDriver
from communication.driver.pv_driver import PvDriver
from keys.keys import Keys


class TestBessDriver:
    """Tests pour la classe BessDriver."""

    @pytest.fixture
    def bess_driver(self):
        """Crée une instance de BessDriver."""
        return BessDriver()

    def test_bess_driver_read(self, bess_driver):
        """Test read du BessDriver."""
        system_obs = bess_driver.read()

        assert isinstance(system_obs, SystemObs)
        assert len(system_obs.bess) == 1
        assert len(system_obs.project_data) == 1
        assert system_obs.bess[0].p >= 0  # current_second
        assert system_obs.bess[0].q == 20.0
        assert system_obs.bess[0].soc == 50.0
        assert system_obs.project_data[0].name == Keys.TEMPERATURE_BESS_KEY
        assert system_obs.project_data[0].value == 20.0

    def test_bess_driver_write(self, bess_driver, capsys):
        """Test write du BessDriver."""
        command = Command(pSp=100.0, qSp=50.0, equipment_type=EquipmentType.BESS)
        bess_driver.write(command)

        # Vérifier que le message a été imprimé
        captured = capsys.readouterr()
        assert "Writing command" in captured.out

    def test_bess_driver_get_equipment_type(self, bess_driver):
        """Test get_equipment_type du BessDriver."""
        assert bess_driver.get_equipment_type() == EquipmentType.BESS


class TestPvDriver:
    """Tests pour la classe PvDriver."""

    @pytest.fixture
    def pv_driver(self):
        """Crée une instance de PvDriver."""
        return PvDriver()

    def test_pv_driver_initialization(self, pv_driver):
        """Test l'initialisation du PvDriver."""
        assert pv_driver.n == 0

    def test_pv_driver_read(self, pv_driver):
        """Test read du PvDriver."""
        system_obs = pv_driver.read()

        assert isinstance(system_obs, SystemObs)
        assert len(system_obs.pv) == 1
        assert len(system_obs.project_data) == 1
        assert system_obs.pv[0].p == 1  # n commence à 0, puis incrémente
        assert system_obs.pv[0].q == 10  # n * 10
        assert system_obs.project_data[0].name == Keys.IRRADIANCE_KEY
        assert system_obs.project_data[0].value == 1000.0

    def test_pv_driver_read_increments(self, pv_driver):
        """Test que read incrémente n."""
        obs1 = pv_driver.read()
        obs2 = pv_driver.read()

        assert obs1.pv[0].p == 1
        assert obs2.pv[0].p == 2
        assert obs1.pv[0].q == 10
        assert obs2.pv[0].q == 20

    def test_pv_driver_write(self, pv_driver):
        """Test write du PvDriver."""
        command = Command(pSp=200.0, qSp=0.0, equipment_type=EquipmentType.PV)
        # Ne devrait pas lever d'exception
        pv_driver.write(command)

    def test_pv_driver_get_equipment_type(self, pv_driver):
        """Test get_equipment_type du PvDriver."""
        assert pv_driver.get_equipment_type() == EquipmentType.PV
