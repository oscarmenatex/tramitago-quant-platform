from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from quant_platform.research.knowledge.candidate.research_knowledge_candidate_record import (
    ResearchKnowledgeCandidateRecord,
)
from quant_platform.research.result.research_result_registry import (
    ResearchResultRegistry,
)

CANDIDATE = "CANDIDATE"


class ResearchKnowledgeCandidateRegistry:
    """Registry for knowledge candidates derived from research results.

    This MVP preserves the conceptual boundary between a Knowledge Candidate and
    a Knowledge artifact by managing only candidate records and keeping the
    dependency surface limited to the result registry.
    """

    def __init__(self, result_registry: ResearchResultRegistry) -> None:
        self._result_registry = result_registry
        self._candidates: Dict[str, ResearchKnowledgeCandidateRecord] = {}
        self._result_to_candidate: Dict[str, str] = {}

    def register(
        self,
        knowledge_candidate_id: str,
        result_id: str,
        knowledge_type: str,
        description: str,
        version: str = "1",
    ) -> ResearchKnowledgeCandidateRecord:
        if not knowledge_candidate_id:
            raise ValueError("knowledge_candidate_id is required")
        if not result_id:
            raise ValueError("result_id is required")
        if not knowledge_type:
            raise ValueError("knowledge_type is required")
        if not description:
            raise ValueError("description is required")

        if knowledge_candidate_id in self._candidates:
            raise ValueError(
                f"knowledge candidate already registered '{knowledge_candidate_id}'"
            )

        result = self._result_registry.get(result_id)
        if result is None:
            raise ValueError(f"unknown result '{result_id}'")

        if result_id in self._result_to_candidate:
            raise ValueError(
                f"knowledge candidate already registered for result '{result_id}'"
            )

        record = ResearchKnowledgeCandidateRecord(
            knowledge_candidate_id=knowledge_candidate_id,
            result_id=result_id,
            knowledge_type=knowledge_type,
            description=description,
            version=version,
            created_at=datetime.utcnow(),
            status=CANDIDATE,
        )

        self._candidates[knowledge_candidate_id] = record
        self._result_to_candidate[result_id] = knowledge_candidate_id
        return record

    def get(
        self, knowledge_candidate_id: str
    ) -> Optional[ResearchKnowledgeCandidateRecord]:
        return self._candidates.get(knowledge_candidate_id)

    def exists(self, knowledge_candidate_id: str) -> bool:
        return knowledge_candidate_id in self._candidates

    def list(self) -> List[ResearchKnowledgeCandidateRecord]:
        return list(self._candidates.values())
