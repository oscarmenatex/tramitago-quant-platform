from __future__ import annotations

from typing import List, Optional

from quant_platform.research.knowledge.validation.research_validated_knowledge_record import (
    ResearchValidatedKnowledgeRecord,
)
from quant_platform.research.knowledge.validation.research_validated_knowledge_registry import (
    ResearchValidatedKnowledgeRegistry,
)


class ResearchValidatedKnowledgeAccess:
    """Read-only access adapter for validated knowledge artifacts."""

    def __init__(self, registry: ResearchValidatedKnowledgeRegistry) -> None:
        self._registry = registry

    def get(
        self, knowledge_version_id: str
    ) -> Optional[ResearchValidatedKnowledgeRecord]:
        return self._registry.get(knowledge_version_id)

    def exists(self, knowledge_version_id: str) -> bool:
        return self._registry.exists(knowledge_version_id)

    def list(self) -> List[ResearchValidatedKnowledgeRecord]:
        return self._registry.list()
