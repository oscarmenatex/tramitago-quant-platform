from __future__ import annotations

from quant_platform.research.knowledge.evolution.research_knowledge_evolution_record import (
    ResearchKnowledgeEvolutionRecord,
)
from quant_platform.research.knowledge.evolution.research_knowledge_evolution_registry import (
    ResearchKnowledgeEvolutionRegistry,
)


class ResearchKnowledgeEvolutionService:
    """Creates a new, traceable knowledge version without changing its predecessor."""

    def __init__(self, registry: ResearchKnowledgeEvolutionRegistry) -> None:
        self._registry = registry

    def evolve(
        self,
        knowledge_version_id: str,
        previous_knowledge_version_id: str,
        evidence_result_id: str,
        description: str,
    ) -> ResearchKnowledgeEvolutionRecord:
        return self._registry.register(
            knowledge_version_id=knowledge_version_id,
            previous_knowledge_version_id=previous_knowledge_version_id,
            evidence_result_id=evidence_result_id,
            description=description,
        )
