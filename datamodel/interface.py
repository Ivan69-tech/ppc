from typing import Protocol


class TimestampedData(Protocol):
    @property
    def timestamp(self) -> float: ...
