from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ResearchExecutionRecord:
    """Representation of a research execution evidence record."""

    execution_id: str
    research_id: str
    configuration_id: str
    dataset_id: str
    dataset_version: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    status: str = "CREATED"
