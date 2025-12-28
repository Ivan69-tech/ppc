import time
import threading
from enum import Enum
from typing import Optional
from dataclasses import dataclass


class WatchdogState(Enum):
    """États possibles du watchdog."""

    ONLINE = "online"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class WatchdogStatus:
    """Statut du watchdog à un instant donné."""

    state: WatchdogState
    last_value: float
    last_update_time: float
    timeout_seconds: float


class Watchdog:
    """
    Gère un watchdog pour surveiller l'état de connexion d'un équipement.

    Le watchdog détecte si un équipement est en ligne en vérifiant que
    la valeur du registre watchdog change régulièrement (heartbeat).
    Si aucune mise à jour n'est reçue pendant le timeout, l'état passe à DISCONNECTED.
    """

    def __init__(
        self,
        timeout_seconds: float = 5.0,
        min_heartbeat_interval: float = 0.5,
    ):
        """
        Initialise le watchdog.

        Args:
            timeout_seconds: Délai en secondes avant de considérer l'équipement comme déconnecté
            min_heartbeat_interval: Intervalle minimum entre deux heartbeats valides (secondes)
            expected_value_range: Plage de valeurs attendues (min, max). Si None, toutes les valeurs sont acceptées.
        """
        self.timeout_seconds = timeout_seconds
        self.min_heartbeat_interval = min_heartbeat_interval

        # État interne protégé par un verrou
        self._lock = threading.Lock()
        self._last_value: Optional[float] = None
        self._last_update_time: Optional[float] = None
        self._last_heartbeat_time: Optional[float] = None
        self._current_state: WatchdogState = WatchdogState.UNKNOWN

    def update(self, value: float, timestamp: Optional[float] = None) -> None:
        """
        Met à jour le watchdog avec une nouvelle valeur.

        Args:
            value: Nouvelle valeur du registre watchdog
            timestamp: Timestamp de la mise à jour (si None, utilise time.time())
        """
        if timestamp is None:
            timestamp = time.time()

        with self._lock:
            # Vérifier si c'est un heartbeat valide (uniquement si la valeur change)
            # Cela permet de détecter si quelqu'un écrit réellement sur le registre
            is_valid_heartbeat = False

            if self._last_value is None:
                # Première mise à jour : on initialise juste la valeur
                # On ne considère pas cela comme un heartbeat valide
                # Le watchdog reste DISCONNECTED jusqu'à ce qu'un changement soit détecté
                self._last_value = value
                self._last_update_time = timestamp
                # L'état reste DISCONNECTED ou UNKNOWN
                if self._current_state == WatchdogState.UNKNOWN:
                    self._current_state = WatchdogState.DISCONNECTED
                return

            if self._last_value != value:
                # La valeur a changé, c'est un heartbeat valide
                # C'est le seul cas où on considère un heartbeat valide
                is_valid_heartbeat = True

            if is_valid_heartbeat:
                self._last_heartbeat_time = timestamp
                self._current_state = WatchdogState.ONLINE

            # Toujours mettre à jour la dernière valeur et le timestamp
            # même si ce n'est pas un heartbeat valide
            # Cela permet de détecter le timeout si la valeur ne change pas
            self._last_value = value
            self._last_update_time = timestamp

    def get_status(self) -> WatchdogStatus:
        """
        Retourne le statut actuel du watchdog.

        Returns:
            WatchdogStatus contenant l'état, la dernière valeur et le timestamp
        """
        with self._lock:
            current_time = time.time()
            state = self._current_state

            # Vérifier si on est en timeout
            # On utilise _last_heartbeat_time car c'est le dernier moment où on a eu un heartbeat valide
            # Si la valeur ne change pas, _last_heartbeat_time ne sera pas mis à jour
            if (
                self._last_heartbeat_time is not None
                and (current_time - self._last_heartbeat_time) > self.timeout_seconds
            ):
                state = WatchdogState.DISCONNECTED
                self._current_state = WatchdogState.DISCONNECTED

            elif self._last_heartbeat_time is None and self._last_value is not None:
                # Si on a une valeur mais jamais de heartbeat valide, on est en DISCONNECTED
                # Vérifier le timeout depuis la première valeur
                if (
                    self._last_update_time is not None
                    and (current_time - self._last_update_time) > self.timeout_seconds
                ):
                    state = WatchdogState.DISCONNECTED
                    self._current_state = WatchdogState.DISCONNECTED

                else:
                    # On a une valeur mais pas de heartbeat valide, on est en DISCONNECTED
                    state = WatchdogState.DISCONNECTED
                    self._current_state = WatchdogState.DISCONNECTED

            last_value = self._last_value if self._last_value is not None else 0.0
            last_update = (
                self._last_update_time if self._last_update_time is not None else 0.0
            )

            return WatchdogStatus(
                state=state,
                last_value=last_value,
                last_update_time=last_update,
                timeout_seconds=self.timeout_seconds,
            )

    def get_state(self) -> WatchdogState:
        """
        Retourne l'état actuel du watchdog.

        Returns:
            WatchdogState actuel
        """
        return self.get_status().state

    def is_online(self) -> bool:
        """
        Vérifie si l'équipement est en ligne.

        Returns:
            True si l'état est ONLINE, False sinon
        """
        return self.get_state() == WatchdogState.ONLINE

    def is_disconnected(self) -> bool:
        """
        Vérifie si l'équipement est déconnecté.

        Returns:
            True si l'état est DISCONNECTED, False sinon
        """
        return self.get_state() == WatchdogState.DISCONNECTED
