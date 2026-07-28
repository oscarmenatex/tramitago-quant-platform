from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class ResearchConfigurationRecord:
    """A concrete research execution configuration."""

    configuration_id: str
    research_id: str
    access_policy: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None
