from dataclasses import dataclass
import threading
from datamodel.interface import TimestampedData


@dataclass
class Context:
    """
    Contexte runtime mutable.
    Alimenté par les drivers.
    Consommé uniquement par les adapters.
    """

    # === Données génériques système ===

    def __init__(self, data: dict[str, TimestampedData]):
        self.data = data

    def __post_init__(self):
        self._lock = threading.Lock()

    def set(self, key: str, value: TimestampedData):
        with self._lock:
            self.data[key] = value

    def get(self, key: str) -> TimestampedData:
        with self._lock:
            return self.data[key]
