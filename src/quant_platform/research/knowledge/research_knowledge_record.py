from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ResearchKnowledgeRecord:
    """Representation of a reusable research knowledge artifact."""

    knowledge_id: str
    result_id: str
    knowledge_type: str
    description: str
    version: str = "v1"
    created_at: datetime | None = None
    status: str = "CREATED"
