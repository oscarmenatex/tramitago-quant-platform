from __future__ import annotations

from typing import List, Optional

from quant_platform.research.knowledge.evolution.research_knowledge_evolution_record import (
    ResearchKnowledgeEvolutionRecord,
)
from quant_platform.research.knowledge.evolution.research_knowledge_evolution_registry import (
    ResearchKnowledgeEvolutionRegistry,
)


class ResearchKnowledgeEvolutionAccess:
    """Read-only access adapter for evolved knowledge versions."""

    def __init__(self, registry: ResearchKnowledgeEvolutionRegistry) -> None:
        self._registry = registry

    def get(self, evolution_id: str) -> Optional[ResearchKnowledgeEvolutionRecord]:
        return next(
            (
                version
                for version in self._registry.list()
                if version.evolution_id == evolution_id
            ),
            None,
        )

    def exists(self, evolution_id: str) -> bool:
        return self.get(evolution_id) is not None

    def list(self) -> List[ResearchKnowledgeEvolutionRecord]:
        return self._registry.list()
