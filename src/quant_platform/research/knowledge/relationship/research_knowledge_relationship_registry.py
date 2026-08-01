from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from quant_platform.research.knowledge.relationship.research_knowledge_relationship_record import (
    ResearchKnowledgeRelationshipRecord,
)
from quant_platform.research.knowledge.version.knowledge_version import (
    KnowledgeVersionSource,
)

VALID_RELATIONSHIP_TYPES = {"SUPPORTS", "REFINES", "SPECIALIZES", "RELATED_TO"}


class ResearchKnowledgeRelationshipRegistry:
    """Registry for relationships between exact knowledge versions."""

    def __init__(self, knowledge_versions: KnowledgeVersionSource) -> None:
        self._knowledge_versions = knowledge_versions
        self._relationships: Dict[str, ResearchKnowledgeRelationshipRecord] = {}
        self._version_to_relationships: Dict[str, List[str]] = {}
        self._relationship_keys: set[tuple[str, str, str]] = set()

    def register(
        self,
        knowledge_relationship_id: str,
        source_knowledge_version_id: str,
        target_knowledge_version_id: str,
        relationship_type: str,
        version: str = "1",
    ) -> ResearchKnowledgeRelationshipRecord:
        if not knowledge_relationship_id:
            raise ValueError("knowledge_relationship_id is required")
        if not source_knowledge_version_id:
            raise ValueError("source_knowledge_version_id is required")
        if not target_knowledge_version_id:
            raise ValueError("target_knowledge_version_id is required")
        if source_knowledge_version_id == target_knowledge_version_id:
            raise ValueError("source and target knowledge versions must be different")
        if relationship_type.upper() not in VALID_RELATIONSHIP_TYPES:
            raise ValueError("invalid relationship_type")
        if knowledge_relationship_id in self._relationships:
            raise ValueError("knowledge relationship already registered")
        if self._knowledge_versions.get(source_knowledge_version_id) is None:
            raise ValueError("unknown source knowledge version")
        if self._knowledge_versions.get(target_knowledge_version_id) is None:
            raise ValueError("unknown target knowledge version")
        key = (
            source_knowledge_version_id,
            target_knowledge_version_id,
            relationship_type.upper(),
        )
        if key in self._relationship_keys:
            raise ValueError("knowledge relationship already registered for versions")
        record = ResearchKnowledgeRelationshipRecord(
            knowledge_relationship_id,
            source_knowledge_version_id,
            target_knowledge_version_id,
            relationship_type.upper(),
            version,
            datetime.utcnow(),
        )
        self._relationships[knowledge_relationship_id] = record
        self._relationship_keys.add(key)
        for version_id in (source_knowledge_version_id, target_knowledge_version_id):
            self._version_to_relationships.setdefault(version_id, []).append(
                knowledge_relationship_id
            )
        return record

    def get(
        self, knowledge_relationship_id: str
    ) -> Optional[ResearchKnowledgeRelationshipRecord]:
        return self._relationships.get(knowledge_relationship_id)

    def exists(self, knowledge_relationship_id: str) -> bool:
        return knowledge_relationship_id in self._relationships

    def list(self) -> List[ResearchKnowledgeRelationshipRecord]:
        return list(self._relationships.values())

    def list_for_knowledge_version(
        self, knowledge_version_id: str
    ) -> List[ResearchKnowledgeRelationshipRecord]:
        return [
            self._relationships[relationship_id]
            for relationship_id in self._version_to_relationships.get(
                knowledge_version_id, []
            )
        ]
