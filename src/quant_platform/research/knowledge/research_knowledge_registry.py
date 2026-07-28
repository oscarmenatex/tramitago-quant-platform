from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from quant_platform.research.knowledge.research_knowledge_record import (
    ResearchKnowledgeRecord,
)
from quant_platform.research.result.research_result_registry import (
    ResearchResultRegistry,
)

CREATED = "CREATED"


class ResearchKnowledgeRegistry:
    """Registry for recording research knowledge artifacts derived from results."""

    def __init__(self, result_registry: ResearchResultRegistry) -> None:
        self._result_registry = result_registry
        self._knowledge: Dict[str, ResearchKnowledgeRecord] = {}
        self._result_to_knowledge: Dict[str, str] = {}

    def register(
        self,
        knowledge_id: str,
        result_id: str,
        knowledge_type: str,
        description: str,
        version: str = "v1",
    ) -> ResearchKnowledgeRecord:
        if not knowledge_id:
            raise ValueError("knowledge_id is required")
        if not result_id:
            raise ValueError("result_id is required")
        if not knowledge_type:
            raise ValueError("knowledge_type is required")
        if not description:
            raise ValueError("description is required")

        result = self._result_registry.get(result_id)
        if result is None:
            raise ValueError(f"unknown result '{result_id}'")

        if result_id in self._result_to_knowledge:
            raise ValueError(f"knowledge already registered for result '{result_id}'")

        record = ResearchKnowledgeRecord(
            knowledge_id=knowledge_id,
            result_id=result_id,
            knowledge_type=knowledge_type,
            description=description,
            version=version,
            created_at=datetime.utcnow(),
            status=CREATED,
        )

        self._knowledge[knowledge_id] = record
        self._result_to_knowledge[result_id] = knowledge_id

        return record

    def get(self, knowledge_id: str) -> Optional[ResearchKnowledgeRecord]:
        return self._knowledge.get(knowledge_id)

    def exists(self, knowledge_id: str) -> bool:
        return knowledge_id in self._knowledge

    def exists_for_result(self, result_id: str) -> bool:
        return result_id in self._result_to_knowledge

    def list(self) -> List[ResearchKnowledgeRecord]:
        return list(self._knowledge.values())
