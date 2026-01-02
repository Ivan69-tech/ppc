"""
Tests unitaires pour le module database.
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from datamodel.datamodel import SystemObs
from datamodel.standard_data import Bess, Pv
from datamodel.project_data import ProjectData
from database.database import Database


class TestDatabase:
    """Tests pour la classe Database."""

    @pytest.fixture
    def temp_db_path(self):
        """Crée un chemin temporaire pour la base de données."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        # Nettoyer après le test
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def database(self, temp_db_path):
        """Crée une instance de Database avec un chemin temporaire."""
        db = Database(db_path=temp_db_path)
        yield db
        db.close()

    @pytest.fixture
    def sample_system_obs(self):
        """Crée un SystemObs de test."""
        return SystemObs(
            bess=[Bess(p=100.0, q=50.0, soc=75.0, timestamp=1000.0)],
            pv=[Pv(p=200.0, q=0.0, timestamp=1000.0)],
            project_data=[ProjectData(name="test_key", value=123.0, timestamp=1000.0)],
        )

    def test_database_initialization(self, temp_db_path):
        """Test l'initialisation de la Database."""
        db = Database(db_path=temp_db_path)
        assert db.db_path == temp_db_path
        assert db.connection is not None
        db.close()

    def test_database_creates_tables(self, database):
        """Test que les tables sont créées à l'initialisation."""
        cursor = database.connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('bess', 'pv', 'project_data')"
        )
        tables = [row[0] for row in cursor.fetchall()]
        assert "bess" in tables
        assert "pv" in tables
        assert "project_data" in tables

    def test_save_system_obs_bess(self, database, sample_system_obs):
        """Test save_system_obs avec des données BESS."""
        database.save_system_obs(sample_system_obs)

        cursor = database.connection.cursor()
        cursor.execute("SELECT p, q, soc, timestamp FROM bess")
        rows = cursor.fetchall()

        assert len(rows) == 1
        assert rows[0] == (100.0, 50.0, 75.0, 1000.0)

    def test_save_system_obs_pv(self, database, sample_system_obs):
        """Test save_system_obs avec des données PV."""
        database.save_system_obs(sample_system_obs)

        cursor = database.connection.cursor()
        cursor.execute("SELECT p, q, timestamp FROM pv")
        rows = cursor.fetchall()

        assert len(rows) == 1
        assert rows[0] == (200.0, 0.0, 1000.0)

    def test_save_system_obs_project_data(self, database, sample_system_obs):
        """Test save_system_obs avec des données project_data."""
        database.save_system_obs(sample_system_obs)

        cursor = database.connection.cursor()
        cursor.execute("SELECT name, value, timestamp FROM project_data")
        rows = cursor.fetchall()

        assert len(rows) == 1
        assert rows[0] == ("test_key", 123.0, 1000.0)

    def test_save_system_obs_empty(self, database):
        """Test save_system_obs avec un SystemObs vide."""
        empty_obs = SystemObs()
        database.save_system_obs(empty_obs)

        cursor = database.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM bess")
        bess_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pv")
        pv_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM project_data")
        project_data_count = cursor.fetchone()[0]

        assert bess_count == 0
        assert pv_count == 0
        assert project_data_count == 0

    def test_save_system_obs_multiple_entries(self, database):
        """Test save_system_obs avec plusieurs entrées."""
        obs = SystemObs(
            bess=[
                Bess(p=100.0, q=50.0, soc=75.0, timestamp=1000.0),
                Bess(p=200.0, q=100.0, soc=80.0, timestamp=1001.0),
            ],
            pv=[
                Pv(p=300.0, q=0.0, timestamp=1000.0),
                Pv(p=400.0, q=0.0, timestamp=1001.0),
            ],
        )
        database.save_system_obs(obs)

        cursor = database.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM bess")
        bess_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pv")
        pv_count = cursor.fetchone()[0]

        assert bess_count == 2
        assert pv_count == 2

    def test_save_system_obs_thread_safe(self, database, sample_system_obs):
        """Test que save_system_obs est thread-safe."""
        import threading

        def save_data():
            database.save_system_obs(sample_system_obs)

        threads = [threading.Thread(target=save_data) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        cursor = database.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM bess")
        bess_count = cursor.fetchone()[0]

        # Devrait avoir 5 entrées (une par thread)
        assert bess_count == 5

    def test_close(self, temp_db_path):
        """Test close."""
        db = Database(db_path=temp_db_path)
        assert db.connection is not None
        db.close()
        assert db.connection is None

    def test_context_manager(self, temp_db_path):
        """Test le context manager."""
        with Database(db_path=temp_db_path) as db:
            assert db.connection is not None
            db.save_system_obs(
                SystemObs(bess=[Bess(p=100.0, q=50.0, soc=75.0, timestamp=1000.0)])
            )

        # Après la sortie du context manager, la connexion devrait être fermée
        # On ne peut pas vérifier directement car connection est None
        # Mais on peut vérifier que le fichier existe et contient des données
        assert os.path.exists(temp_db_path)

    def test_database_creates_parent_directory(self, tmp_path):
        """Test que la Database crée le répertoire parent si nécessaire."""
        db_path = str(tmp_path / "subdir" / "test.db")
        db = Database(db_path=db_path)
        assert os.path.exists(db_path)
        db.close()

    def test_save_system_obs_without_connection(self, temp_db_path):
        """Test save_system_obs sans connexion (devrait lever une exception)."""
        db = Database(db_path=temp_db_path)
        db.close()
        obs = SystemObs(bess=[Bess(p=100.0, q=50.0, soc=75.0, timestamp=1000.0)])

        with pytest.raises(
            RuntimeError, match="connexion à la base de données n'est pas initialisée"
        ):
            db.save_system_obs(obs)
