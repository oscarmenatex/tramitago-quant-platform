from __future__ import annotations

from typing import List, Optional

from quant_platform.research.knowledge.candidate.research_knowledge_candidate_record import (
    ResearchKnowledgeCandidateRecord,
)
from quant_platform.research.knowledge.candidate.research_knowledge_candidate_registry import (
    ResearchKnowledgeCandidateRegistry,
)


class ResearchKnowledgeCandidateAccess:
    """Read-only access adapter for knowledge candidates."""

    def __init__(self, registry: ResearchKnowledgeCandidateRegistry) -> None:
        self._registry = registry

    def get(
        self, knowledge_candidate_id: str
    ) -> Optional[ResearchKnowledgeCandidateRecord]:
        return self._registry.get(knowledge_candidate_id)

    def exists(self, knowledge_candidate_id: str) -> bool:
        return self._registry.exists(knowledge_candidate_id)

    def list(self) -> List[ResearchKnowledgeCandidateRecord]:
        return self._registry.list()
