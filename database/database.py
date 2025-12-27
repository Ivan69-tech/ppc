import sqlite3
import threading
from pathlib import Path
from typing import Optional, Any

from datamodel.datamodel import SystemObs


class Database:
    """
    Classe pour sauvegarder un SystemObs agrégé dans une base de données SQLite.
    """

    def __init__(self, db_path: str = "system_data.db"):
        """
        Initialise la connexion à la base de données.

        Args:
            db_path: Chemin vers le fichier de base de données (.db)
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        # Verrou pour garantir la sécurité thread-safe
        self._lock = threading.Lock()
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Crée les tables nécessaires si elles n'existent pas."""
        # Créer le répertoire parent si nécessaire
        db_path_obj = Path(self.db_path)
        db_path_obj.parent.mkdir(parents=True, exist_ok=True)

        # Ouvrir ou créer la base de données (SQLite crée le fichier s'il n'existe pas)
        # check_same_thread=False permet d'utiliser la connexion depuis différents threads
        self.connection = sqlite3.connect(
            self.db_path, check_same_thread=False, timeout=10.0
        )
        cursor = self.connection.cursor()

        # Table pour les données BESS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bess (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                p REAL NOT NULL,
                q REAL NOT NULL,
                soc REAL NOT NULL,
                timestamp REAL NOT NULL
            )
        """)

        # Table pour les données PV
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pv (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                p REAL NOT NULL,
                q REAL NOT NULL,
                timestamp REAL NOT NULL
            )
        """)

        # Table pour les données de projet
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                project_data REAL NOT NULL,
                timestamp REAL NOT NULL
            )
        """)

        self.connection.commit()

    def save_system_obs(self, system_obs: SystemObs) -> None:
        """
        Sauvegarde tous les objets d'un SystemObs agrégé dans la base de données.
        Thread-safe : utilise un verrou pour garantir l'accès exclusif.

        Args:
            system_obs: SystemObs agrégé contenant les données à sauvegarder
        """
        if self.connection is None:
            raise RuntimeError(
                "La connexion à la base de données n'est pas initialisée"
            )

        # Utiliser un verrou pour garantir la sécurité thread-safe
        with self._lock:
            cursor = self.connection.cursor()
            rows_inserted = 0

            # Sauvegarder les données BESS
            if system_obs.bess:
                for bess in system_obs.bess:
                    cursor.execute(
                        "INSERT INTO bess (p, q, soc, timestamp) VALUES (?, ?, ?, ?)",
                        (bess.p, bess.q, bess.soc, bess.timestamp),
                    )
                    rows_inserted += 1

            # Sauvegarder les données PV
            if system_obs.pv:
                for pv in system_obs.pv:
                    cursor.execute(
                        "INSERT INTO pv (p, q, timestamp) VALUES (?, ?, ?)",
                        (pv.p, pv.q, pv.timestamp),
                    )
                    rows_inserted += 1

            # Sauvegarder les données de projet
            if system_obs.project_data:
                for project_data in system_obs.project_data:
                    cursor.execute(
                        "INSERT INTO project_data (name, project_data, timestamp) VALUES (?, ?, ?)",
                        (
                            project_data.name,
                            project_data.project_data,
                            project_data.timestamp,
                        ),
                    )
                    rows_inserted += 1

            self.connection.commit()

    def close(self) -> None:
        """Ferme la connexion à la base de données."""
        with self._lock:
            if self.connection:
                self.connection.close()
                self.connection = None

    def __enter__(self):
        """Support du context manager."""
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        """Ferme la connexion lors de la sortie du context manager."""
        self.close()
