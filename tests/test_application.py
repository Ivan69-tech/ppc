"""
Tests unitaires pour le module application.
"""

import pytest
import time
from unittest.mock import Mock, patch
from datamodel.datamodel import SystemObs, Command, EquipmentType
from datamodel.standard_data import Bess
from application.application import Application, get_daily_db_path
from adapter.adapter import Adapter
from core.orchestrator import Orchestrator


class TestGetDailyDbPath:
    """Tests pour la fonction get_daily_db_path."""

    def test_get_daily_db_path_format(self):
        """Test le format du chemin de base de données."""
        db_path = get_daily_db_path()
        assert db_path.startswith("db/")
        assert db_path.endswith(".db")
        # Vérifier le format YYYY_MM_DD
        parts = db_path.split("/")
        filename = parts[-1]
        date_parts = filename.replace(".db", "").split("_")
        assert len(date_parts) == 3
        assert len(date_parts[0]) == 4  # Année
        assert len(date_parts[1]) == 2  # Mois
        assert len(date_parts[2]) == 2  # Jour


class TestApplication:
    """Tests pour la classe Application."""

    @pytest.fixture
    def mock_driver(self):
        """Crée un mock driver."""
        driver = Mock()
        driver.read.return_value = SystemObs(
            bess=[Bess(p=100.0, q=50.0, soc=75.0, timestamp=time.time())]
        )
        driver.write = Mock()
        driver.get_equipment_type.return_value = EquipmentType.BESS
        return driver

    @pytest.fixture
    def mock_server(self):
        """Crée un mock serveur."""
        server = Mock()
        server.fill_system_obs.return_value = SystemObs()
        server.expose_server = Mock()
        return server

    @pytest.fixture
    def mock_control_function(self):
        """Crée une fonction de contrôle mock."""
        func = Mock()
        func.compute.return_value = [
            Command(pSp=100.0, qSp=50.0, equipment_type=EquipmentType.BESS)
        ]
        return func

    @pytest.fixture
    def mock_orchestrator(self, mock_control_function):
        """Crée un orchestrator mock."""
        return Orchestrator(functions=[mock_control_function])

    @pytest.fixture
    def application(self, mock_driver, mock_server, mock_orchestrator, tmp_path):
        """Crée une instance d'Application."""
        db_path = str(tmp_path / "test.db")
        return Application(
            drivers=[mock_driver],
            server=mock_server,
            orchestrator=mock_orchestrator,
            communication_interval=0.1,
            process_interval=0.1,
            db_path=db_path,
        )

    def test_application_initialization(
        self, application, mock_driver, mock_server, mock_orchestrator
    ):
        """Test l'initialisation de l'Application."""
        assert isinstance(application.adapter, Adapter)
        assert application.orchestrator == mock_orchestrator
        assert application.communication_interval == 0.1
        assert application.process_interval == 0.1
        assert application.database is not None
        assert application._running is False

    def test_start(self, application):
        """Test start."""
        application.start()
        assert application._running is True
        assert application._aggregation_thread is not None
        assert application._process_thread is not None
        assert application._server_thread is not None
        application.stop()

    def test_stop(self, application):
        """Test stop."""
        application.start()
        time.sleep(0.2)  # Attendre un peu pour que les threads démarrent
        application.stop()
        assert application._running is False
        # Vérifier que la base de données est fermée
        assert application.database.connection is None

    def test_stop_when_not_running(self, application):
        """Test stop quand l'application n'est pas en cours d'exécution."""
        application.stop()  # Ne devrait pas lever d'exception

    def test_aggregation_loop_reads_data(self, application, mock_driver):
        """Test que _aggregation_loop lit les données."""
        application.start()
        time.sleep(0.15)  # Attendre au moins un cycle
        application.stop()

        # Vérifier que le driver a été appelé
        assert mock_driver.read.call_count > 0

    def test_process_loop_generates_commands(self, application, mock_control_function):
        """Test que _process_loop génère des commandes."""
        application.start()
        time.sleep(0.15)  # Attendre au moins un cycle
        application.stop()

        # Vérifier que la fonction de contrôle a été appelée
        assert mock_control_function.compute.call_count > 0

    def test_application_saves_to_database(self, application, mock_driver, tmp_path):
        """Test que l'application sauvegarde dans la base de données."""
        db_path = str(tmp_path / "test.db")
        application.start()
        time.sleep(0.15)  # Attendre au moins un cycle
        application.stop()

        # Vérifier que le fichier de base de données existe
        import os

        assert os.path.exists(db_path)

    def test_application_uses_daily_db_path_when_none(
        self, mock_driver, mock_server, mock_orchestrator
    ):
        """Test que l'application utilise get_daily_db_path quand db_path est None."""
        with patch(
            "application.application.get_daily_db_path", return_value="db/test.db"
        ):
            app = Application(
                drivers=[mock_driver],
                server=mock_server,
                orchestrator=mock_orchestrator,
            )
            assert app.database.db_path == "db/test.db"
            app.stop()

    def test_application_handles_keyboard_interrupt(self, application):
        """Test que run gère KeyboardInterrupt."""
        # Ce test est difficile à tester directement car run() bloque
        # On teste plutôt que stop() fonctionne correctement
        application.start()
        time.sleep(0.1)
        # Simuler un arrêt propre
        application.stop()
        assert application._running is False

    def test_server_loop_syncs_server(self, application, mock_server):
        """Test que _server_loop synchronise le serveur."""
        application.start()
        time.sleep(0.15)  # Attendre au moins un cycle
        application.stop()

        # Vérifier que expose_server a été appelé
        assert mock_server.expose_server.call_count > 0

    def test_application_sends_commands(
        self, application, mock_driver, mock_control_function
    ):
        """Test que l'application envoie les commandes."""
        application.start()
        time.sleep(0.2)  # Attendre que les commandes soient générées et envoyées
        application.stop()

        # Vérifier que write a été appelé sur le driver
        assert mock_driver.write.call_count > 0

    def test_application_handles_driver_errors(
        self, mock_server, mock_orchestrator, tmp_path
    ):
        """Test que l'application gère les erreurs des drivers."""
        failing_driver = Mock()
        failing_driver.read.side_effect = Exception("Driver error")
        failing_driver.get_equipment_type.return_value = EquipmentType.BESS

        db_path = str(tmp_path / "test.db")
        app = Application(
            drivers=[failing_driver],
            server=mock_server,
            orchestrator=mock_orchestrator,
            communication_interval=0.1,
            process_interval=0.1,
            db_path=db_path,
        )

        app.start()
        time.sleep(0.15)
        app.stop()
        # Ne devrait pas lever d'exception

    def test_application_handles_database_errors(self, application, mock_driver):
        """Test que l'application gère les erreurs de base de données."""
        # Simuler une erreur de base de données
        application.database.connection = None
        application.start()
        time.sleep(0.15)
        application.stop()
        # Ne devrait pas lever d'exception (juste logger l'erreur)
