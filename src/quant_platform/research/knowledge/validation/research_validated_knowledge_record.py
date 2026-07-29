from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ResearchValidatedKnowledgeRecord:
    """Representation of a validated knowledge artifact derived from a candidate."""

    knowledge_id: str
    knowledge_version_id: str
    candidate_id: str
    result_id: str
    knowledge_type: str
    description: str
    version: str = "1"
    created_at: datetime | None = None
    status: str = "VALIDATED"
