from transitions import Machine
from datamodel.datamodel import SystemObs
from keys.keys import Keys
from metier.utils.watchog import Watchdog, WatchdogState


class StateMachine:
    """
    Machine à états pour gérer les transitions entre les états AUTO et ERROR.

    La machine passe en état ERROR si le watchdog BESS est disconnected,
    sinon elle reste en état AUTO.

    Utilise la bibliothèque transitions pour gérer les états et transitions.
    """

    # États possibles
    states = ["auto", "error"]

    def __init__(
        self, timeout_seconds: float = 5.0, min_heartbeat_interval: float = 0.5
    ):
        """
        Initialise la machine à états.

        Args:
            timeout_seconds: Délai en secondes avant de considérer l'équipement comme déconnecté
            min_heartbeat_interval: Intervalle minimum entre deux heartbeats valides (secondes)
        """
        # Instancier le Watchdog
        self.watchdog = Watchdog(
            timeout_seconds=timeout_seconds,
            min_heartbeat_interval=min_heartbeat_interval,
        )

        # Initialiser la machine à états avec transitions
        # L'état initial est "auto"
        self.machine = Machine(  # type: ignore
            model=self,
            states=StateMachine.states,
            initial="auto",
            auto_transitions=False,  # Désactiver les transitions automatiques
        )

        # Définir les transitions
        self.machine.add_transition(  # type: ignore
            "to_error", "auto", "error", conditions="is_watchdog_disconnected"
        )
        self.machine.add_transition(  # type: ignore
            "to_auto", "error", "auto", conditions="is_watchdog_connected"
        )
        # Permettre de rester dans le même état si les conditions ne sont pas remplies
        self.machine.add_transition("stay_auto", "auto", "auto")  # type: ignore
        self.machine.add_transition("stay_error", "error", "error")  # type: ignore

    def update(self, system_obs: SystemObs) -> str:
        """
        Met à jour la machine à états en fonction du SystemObs.

        Args:
            system_obs: SystemObs contenant les données du système, notamment
                       le watchdog BESS dans project_data

        Returns:
            str: L'état actuel après la mise à jour ("auto" ou "error")
        """
        # Récupérer la valeur du watchdog BESS depuis le SystemObs
        watchdog_project_data = system_obs.get_project_data(Keys.WATCHDOG_BESS_KEY)

        if watchdog_project_data is not None:
            # Mettre à jour le watchdog avec la valeur et le timestamp
            self.watchdog.update(
                watchdog_project_data.value, watchdog_project_data.timestamp
            )

        # Déclencher les transitions en fonction de l'état du watchdog
        if self.state == "auto":  # type: ignore
            if self.is_watchdog_disconnected():
                self.to_error()  # type: ignore
            else:
                self.stay_auto()  # type: ignore
        elif self.state == "error":  # type: ignore
            if self.is_watchdog_connected():
                self.to_auto()  # type: ignore
            else:
                self.stay_error()  # type: ignore

        return self.state  # type: ignore

    def is_watchdog_disconnected(self) -> bool:
        """
        Condition pour la transition vers ERROR.
        Vérifie si le watchdog est disconnected.

        Returns:
            True si le watchdog est disconnected, False sinon
        """
        return self.watchdog.get_state() == WatchdogState.DISCONNECTED

    def is_watchdog_connected(self) -> bool:
        """
        Condition pour la transition vers AUTO.
        Vérifie si le watchdog n'est pas disconnected.

        Returns:
            True si le watchdog n'est pas disconnected, False sinon
        """
        return self.watchdog.get_state() != WatchdogState.DISCONNECTED

    def get_state(self) -> str:
        """
        Retourne l'état actuel de la machine à états.

        Returns:
            str: L'état actuel ("auto" ou "error")
        """
        return self.state  # type: ignore

    def is_error(self) -> bool:
        """
        Vérifie si la machine est en état ERROR.

        Returns:
            True si l'état est ERROR, False sinon
        """
        return self.state == "error"  # type: ignore

    def is_auto(self) -> bool:
        """
        Vérifie si la machine est en état AUTO.

        Returns:
            True si l'état est AUTO, False sinon
        """
        return self.state == "auto"  # type: ignore
