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
from quant_platform.research.knowledge.consumption.knowledge_resolution_errors import (
    AmbiguousKnowledgeVersionError,
    InvalidKnowledgeIdentifierError,
    InvalidKnowledgeVersionError,
    KnowledgeLineageNotFoundError,
    KnowledgeVersionNotConsumableError,
    KnowledgeVersionNotFoundError,
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

    def resolve(
        self, knowledge_id: str, knowledge_version: str
    ) -> KnowledgeConsumptionRecord:
        """Resolve one exact published version without selecting a current version."""
        lineage_id = self._normalize_lineage_id(knowledge_id)
        version_label = self._normalize_version(knowledge_version)
        lineage_versions = [
            version
            for version in self._knowledge_versions.list()
            if version.knowledge_id == lineage_id
        ]
        if not lineage_versions:
            raise KnowledgeLineageNotFoundError(
                f"unknown Knowledge lineage '{lineage_id}'"
            )
        matches = [
            version for version in lineage_versions if version.version == version_label
        ]
        if not matches:
            raise KnowledgeVersionNotFoundError(
                f"unknown version '{version_label}' for Knowledge '{lineage_id}'"
            )
        if len(matches) > 1:
            raise AmbiguousKnowledgeVersionError(
                f"ambiguous version '{version_label}' for Knowledge '{lineage_id}'"
            )
        resolved = matches[0]
        if resolved.status != "VALIDATED":
            raise KnowledgeVersionNotConsumableError(
                f"Knowledge version '{resolved.knowledge_version_id}' is not consumable"
            )
        record = self._to_public_record(resolved)
        if record.knowledge_id != lineage_id or record.version != version_label:
            raise AmbiguousKnowledgeVersionError("resolved public record is inconsistent")
        return record

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
                if confidence.knowledge_version_id == knowledge_id
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
                source_knowledge_version_id=(
                    relationship.source_knowledge_version_id
                ),
                target_knowledge_version_id=(
                    relationship.target_knowledge_version_id
                ),
                relationship_type=relationship.relationship_type,
                version=relationship.version,
                created_at=relationship.created_at,
            )
            for relationship in self._relationship_access.list_for_knowledge_version(
                knowledge_id
            )
        ]

    def _get_knowledge_version(self, knowledge_id: str) -> KnowledgeVersion:
        if not knowledge_id:
            raise ValueError("knowledge_id is required")
        knowledge_version = self._knowledge_versions.get(knowledge_id)
        if knowledge_version is None:
            raise ValueError(f"unknown reusable knowledge '{knowledge_id}'")
        if knowledge_version.status != "VALIDATED":
            raise ValueError(f"knowledge version '{knowledge_id}' is not consumable")
        return knowledge_version

    @staticmethod
    def _normalize_lineage_id(value: object) -> str:
        if not isinstance(value, str) or not (normalized := value.strip()):
            raise InvalidKnowledgeIdentifierError("knowledge_id is required")
        return normalized

    @staticmethod
    def _normalize_version(value: object) -> str:
        if not isinstance(value, str) or not (normalized := value.strip()):
            raise InvalidKnowledgeVersionError("knowledge_version is required")
        return normalized

    def _to_public_record(
        self, knowledge_version: KnowledgeVersion
    ) -> KnowledgeConsumptionRecord:
        confidence = self.get_confidence(knowledge_version.knowledge_version_id)
        relationships = self.get_relationships(knowledge_version.knowledge_version_id)
        return KnowledgeConsumptionRecord(
            knowledge_id=knowledge_version.knowledge_id,
            knowledge_version_id=knowledge_version.knowledge_version_id,
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
