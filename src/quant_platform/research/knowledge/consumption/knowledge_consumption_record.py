from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class KnowledgeConsumptionRecord:
    """Public, immutable read model for reusable knowledge."""

    knowledge_id: str
    knowledge_version_id: str
    knowledge_type: str
    description: str
    status: str
    confidence_reference: str | None
    relationship_references: tuple[str, ...]
    source_reference: str
    version: str
    created_at: datetime | None


@dataclass(frozen=True)
class KnowledgeConfidenceConsumptionRecord:
    """Immutable public view of confidence associated with a knowledge item."""

    confidence_reference: str
    confidence_level: str
    status: str
    version: str
    created_at: datetime | None


@dataclass(frozen=True)
class KnowledgeRelationshipConsumptionRecord:
    """Immutable public view of a relationship associated with knowledge."""

    relationship_reference: str
    source_knowledge_version_id: str
    target_knowledge_version_id: str
    relationship_type: str
    version: str
    created_at: datetime | None
