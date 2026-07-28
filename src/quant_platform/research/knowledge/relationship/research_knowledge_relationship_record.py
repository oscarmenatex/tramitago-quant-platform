from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ResearchKnowledgeRelationshipRecord:
    """Representation of an explicit relationship between two validated knowledge artifacts."""

    knowledge_relationship_id: str
    source_knowledge_id: str
    target_knowledge_id: str
    relationship_type: str
    version: str = "1"
    created_at: datetime | None = None
