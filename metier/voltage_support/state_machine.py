from transitions import Machine
from datamodel.datamodel import SystemObs
from keys.keys import Keys
from metier.utils.watchog import Watchdog, WatchdogState
from dataclasses import dataclass

# États
states = ["auto", "error"]

# Transitions
transitions = [
    {
        "trigger": "update_state",
        "source": "auto",
        "dest": "error",
        "conditions": "is_watchdog_disconnected",
    },
    {
        "trigger": "update_state",
        "source": "error",
        "dest": "auto",
        "conditions": "is_watchdog_connected",
    },
]


@dataclass
class State:
    AUTO: str = "auto"
    ERROR: str = "error"


class StateMachine:
    """
    Machine à états pour gérer les transitions entre les états AUTO et ERROR.

    La machine passe en état ERROR si le watchdog BESS est disconnected,
    sinon elle reste en état AUTO.

    Utilise la bibliothèque transitions pour gérer les états et transitions.
    """

    def __init__(
        self, timeout_seconds: float = 5.0, min_heartbeat_interval: float = 0.5
    ):
        self.watchdog = Watchdog(
            timeout_seconds=timeout_seconds,
            min_heartbeat_interval=min_heartbeat_interval,
        )

        self.machine = Machine(
            model=self,
            states=states,
            transitions=transitions,
            initial="error",
        )

    def update(self, system_obs: SystemObs):
        """
        Met à jour la machine à états en fonction du SystemObs.

        Args:
            system_obs: SystemObs contenant les données du système, notamment
                       le watchdog BESS dans project_data


        """
        watchdog_project_data = system_obs.get_project_data(Keys.WATCHDOG_BESS_KEY)

        if watchdog_project_data is not None:
            self.watchdog.update(
                watchdog_project_data.value, watchdog_project_data.timestamp
            )

        self.update_state()  # type: ignore

    def is_watchdog_disconnected(self) -> bool:
        return self.watchdog.get_state() == WatchdogState.DISCONNECTED

    def is_watchdog_connected(self) -> bool:
        return self.watchdog.get_state() != WatchdogState.DISCONNECTED

    def get_state(self) -> str:
        return self.state  # type: ignore

    def is_error(self) -> bool:
        return self.get_state() == State.ERROR

    def is_auto(self) -> bool:
        return self.get_state() == State.AUTO
