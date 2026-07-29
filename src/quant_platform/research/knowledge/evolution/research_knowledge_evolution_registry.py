from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Protocol

from quant_platform.research.knowledge.evolution.research_knowledge_evolution_record import (
    ResearchKnowledgeEvolutionRecord,
)
from quant_platform.research.knowledge.validation.research_validated_knowledge_registry import (
    ResearchValidatedKnowledgeRegistry,
)
from quant_platform.research.result.research_result_registry import (
    ResearchResultRegistry,
)

VALIDATED = "VALIDATED"


class _KnowledgeVersion(Protocol):
    candidate_id: str
    result_id: str
    knowledge_type: str
    description: str
    version: str
    status: str


class ResearchKnowledgeEvolutionRegistry:
    """Append-only registry for the linear evolution of validated knowledge."""

    def __init__(
        self,
        validated_registry: ResearchValidatedKnowledgeRegistry,
        result_registry: ResearchResultRegistry,
    ) -> None:
        self._validated_registry = validated_registry
        self._result_registry = result_registry
        self._versions: Dict[str, ResearchKnowledgeEvolutionRecord] = {}
        self._successor_by_version_id: Dict[str, str] = {}

    def register(
        self,
        knowledge_version_id: str,
        previous_knowledge_version_id: str,
        evidence_result_id: str,
        description: str,
    ) -> ResearchKnowledgeEvolutionRecord:
        if not knowledge_version_id:
            raise ValueError("knowledge_version_id is required")
        if not previous_knowledge_version_id:
            raise ValueError("previous_knowledge_version_id is required")
        if not evidence_result_id:
            raise ValueError("evidence_result_id is required")
        if not description:
            raise ValueError("description is required")

        if self.exists(knowledge_version_id):
            raise ValueError(f"knowledge version already registered '{knowledge_version_id}'")

        previous = self.get(previous_knowledge_version_id)
        if previous is None:
            raise ValueError(
                f"unknown knowledge version '{previous_knowledge_version_id}'"
            )
        if previous.status != VALIDATED:
            raise ValueError(
                f"knowledge version '{previous_knowledge_version_id}' is not in VALIDATED state"
            )
        if previous_knowledge_version_id in self._successor_by_version_id:
            raise ValueError(
                f"knowledge version '{previous_knowledge_version_id}' already has an evolved version"
            )
        if self._result_registry.get(evidence_result_id) is None:
            raise ValueError(f"unknown evidence result '{evidence_result_id}'")

        record = ResearchKnowledgeEvolutionRecord(
            knowledge_version_id=knowledge_version_id,
            knowledge_id=previous.knowledge_id,
            previous_knowledge_version_id=previous_knowledge_version_id,
            candidate_id=previous.candidate_id,
            result_id=previous.result_id,
            evidence_result_id=evidence_result_id,
            knowledge_type=previous.knowledge_type,
            description=description,
            version=self._next_version(previous.version),
            created_at=datetime.utcnow(),
        )
        if any(
            version.knowledge_id == record.knowledge_id
            and version.version == record.version
            for version in self.list()
        ):
            raise ValueError("knowledge_id and version must be unique")
        self._versions[knowledge_version_id] = record
        self._successor_by_version_id[previous_knowledge_version_id] = knowledge_version_id
        return record

    def get(self, knowledge_version_id: str) -> Optional[_KnowledgeVersion]:
        evolved = self._versions.get(knowledge_version_id)
        if evolved is not None:
            return evolved
        return self._validated_registry.get(knowledge_version_id)

    def exists(self, knowledge_version_id: str) -> bool:
        return knowledge_version_id in self._versions or self._validated_registry.exists(
            knowledge_version_id
        )

    def list(self) -> List[ResearchKnowledgeEvolutionRecord]:
        return list(self._versions.values())

    def get_predecessor(self, knowledge_version_id: str) -> Optional[_KnowledgeVersion]:
        version = self._versions.get(knowledge_version_id)
        if version is None:
            return None
        return self.get(version.previous_knowledge_version_id)

    @staticmethod
    def _next_version(previous_version: str) -> str:
        try:
            return str(int(previous_version) + 1)
        except ValueError as exc:
            raise ValueError("previous knowledge version must be numeric") from exc
