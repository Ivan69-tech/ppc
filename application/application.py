# application/application.py
import threading
from collections import deque
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from communication.interface import Driver
from communication.interface import Server
from adapter.adapter import Adapter
from core.orchestrator import Orchestrator
from datamodel.datamodel import SystemObs, Command
from database.database import Database

logger = logging.getLogger(__name__)


def get_daily_db_path() -> str:
    """
    Génère le chemin de la base de données basé sur la date du jour.
    Format: db/YYYY_MM_DD.db

    Returns:
        Chemin vers le fichier de base de données
    """
    today = datetime.now()
    db_dir = Path("db")
    db_dir.mkdir(exist_ok=True)
    db_filename = f"{today.year}_{today.month:02d}_{today.day:02d}.db"
    return str(db_dir / db_filename)


class Application:
    """
    Application principale qui orchestre le flux de données entre les couches.
    Coordonne les threads, délègue la communication aux drivers à l'Adapter,
    et orchestre le traitement métier via l'Orchestrator.
    Encapsule la logique de threading, queues et verrous.
    """

    def __init__(
        self,
        drivers: List[Driver],
        server: Server,
        orchestrator: Orchestrator,
        communication_interval: float = 1.0,
        process_interval: float = 1.0,
        db_path: Optional[str] = None,
    ):
        """
        Initialise l'application.

        Args:
            drivers: Liste des drivers de communication (Modbus, etc.)
            orchestrator: Orchestrateur pour le traitement des mesures
            communication_interval: Intervalle entre les lectures/écritures (secondes)
            process_interval: Intervalle entre les traitements (secondes)
            db_path: Chemin vers le fichier de base de données (.db).
                     Si None, utilise automatiquement db/YYYY_MM_DD.db basé sur la date du jour.
        """
        self.orchestrator = orchestrator

        # Adapter gère la communication avec les drivers
        self.adapter: Adapter = Adapter(drivers=drivers, server=server)
        self.communication_interval = communication_interval
        self.process_interval = process_interval

        # Base de données pour sauvegarder les données agrégées
        # Utilise le chemin basé sur la date du jour si non spécifié
        if db_path is None:
            db_path = get_daily_db_path()
        self.database = Database(db_path)

        # Deques avec maxlen=1 : remplace automatiquement l'ancien élément
        self.dataobs_deque: deque[SystemObs] = deque(maxlen=1)
        self.cmd_deque: deque[List[Command]] = deque(maxlen=1)

        # Verrous pour la sécurité thread
        self.dataobs_lock = threading.Lock()
        self.cmd_lock = threading.Lock()

        # Event pour signaler l'arrêt propre
        self._stop_event = threading.Event()
        self._running = False

        # Références aux threads
        self._aggregation_thread: Optional[threading.Thread] = None
        self._process_thread: Optional[threading.Thread] = None
        self._server_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Démarre les threads de communication et traitement."""
        if self._running:
            return

        self._stop_event.clear()
        self._running = True

        # Thread pour l'agrégation des données
        self._aggregation_thread = threading.Thread(
            target=self._aggregation_loop, daemon=True
        )
        # Thread pour le traitement
        self._process_thread = threading.Thread(target=self._process_loop, daemon=True)
        # Thread pour la synchronisation du serveur Modbus
        self._server_thread = threading.Thread(target=self._server_loop, daemon=True)

        self._aggregation_thread.start()
        self._process_thread.start()
        self._start_modbus_server()
        self._server_thread.start()

    def stop(self) -> None:
        """Arrête proprement les threads."""
        if not self._running:
            return

        self._running = False
        self._stop_event.set()

        # Attendre que les threads se terminent (avec timeout)
        if self._aggregation_thread:
            self._aggregation_thread.join(timeout=2.0)
        if self._process_thread:
            self._process_thread.join(timeout=2.0)
        if self._server_thread:
            self._server_thread.join(timeout=2.0)

        # Arrêter le serveur Modbus
        self._stop_modbus_server()

        # Fermer la connexion à la base de données
        self.database.close()

    def run(self) -> None:
        """
        Méthode de blocage qui démarre l'application et attend jusqu'à interruption.
        Gère KeyboardInterrupt pour un arrêt propre.
        """
        self.start()
        try:
            while self._running:
                time.sleep(0.1)  # Petite pause pour éviter de consommer trop de CPU
        except KeyboardInterrupt:
            logger.info("Arrêt du logiciel demandé par l'utilisateur...")
        finally:
            self.stop()

    def _aggregation_loop(self) -> None:
        """
        Boucle d'agrégation : délègue la collecte et l'agrégation des données à l'Adapter,
        puis met les données à disposition pour le traitement.
        """
        while not self._stop_event.is_set():
            try:
                # Déléguer la lecture et l'agrégation à l'Adapter
                aggregated_data = self.adapter.read_and_aggregate()

                # Stocker les données agrégées
                with self.dataobs_lock:
                    self.dataobs_deque.append(aggregated_data)

                # Sauvegarder les données agrégées dans la base de données
                try:
                    self.database.save_system_obs(aggregated_data)
                except Exception as e:
                    logger.error(
                        f"Erreur lors de la sauvegarde en base de données: {e}",
                        exc_info=True,
                    )

                logger.debug(f"Données agrégées: {aggregated_data}")

                # Envoyer les commandes si disponibles (délégué à l'Adapter)
                with self.cmd_lock:
                    if self.cmd_deque:
                        commands = self.cmd_deque.popleft()
                        self.adapter.send_commands(commands)

            except Exception as e:
                logger.error(f"Erreur dans la boucle d'agrégation: {e}", exc_info=True)

            # Attendre l'intervalle ou l'arrêt
            self._stop_event.wait(self.communication_interval)

    def _start_modbus_server(self) -> None:
        """
        Démarre le serveur Modbus.
        Le serveur Modbus est démarré dans son propre thread par la méthode expose_server.
        """
        try:
            # Initialiser le serveur avec un SystemObs vide
            # Le serveur sera mis à jour régulièrement par _server_loop
            initial_system_obs = SystemObs()
            self.adapter.server.expose_server(initial_system_obs)
            logger.info("Serveur Modbus démarré")
        except Exception as e:
            logger.error(
                f"Erreur lors du démarrage du serveur Modbus: {e}", exc_info=True
            )

    def _stop_modbus_server(self) -> None:
        """Arrête le serveur Modbus."""
        try:
            # Le serveur Modbus s'arrête automatiquement quand le thread principal se termine
            # car il est démarré en mode daemon dans ModbusServer.expose_server()
            # Vérifier si c'est une instance de ModbusServer pour accéder à server_running
            from communication.server.modbus_server import ModbusServer

            if isinstance(self.adapter.server, ModbusServer):
                self.adapter.server.server_running = False
            logger.info("Serveur Modbus arrêté")
        except Exception as e:
            logger.error(
                f"Erreur lors de l'arrêt du serveur Modbus: {e}", exc_info=True
            )

    def _server_loop(self) -> None:
        """Boucle de synchronisation avec le serveur Modbus."""
        while not self._stop_event.is_set():
            try:
                # Synchroniser le serveur avec les données agrégées actuelles
                self.adapter.sync_server()
            except Exception as e:
                logger.error(
                    f"Erreur dans la boucle de synchronisation avec le serveur: {e}",
                    exc_info=True,
                )
            self._stop_event.wait(self.communication_interval)

    def _process_loop(self) -> None:
        """Boucle de traitement : traite les mesures agrégées et génère les commandes."""
        while not self._stop_event.is_set():
            try:
                # Lire la dernière mesure disponible
                with self.dataobs_lock:
                    if self.dataobs_deque:
                        dataobs = self.dataobs_deque[0]
                    else:
                        dataobs = None

                if dataobs is not None:
                    commands = self.orchestrator.step(dataobs)
                    # append() remplace automatiquement l'ancienne liste de commandes si maxlen=1
                    if commands:
                        with self.cmd_lock:
                            self.cmd_deque.append(commands)

            except Exception as e:
                logger.error(f"Erreur dans la boucle de traitement: {e}", exc_info=True)

            # Attendre l'intervalle ou l'arrêt
            self._stop_event.wait(self.process_interval)
