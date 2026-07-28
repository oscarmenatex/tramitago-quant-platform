from __future__ import annotations

from typing import List, Optional

from quant_platform.research.knowledge.confidence.research_knowledge_confidence_access import (
    ResearchKnowledgeConfidenceAccess,
)
from quant_platform.research.knowledge.consumption.knowledge_consumption_record import (
    KnowledgeConfidenceConsumptionRecord,
    KnowledgeConsumptionRecord,
    KnowledgeRelationshipConsumptionRecord,
)
from quant_platform.research.knowledge.relationship.research_knowledge_relationship_access import (
    ResearchKnowledgeRelationshipAccess,
)
from quant_platform.research.knowledge.version.knowledge_version import (
    KnowledgeVersion,
    KnowledgeVersionSource,
)


class KnowledgeConsumptionAccess:
    """Public read-only boundary for reusable, validated knowledge.

    The boundary depends exclusively on read access adapters and returns an
    immutable projection, never lifecycle artifacts such as candidates.
    """

    def __init__(
        self,
        knowledge_versions: KnowledgeVersionSource,
        confidence_access: ResearchKnowledgeConfidenceAccess,
        relationship_access: ResearchKnowledgeRelationshipAccess,
    ) -> None:
        self._knowledge_versions = knowledge_versions
        self._confidence_access = confidence_access
        self._relationship_access = relationship_access

    def get(self, knowledge_id: str) -> KnowledgeConsumptionRecord:
        knowledge_version = self._get_knowledge_version(knowledge_id)
        return self._to_public_record(knowledge_version)

    def exists(self, knowledge_id: str) -> bool:
        return bool(knowledge_id) and self._knowledge_versions.exists(knowledge_id)

    def list(self) -> List[KnowledgeConsumptionRecord]:
        return [
            self._to_public_record(knowledge_version)
            for knowledge_version in self._knowledge_versions.list()
        ]

    def get_confidence(
        self, knowledge_id: str
    ) -> Optional[KnowledgeConfidenceConsumptionRecord]:
        self._get_knowledge_version(knowledge_id)
        confidence = next(
            (
                confidence
                for confidence in self._confidence_access.list()
                if confidence.validated_knowledge_id == knowledge_id
            ),
            None,
        )
        if confidence is None:
            return None
        return KnowledgeConfidenceConsumptionRecord(
            confidence_reference=confidence.knowledge_confidence_id,
            confidence_level=confidence.confidence_level,
            status=confidence.status,
            version=confidence.version,
            created_at=confidence.created_at,
        )

    def get_relationships(
        self, knowledge_id: str
    ) -> List[KnowledgeRelationshipConsumptionRecord]:
        self._get_knowledge_version(knowledge_id)
        return [
            KnowledgeRelationshipConsumptionRecord(
                relationship_reference=relationship.knowledge_relationship_id,
                source_knowledge_id=relationship.source_knowledge_id,
                target_knowledge_id=relationship.target_knowledge_id,
                relationship_type=relationship.relationship_type,
                version=relationship.version,
                created_at=relationship.created_at,
            )
            for relationship in self._relationship_access.list_for_knowledge(
                knowledge_id
            )
        ]

    def _get_knowledge_version(self, knowledge_id: str) -> KnowledgeVersion:
        if not knowledge_id:
            raise ValueError("knowledge_id is required")
        knowledge_version = self._knowledge_versions.get(knowledge_id)
        if knowledge_version is None:
            raise ValueError(f"unknown reusable knowledge '{knowledge_id}'")
        return knowledge_version

    def _to_public_record(
        self, knowledge_version: KnowledgeVersion
    ) -> KnowledgeConsumptionRecord:
        confidence = self.get_confidence(knowledge_version.knowledge_id)
        relationships = self.get_relationships(knowledge_version.knowledge_id)
        return KnowledgeConsumptionRecord(
            knowledge_id=knowledge_version.knowledge_id,
            knowledge_type=knowledge_version.knowledge_type,
            description=knowledge_version.description,
            status=knowledge_version.status,
            confidence_reference=(
                confidence.confidence_reference if confidence is not None else None
            ),
            relationship_references=tuple(
                relationship.relationship_reference for relationship in relationships
            ),
            source_reference=knowledge_version.result_id,
            version=knowledge_version.version,
            created_at=knowledge_version.created_at,
        )
