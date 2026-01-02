"""
Tests unitaires pour le module adapter.
"""

import pytest
from unittest.mock import Mock
from datamodel.datamodel import SystemObs, Command, EquipmentType
from datamodel.standard_data import Bess, Pv
from datamodel.project_data import ProjectData
from adapter.adapter import Adapter
from keys.keys import Keys


class TestAdapter:
    """Tests pour la classe Adapter."""

    @pytest.fixture
    def mock_driver_bess(self):
        """Crée un mock driver BESS."""
        driver = Mock()
        driver.get_equipment_type.return_value = EquipmentType.BESS
        driver.read.return_value = SystemObs(
            bess=[Bess(p=100.0, q=50.0, soc=75.0, timestamp=0.0)],
            project_data=[
                ProjectData(name=Keys.TEMPERATURE_BESS_KEY, value=20.0, timestamp=0.0)
            ],
        )
        return driver

    @pytest.fixture
    def mock_driver_pv(self):
        """Crée un mock driver PV."""
        driver = Mock()
        driver.get_equipment_type.return_value = EquipmentType.PV
        driver.read.return_value = SystemObs(
            pv=[Pv(p=200.0, q=0.0, timestamp=0.0)],
            project_data=[
                ProjectData(name=Keys.IRRADIANCE_KEY, value=1000.0, timestamp=0.0)
            ],
        )
        return driver

    @pytest.fixture
    def mock_server(self):
        """Crée un mock serveur."""
        server = Mock()
        server.fill_system_obs.return_value = SystemObs(
            project_data=[
                ProjectData(name=Keys.BESS_SETPOINT_KEY, value=150.0, timestamp=0.0)
            ]
        )
        server.expose_server = Mock()
        return server

    @pytest.fixture
    def adapter(self, mock_driver_bess, mock_driver_pv, mock_server):
        """Crée un Adapter avec des drivers mock."""
        return Adapter(drivers=[mock_driver_bess, mock_driver_pv], server=mock_server)

    def test_adapter_initialization(self, adapter):
        """Test l'initialisation de l'Adapter."""
        assert len(adapter.drivers) == 2
        assert adapter.global_system_obs == SystemObs()

    def test_read_and_aggregate_success(
        self, adapter, mock_driver_bess, mock_driver_pv, mock_server
    ):
        """Test read_and_aggregate avec succès."""
        result = adapter.read_and_aggregate()

        # Vérifier que tous les drivers ont été appelés
        mock_driver_bess.read.assert_called_once()
        mock_driver_pv.read.assert_called_once()
        mock_server.fill_system_obs.assert_called_once()

        # Vérifier l'agrégation
        assert len(result.bess) == 1
        assert len(result.pv) == 1
        assert len(result.project_data) == 3  # temperature, irradiance, setpoint

        # Vérifier que global_system_obs a été mis à jour
        assert adapter.global_system_obs == result

    def test_read_and_aggregate_driver_error(self, mock_server):
        """Test read_and_aggregate avec erreur d'un driver."""
        failing_driver = Mock()
        failing_driver.read.side_effect = Exception("Driver error")
        failing_driver.get_equipment_type.return_value = EquipmentType.BESS

        working_driver = Mock()
        working_driver.read.return_value = SystemObs(
            bess=[Bess(p=100.0, q=50.0, soc=75.0, timestamp=0.0)]
        )
        working_driver.get_equipment_type.return_value = EquipmentType.BESS

        adapter = Adapter(drivers=[failing_driver, working_driver], server=mock_server)
        result = adapter.read_and_aggregate()

        # Le driver qui fonctionne devrait toujours être lu
        working_driver.read.assert_called_once()
        # Le résultat devrait contenir les données du driver qui fonctionne
        assert len(result.bess) == 1

    def test_send_commands_success(self, adapter, mock_driver_bess, mock_driver_pv):
        """Test send_commands avec succès."""
        commands = [
            Command(pSp=100.0, qSp=50.0, equipment_type=EquipmentType.BESS),
            Command(pSp=200.0, qSp=0.0, equipment_type=EquipmentType.PV),
        ]

        adapter.send_commands(commands)

        # Vérifier que les commandes ont été envoyées aux bons drivers
        mock_driver_bess.write.assert_called_once_with(commands[0])
        mock_driver_pv.write.assert_called_once_with(commands[1])

    def test_send_commands_no_matching_driver(self, adapter):
        """Test send_commands avec un type d'équipement sans driver correspondant."""
        # Créer un adapter avec seulement un driver BESS
        mock_driver_bess = Mock()
        mock_driver_bess.get_equipment_type.return_value = EquipmentType.BESS
        mock_server = Mock()
        adapter = Adapter(drivers=[mock_driver_bess], server=mock_server)

        # Envoyer une commande PV (pas de driver correspondant)
        commands = [Command(pSp=200.0, qSp=0.0, equipment_type=EquipmentType.PV)]
        adapter.send_commands(commands)

        # Le driver BESS ne devrait pas être appelé
        mock_driver_bess.write.assert_not_called()

    def test_send_commands_driver_error(self, adapter, mock_driver_bess):
        """Test send_commands avec erreur d'un driver."""
        mock_driver_bess.write.side_effect = Exception("Write error")

        commands = [Command(pSp=100.0, qSp=50.0, equipment_type=EquipmentType.BESS)]
        # Ne devrait pas lever d'exception, juste logger l'erreur
        adapter.send_commands(commands)

        mock_driver_bess.write.assert_called_once()

    def test_aggregate_multiple_drivers(self, mock_server):
        """Test l'agrégation avec plusieurs drivers du même type."""
        driver1 = Mock()
        driver1.read.return_value = SystemObs(
            bess=[Bess(p=100.0, q=50.0, soc=75.0, timestamp=0.0)]
        )
        driver1.get_equipment_type.return_value = EquipmentType.BESS

        driver2 = Mock()
        driver2.read.return_value = SystemObs(
            bess=[Bess(p=200.0, q=100.0, soc=80.0, timestamp=0.0)]
        )
        driver2.get_equipment_type.return_value = EquipmentType.BESS

        adapter = Adapter(drivers=[driver1, driver2], server=mock_server)
        result = adapter.read_and_aggregate()

        # Les deux BESS devraient être agrégés
        assert len(result.bess) == 2

    def test_aggregate_empty_outputs(self):
        """Test l'agrégation avec des SystemObs vides."""
        driver = Mock()
        driver.read.return_value = SystemObs()
        driver.get_equipment_type.return_value = EquipmentType.BESS

        # Créer un mock serveur qui retourne un SystemObs vide
        mock_server = Mock()
        mock_server.fill_system_obs.return_value = SystemObs()
        mock_server.expose_server = Mock()

        adapter = Adapter(drivers=[driver], server=mock_server)
        result = adapter.read_and_aggregate()

        assert result == SystemObs()

    def test_sync_server(self, adapter, mock_server):
        """Test sync_server."""
        # Mettre à jour global_system_obs
        adapter.global_system_obs = SystemObs(
            bess=[Bess(p=100.0, q=50.0, soc=75.0, timestamp=0.0)]
        )

        adapter.sync_server()

        mock_server.expose_server.assert_called_once_with(adapter.global_system_obs)
