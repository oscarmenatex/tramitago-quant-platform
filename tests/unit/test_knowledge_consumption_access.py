from dataclasses import FrozenInstanceError, dataclass
from datetime import datetime
from pathlib import Path

import pytest

from quant_platform.research.knowledge.confidence.research_knowledge_confidence_record import (
    ResearchKnowledgeConfidenceRecord,
)
from quant_platform.research.knowledge.consumption import KnowledgeConsumptionAccess
from quant_platform.research.knowledge.relationship.research_knowledge_relationship_record import (
    ResearchKnowledgeRelationshipRecord,
)


@dataclass(frozen=True)
class Version:
    knowledge_id: str
    knowledge_version_id: str
    version: str
    status: str = "VALIDATED"
    candidate_id: str = "candidate"
    result_id: str = "result"
    knowledge_type: str = "Pattern"
    description: str = "Published"
    created_at: datetime | None = None


class Versions:
    def __init__(self, *versions: Version) -> None:
        self.items = {item.knowledge_version_id: item for item in versions}
    def get(self, key: str) -> Version | None: return self.items.get(key)
    def exists(self, key: str) -> bool: return key in self.items
    def list(self) -> list[Version]: return list(self.items.values())


class ConfidenceAccess:
    def __init__(self, *items: ResearchKnowledgeConfidenceRecord) -> None: self.items = items
    def list(self): return list(self.items)


class RelationshipAccess:
    def __init__(self, *items: ResearchKnowledgeRelationshipRecord) -> None: self.items = items
    def list_for_knowledge_version(self, version_id: str):
        return [item for item in self.items if version_id in (item.source_knowledge_version_id, item.target_knowledge_version_id)]


def build_consumption_access() -> KnowledgeConsumptionAccess:
    confidence_v1 = ResearchKnowledgeConfidenceRecord("confidence-1", "KV-001", "HIGH")
    confidence_v2 = ResearchKnowledgeConfidenceRecord("confidence-2", "KV-002", "LOW")
    relationship_v1 = ResearchKnowledgeRelationshipRecord("relationship-1", "KV-001", "KV-101", "SUPPORTS")
    relationship_v2 = ResearchKnowledgeRelationshipRecord("relationship-2", "KV-002", "KV-101", "REFINES")
    return KnowledgeConsumptionAccess(
        Versions(Version("K-001", "KV-001", "1"), Version("K-001", "KV-002", "2"), Version("K-002", "KV-101", "1")),
        ConfidenceAccess(confidence_v1, confidence_v2),
        RelationshipAccess(relationship_v1, relationship_v2),
    )


def test_get_publishes_only_the_public_knowledge_model() -> None:
    knowledge = build_consumption_access().get("KV-001")
    assert (knowledge.knowledge_id, knowledge.knowledge_version_id, knowledge.version) == ("K-001", "KV-001", "1")
    assert knowledge.confidence_reference == "confidence-1"
    assert knowledge.relationship_references == ("relationship-1",)
    assert not hasattr(knowledge, "candidate_id")


def test_existence_and_list_include_only_validated_knowledge() -> None:
    consumption = build_consumption_access()
    assert consumption.exists("KV-001") is True and consumption.exists("missing") is False
    assert {(item.knowledge_id, item.knowledge_version_id) for item in consumption.list()} == {("K-001", "KV-001"), ("K-001", "KV-002"), ("K-002", "KV-101")}


def test_get_rejects_unknown_or_candidate_knowledge() -> None:
    consumption = build_consumption_access()
    for key in ("", "missing"):
        with pytest.raises(ValueError):
            consumption.get(key)
    blocked = KnowledgeConsumptionAccess(Versions(Version("K-003", "KV-301", "1", "CREATED")), ConfidenceAccess(), RelationshipAccess())
    with pytest.raises(ValueError, match="not consumable"):
        blocked.get("KV-301")


def test_confidence_and_relationships_are_retrieved_without_mutation() -> None:
    consumption = build_consumption_access()
    assert consumption.get_confidence("KV-001").confidence_reference == "confidence-1"
    assert consumption.get_confidence("KV-002").confidence_reference == "confidence-2"
    assert [item.relationship_reference for item in consumption.get_relationships("KV-001")] == ["relationship-1"]
    assert [item.relationship_reference for item in consumption.get_relationships("KV-002")] == ["relationship-2"]


def test_consumption_results_are_immutable_public_views() -> None:
    knowledge = build_consumption_access().get("KV-001")
    with pytest.raises(FrozenInstanceError):
        knowledge.description = "changed"  # type: ignore[misc]


def test_associated_queries_reject_unknown_knowledge() -> None:
    consumption = build_consumption_access()
    with pytest.raises(ValueError):
        consumption.get_confidence("missing")
    with pytest.raises(ValueError):
        consumption.get_relationships("missing")


def test_consumption_boundary_does_not_import_lifecycle_internals() -> None:
    source = Path("src/quant_platform/research/knowledge/consumption/knowledge_consumption_access.py").read_text(encoding="utf-8")
    assert "strategy_evaluation" not in source
    assert "validated" + "_knowledge_id" not in source
