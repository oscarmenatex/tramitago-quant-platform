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
        evolution_id: str,
        previous_knowledge_id: str,
        evidence_result_id: str,
        description: str,
    ) -> ResearchKnowledgeEvolutionRecord:
        return self._registry.register(
            evolution_id=evolution_id,
            previous_knowledge_id=previous_knowledge_id,
            evidence_result_id=evidence_result_id,
            description=description,
        )
