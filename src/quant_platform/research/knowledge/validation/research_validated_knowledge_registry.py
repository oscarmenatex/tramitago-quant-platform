from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from quant_platform.research.knowledge.candidate.research_knowledge_candidate_registry import (
    ResearchKnowledgeCandidateRegistry,
)
from quant_platform.research.knowledge.validation.research_validated_knowledge_record import (
    ResearchValidatedKnowledgeRecord,
)


class ResearchValidatedKnowledgeRegistry:
    """Registry for validated knowledge artifacts."""

    def __init__(self, candidate_registry: ResearchKnowledgeCandidateRegistry) -> None:
        self._candidate_registry = candidate_registry
        self._validated: Dict[str, ResearchValidatedKnowledgeRecord] = {}
        self._candidate_to_validated: Dict[str, str] = {}

    def register(
        self,
        knowledge_id: str,
        knowledge_version_id: str,
        candidate_id: str,
        result_id: str,
        knowledge_type: str,
        description: str,
        version: str = "1",
    ) -> ResearchValidatedKnowledgeRecord:
        if not knowledge_id:
            raise ValueError("knowledge_id is required")
        if not knowledge_version_id:
            raise ValueError("knowledge_version_id is required")
        if not candidate_id:
            raise ValueError("candidate_id is required")
        if not result_id:
            raise ValueError("result_id is required")
        if not knowledge_type:
            raise ValueError("knowledge_type is required")
        if not description:
            raise ValueError("description is required")
        if knowledge_version_id in self._validated:
            raise ValueError(
                f"knowledge version already registered '{knowledge_version_id}'"
            )

        candidate = self._candidate_registry.get(candidate_id)
        if candidate is None:
            raise ValueError(f"unknown candidate '{candidate_id}'")

        if candidate_id in self._candidate_to_validated:
            raise ValueError(f"already validated '{candidate_id}'")

        record = ResearchValidatedKnowledgeRecord(
            knowledge_id=knowledge_id,
            knowledge_version_id=knowledge_version_id,
            candidate_id=candidate_id,
            result_id=result_id,
            knowledge_type=knowledge_type,
            description=description,
            version=version,
            created_at=datetime.utcnow(),
            status="VALIDATED",
        )

        self._validated[knowledge_version_id] = record
        self._candidate_to_validated[candidate_id] = knowledge_version_id
        return record

    def get(
        self, knowledge_version_id: str
    ) -> Optional[ResearchValidatedKnowledgeRecord]:
        return self._validated.get(knowledge_version_id)

    def exists(self, knowledge_version_id: str) -> bool:
        return knowledge_version_id in self._validated

    def list(self) -> List[ResearchValidatedKnowledgeRecord]:
        return list(self._validated.values())
