from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ResearchKnowledgeEvolutionRecord:
    """An immutable version of validated knowledge created from new evidence."""

    knowledge_version_id: str
    knowledge_id: str
    previous_knowledge_version_id: str
    candidate_id: str
    result_id: str
    evidence_result_id: str
    knowledge_type: str
    description: str
    version: str
    created_at: datetime
    status: str = "VALIDATED"
