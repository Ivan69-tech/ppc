from dataclasses import dataclass
from .interface import TimestampedData


@dataclass
class ProjectData:
    project_data: dict[str, TimestampedData]
