from __future__ import annotations

from typing import List, Optional

from quant_platform.research.knowledge.relationship.research_knowledge_relationship_record import (
    ResearchKnowledgeRelationshipRecord,
)
from quant_platform.research.knowledge.relationship.research_knowledge_relationship_registry import (
    ResearchKnowledgeRelationshipRegistry,
)


class ResearchKnowledgeRelationshipAccess:
    """Read-only access adapter for knowledge relationships."""

    def __init__(self, registry: ResearchKnowledgeRelationshipRegistry) -> None:
        self._registry = registry

    def get(
        self, knowledge_relationship_id: str
    ) -> Optional[ResearchKnowledgeRelationshipRecord]:
        return self._registry.get(knowledge_relationship_id)

    def exists(self, knowledge_relationship_id: str) -> bool:
        return self._registry.exists(knowledge_relationship_id)

    def list(self) -> List[ResearchKnowledgeRelationshipRecord]:
        return self._registry.list()

    def list_for_knowledge_version(
        self, knowledge_version_id: str
    ) -> List[ResearchKnowledgeRelationshipRecord]:
        return self._registry.list_for_knowledge_version(knowledge_version_id)
