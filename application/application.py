# core/application.py
import threading
from collections import deque
import time
from typing import Optional

from communication.interface import Driver
from core.orchestrator import Orchestrator
from datamodel.datamodel import DataModel, Command
from context.context import Context


class Application:
    """
    Application principale qui coordonne la communication et le traitement.
    Encapsule la logique de threading, queues et verrous.
    """

    def __init__(
        self,
        driver: Driver,
        orchestrator: Orchestrator,
        context: Context,
        communication_interval: float = 1.0,
        process_interval: float = 5.0,
    ):
        """
        Initialise l'application.

        Args:
            driver: Driver de communication (Modbus, etc.)
            orchestrator: Orchestrateur pour le traitement des mesures
            communication_interval: Intervalle entre les lectures/écritures (secondes)
            process_interval: Intervalle entre les traitements (secondes)
        """
        self.driver = driver
        self.orchestrator = orchestrator
        self.context = context
        self.communication_interval = communication_interval
        self.process_interval = process_interval

        # Deques avec maxlen=1 : remplace automatiquement l'ancien élément
        self.dataobs_deque: deque[DataModel] = deque(maxlen=1)
        self.cmd_deque: deque[Command] = deque(maxlen=1)

        # Verrous pour la sécurité thread
        self.dataobs_lock = threading.Lock()
        self.cmd_lock = threading.Lock()

        # Event pour signaler l'arrêt propre
        self._stop_event = threading.Event()
        self._running = False

        # Références aux threads
        self._communication_thread: Optional[threading.Thread] = None
        self._process_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Démarre les threads de communication et traitement."""
        if self._running:
            return

        self._stop_event.clear()
        self._running = True

        self._communication_thread = threading.Thread(
            target=self._communication_loop, daemon=True
        )
        self._process_thread = threading.Thread(target=self._process_loop, daemon=True)

        self._communication_thread.start()
        self._process_thread.start()

    def stop(self) -> None:
        """Arrête proprement les threads."""
        if not self._running:
            return

        self._running = False
        self._stop_event.set()

        # Attendre que les threads se terminent (avec timeout)
        if self._communication_thread:
            self._communication_thread.join(timeout=2.0)
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

    def _communication_loop(self) -> None:
        """Boucle de communication : lit les mesures et écrit les commandes."""
        while not self._stop_event.is_set():
            try:
                dataobs = self.driver.read(self.context)
                with self.dataobs_lock:
                    self.dataobs_deque.append(dataobs)
                print(f"dataobs = {dataobs}")

                # Lire la commande si disponible
                with self.cmd_lock:
                    if self.cmd_deque:
                        cmd = self.cmd_deque.popleft()
                        self.driver.write(cmd)

            except Exception as e:
                print(f"Erreur dans la boucle de communication: {e}")

            # Attendre l'intervalle ou l'arrêt
            self._stop_event.wait(self.communication_interval)

    def _process_loop(self) -> None:
        """Boucle de traitement : traite les mesures et génère les commandes."""
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
