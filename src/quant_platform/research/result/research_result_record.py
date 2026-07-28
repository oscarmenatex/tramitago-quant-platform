from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ResearchResultRecord:
    """Representation of a research result evidence record."""

    result_id: str
    execution_id: str
    created_at: datetime | None = None
    status: str = "CREATED"
