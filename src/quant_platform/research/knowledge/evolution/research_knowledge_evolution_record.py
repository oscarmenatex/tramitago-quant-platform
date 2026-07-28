from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ResearchKnowledgeEvolutionRecord:
    """An immutable version of validated knowledge created from new evidence."""

    evolution_id: str
    previous_knowledge_id: str
    candidate_id: str
    result_id: str
    evidence_result_id: str
    knowledge_type: str
    description: str
    version: str
    created_at: datetime
    status: str = "VALIDATED"

    @property
    def knowledge_id(self) -> str:
        """Expose an evolved version through the common KnowledgeVersion contract."""
        return self.evolution_id
