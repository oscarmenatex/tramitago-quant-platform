from __future__ import annotations

from quant_platform.research.knowledge.confidence.research_knowledge_confidence_registry import (
    ResearchKnowledgeConfidenceRegistry,
)
from quant_platform.research.knowledge.confidence.research_knowledge_confidence_record import (
    ResearchKnowledgeConfidenceRecord,
)


class ResearchKnowledgeConfidenceService:
    """Service that creates a confidence artifact from validated knowledge."""

    def __init__(self, registry: ResearchKnowledgeConfidenceRegistry) -> None:
        self._registry = registry

    def assess(
        self,
        knowledge_confidence_id: str,
        validated_knowledge_id: str,
        confidence_level: str,
        version: str = "1",
    ) -> ResearchKnowledgeConfidenceRecord:
        return self._registry.register(
            knowledge_confidence_id=knowledge_confidence_id,
            validated_knowledge_id=validated_knowledge_id,
            confidence_level=confidence_level,
            version=version,
        )
