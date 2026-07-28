from __future__ import annotations

from typing import List, Optional

from quant_platform.research.knowledge.confidence.research_knowledge_confidence_record import (
    ResearchKnowledgeConfidenceRecord,
)
from quant_platform.research.knowledge.confidence.research_knowledge_confidence_registry import (
    ResearchKnowledgeConfidenceRegistry,
)


class ResearchKnowledgeConfidenceAccess:
    """Read-only access adapter for knowledge-confidence assessments."""

    def __init__(self, registry: ResearchKnowledgeConfidenceRegistry) -> None:
        self._registry = registry

    def get(
        self, knowledge_confidence_id: str
    ) -> Optional[ResearchKnowledgeConfidenceRecord]:
        return self._registry.get(knowledge_confidence_id)

    def exists(self, knowledge_confidence_id: str) -> bool:
        return self._registry.exists(knowledge_confidence_id)

    def list(self) -> List[ResearchKnowledgeConfidenceRecord]:
        return self._registry.list()
