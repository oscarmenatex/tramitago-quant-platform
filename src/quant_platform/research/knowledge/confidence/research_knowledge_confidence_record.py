from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ResearchKnowledgeConfidenceRecord:
    """Representation of an assessment of confidence for a validated knowledge artifact."""

    knowledge_confidence_id: str
    validated_knowledge_id: str
    confidence_level: str
    version: str = "1"
    created_at: datetime | None = None
    status: str = "ASSESSED"
