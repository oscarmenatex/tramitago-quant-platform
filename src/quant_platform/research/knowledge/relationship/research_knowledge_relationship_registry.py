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
    """Registry for explicit relationships between validated knowledge artifacts."""

    def __init__(self, knowledge_versions: KnowledgeVersionSource) -> None:
        self._knowledge_versions = knowledge_versions
        self._relationships: Dict[str, ResearchKnowledgeRelationshipRecord] = {}
        self._knowledge_to_relationships: Dict[str, List[str]] = {}
        self._relationship_keys: set[tuple[str, str, str]] = set()

    def register(
        self,
        knowledge_relationship_id: str,
        source_knowledge_id: str,
        target_knowledge_id: str,
        relationship_type: str,
        version: str = "1",
    ) -> ResearchKnowledgeRelationshipRecord:
        if not knowledge_relationship_id:
            raise ValueError("knowledge_relationship_id is required")
        if not source_knowledge_id:
            raise ValueError("source_knowledge_id is required")
        if not target_knowledge_id:
            raise ValueError("target_knowledge_id is required")
        if not relationship_type:
            raise ValueError("relationship_type is required")

        if source_knowledge_id == target_knowledge_id:
            raise ValueError("source and target knowledge must be different")

        if relationship_type.upper() not in VALID_RELATIONSHIP_TYPES:
            raise ValueError(
                "relationship_type must be SUPPORTS, REFINES, SPECIALIZES, or RELATED_TO"
            )

        if knowledge_relationship_id in self._relationships:
            raise ValueError(
                f"knowledge relationship already registered '{knowledge_relationship_id}'"
            )

        source = self._knowledge_versions.get(source_knowledge_id)
        if source is None:
            raise ValueError(f"unknown source knowledge '{source_knowledge_id}'")

        target = self._knowledge_versions.get(target_knowledge_id)
        if target is None:
            raise ValueError(f"unknown target knowledge '{target_knowledge_id}'")

        key = (source_knowledge_id, target_knowledge_id, relationship_type.upper())
        if key in self._relationship_keys:
            raise ValueError(
                f"knowledge relationship already registered for '{source_knowledge_id}' -> '{target_knowledge_id}'"
            )

        record = ResearchKnowledgeRelationshipRecord(
            knowledge_relationship_id=knowledge_relationship_id,
            source_knowledge_id=source_knowledge_id,
            target_knowledge_id=target_knowledge_id,
            relationship_type=relationship_type.upper(),
            version=version,
            created_at=datetime.utcnow(),
        )

        self._relationships[knowledge_relationship_id] = record
        self._relationship_keys.add(key)
        self._knowledge_to_relationships.setdefault(source_knowledge_id, []).append(
            knowledge_relationship_id
        )
        self._knowledge_to_relationships.setdefault(target_knowledge_id, []).append(
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

    def list_for_knowledge(
        self, knowledge_id: str
    ) -> List[ResearchKnowledgeRelationshipRecord]:
        relationship_ids = self._knowledge_to_relationships.get(knowledge_id, [])
        return [
            self._relationships[relationship_id] for relationship_id in relationship_ids
        ]
