from __future__ import annotations

from datetime import datetime

from quant_platform.research.knowledge.candidate.research_knowledge_candidate_registry import (
    ResearchKnowledgeCandidateRegistry,
)
from quant_platform.research.knowledge.validation.research_validated_knowledge_registry import (
    ResearchValidatedKnowledgeRegistry,
)


class ResearchKnowledgeValidationService:
    """Explicit lifecycle process that validates a candidate into a validated knowledge artifact."""

    def __init__(self, candidate_registry: ResearchKnowledgeCandidateRegistry) -> None:
        self._candidate_registry = candidate_registry
        self._validated_registry = ResearchValidatedKnowledgeRegistry(
            candidate_registry
        )

    def validate(self, candidate_id: str, validated_knowledge_id: str) -> object:
        candidate = self._candidate_registry.get(candidate_id)
        if candidate is None:
            raise ValueError(f"unknown candidate '{candidate_id}'")

        if candidate.status != "CANDIDATE":
            raise ValueError(f"candidate '{candidate_id}' is not in CANDIDATE state")

        if self._validated_registry.exists(validated_knowledge_id):
            raise ValueError(
                f"validated knowledge already registered '{validated_knowledge_id}'"
            )

        if candidate_id in {
            record.candidate_id for record in self._validated_registry.list()
        }:
            raise ValueError(f"already validated '{candidate_id}'")

        record = self._validated_registry.register(
            validated_knowledge_id=validated_knowledge_id,
            candidate_id=candidate_id,
            result_id=candidate.result_id,
            knowledge_type=candidate.knowledge_type,
            description=candidate.description,
            version=candidate.version,
        )

        record.created_at = datetime.utcnow()
        return record
