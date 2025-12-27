# application/application.py
import threading
from collections import deque
import time
from typing import Optional, List

from communication.interface import Driver
from adapter.adapter import Adapter
from core.orchestrator import Orchestrator
from datamodel.datamodel import SystemObs, Command


class Application:
    """
    Application principale qui coordonne la communication et le traitement.
    Supporte plusieurs drivers en parallèle avec agrégation des données.
    Encapsule la logique de threading, queues et verrous.
    """

    def __init__(
        self,
        drivers: List[Driver],
        orchestrator: Orchestrator,
        communication_interval: float = 1.0,
        process_interval: float = 1.0,
    ):
        """
        Initialise l'application.

        Args:
            drivers: Liste des drivers de communication (Modbus, etc.)
            orchestrator: Orchestrateur pour le traitement des mesures
            communication_interval: Intervalle entre les lectures/écritures (secondes)
            process_interval: Intervalle entre les traitements (secondes)
        """
        self.drivers = drivers
        self.orchestrator = orchestrator
        # Adapter pour agréger les données des drivers
        self.adapter = Adapter(driver_outputs=[])
        self.communication_interval = communication_interval
        self.process_interval = process_interval

        # Deques avec maxlen=1 : remplace automatiquement l'ancien élément
        self.dataobs_deque: deque[SystemObs] = deque(maxlen=1)
        self.cmd_deque: deque[Command] = deque(maxlen=1)

        # Verrous pour la sécurité thread
        self.dataobs_lock = threading.Lock()
        self.cmd_lock = threading.Lock()

        # Event pour signaler l'arrêt propre
        self._stop_event = threading.Event()
        self._running = False

        # Références aux threads
        self._aggregation_thread: Optional[threading.Thread] = None
        self._process_thread: Optional[threading.Thread] = None

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

        self._aggregation_thread.start()
        self._process_thread.start()

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
            print("\nArrêt du logiciel...")
        finally:
            self.stop()

    def _aggregation_loop(self) -> None:
        """
        Boucle d'agrégation : collecte les données de tous les drivers,
        les agrège et les met à disposition pour le traitement.
        """
        while not self._stop_event.is_set():
            try:
                # Lire les données de tous les drivers
                driver_outputs: list[SystemObs] = []
                for driver in self.drivers:
                    try:
                        system_obs = driver.read()
                        driver_outputs.append(system_obs)
                    except Exception as e:
                        print(f"Erreur lors de la lecture du driver: {e}")

                # Mettre à jour les sorties des drivers dans l'Adapter
                self.adapter.driver_outputs = driver_outputs

                # Agrégation des données via l'Adapter
                aggregated_data = self.adapter.aggregate()

                # Stocker les données agrégées
                with self.dataobs_lock:
                    self.dataobs_deque.append(aggregated_data)

                print(f"Données agrégées: {aggregated_data}")

                # Envoyer la commande si disponible
                with self.cmd_lock:
                    if self.cmd_deque:
                        cmd = self.cmd_deque.popleft()
                        # Router la commande vers le driver correspondant à l'équipement
                        for driver in self.drivers:
                            try:
                                # Vérifier si le driver gère le type d'équipement de la commande
                                if driver.get_equipment_type() == cmd.equipment_type:
                                    driver.write(cmd)
                            except Exception as e:
                                print(f"Erreur lors de l'écriture au driver: {e}")

            except Exception as e:
                print(f"Erreur dans la boucle d'agrégation: {e}")

            # Attendre l'intervalle ou l'arrêt
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
                    cmd = self.orchestrator.step(dataobs)
                    # append() remplace automatiquement l'ancienne commande si maxlen=1
                    with self.cmd_lock:
                        self.cmd_deque.append(cmd)

            except Exception as e:
                print(f"Erreur dans la boucle de traitement: {e}")

            # Attendre l'intervalle ou l'arrêt
            self._stop_event.wait(self.process_interval)
