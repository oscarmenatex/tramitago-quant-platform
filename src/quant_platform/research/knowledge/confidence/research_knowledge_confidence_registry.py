from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from quant_platform.research.knowledge.confidence.research_knowledge_confidence_record import (
    ResearchKnowledgeConfidenceRecord,
)
from quant_platform.research.knowledge.version.knowledge_version import (
    KnowledgeVersionSource,
)

VALID_LEVELS = {"LOW", "MEDIUM", "HIGH"}


class ResearchKnowledgeConfidenceRegistry:
    """Registry for knowledge-confidence assessments."""

    def __init__(self, knowledge_versions: KnowledgeVersionSource) -> None:
        self._knowledge_versions = knowledge_versions
        self._confidence: Dict[str, ResearchKnowledgeConfidenceRecord] = {}
        self._version_to_confidence: Dict[str, str] = {}

    def register(
        self,
        knowledge_confidence_id: str,
        knowledge_version_id: str,
        confidence_level: str,
        version: str = "1",
    ) -> ResearchKnowledgeConfidenceRecord:
        if not knowledge_confidence_id:
            raise ValueError("knowledge_confidence_id is required")
        if not knowledge_version_id:
            raise ValueError("knowledge_version_id is required")
        if not confidence_level:
            raise ValueError("confidence_level is required")
        if confidence_level.upper() not in VALID_LEVELS:
            raise ValueError("confidence_level must be LOW, MEDIUM, or HIGH")

        if knowledge_confidence_id in self._confidence:
            raise ValueError(
                f"knowledge confidence already registered '{knowledge_confidence_id}'"
            )

        knowledge_version = self._knowledge_versions.get(knowledge_version_id)
        if knowledge_version is None:
            raise ValueError(f"unknown knowledge version '{knowledge_version_id}'")
        if knowledge_version.status != "VALIDATED":
            raise ValueError(
                f"knowledge version '{knowledge_version_id}' is not consumable"
            )

        if knowledge_version_id in self._version_to_confidence:
            raise ValueError(
                f"knowledge confidence already registered for version '{knowledge_version_id}'"
            )

        record = ResearchKnowledgeConfidenceRecord(
            knowledge_confidence_id=knowledge_confidence_id,
            knowledge_version_id=knowledge_version_id,
            confidence_level=confidence_level.upper(),
            version=version,
            created_at=datetime.utcnow(),
            status="ASSESSED",
        )

        self._confidence[knowledge_confidence_id] = record
        self._version_to_confidence[knowledge_version_id] = knowledge_confidence_id
        return record

    def get(
        self, knowledge_confidence_id: str
    ) -> Optional[ResearchKnowledgeConfidenceRecord]:
        return self._confidence.get(knowledge_confidence_id)

    def exists(self, knowledge_confidence_id: str) -> bool:
        return knowledge_confidence_id in self._confidence

    def list(self) -> List[ResearchKnowledgeConfidenceRecord]:
        return list(self._confidence.values())
