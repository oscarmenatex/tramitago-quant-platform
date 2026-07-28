from __future__ import annotations

from typing import List, Optional

from quant_platform.research.knowledge.research_knowledge_record import (
    ResearchKnowledgeRecord,
)
from quant_platform.research.knowledge.research_knowledge_registry import (
    ResearchKnowledgeRegistry,
)


class ResearchKnowledgeAccess:
    """Read-only access adapter for research knowledge artifacts."""

    def __init__(self, registry: ResearchKnowledgeRegistry) -> None:
        self._registry = registry

    def get(self, knowledge_id: str) -> Optional[ResearchKnowledgeRecord]:
        return self._registry.get(knowledge_id)

    def exists(self, knowledge_id: str) -> bool:
        return self._registry.exists(knowledge_id)

    def list(self) -> List[ResearchKnowledgeRecord]:
        return self._registry.list()
