"""Research definition record representation."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ResearchRecord:
    """Administrative representation of a research definition."""

    research_id: str
    name: str
    objective: str
    dataset_id: str
    dataset_version: str
    created_at: datetime
    status: str
