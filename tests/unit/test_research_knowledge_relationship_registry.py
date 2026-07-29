from dataclasses import FrozenInstanceError, dataclass

import pytest

from quant_platform.research.knowledge.relationship.research_knowledge_relationship_access import (
    ResearchKnowledgeRelationshipAccess,
)
from quant_platform.research.knowledge.relationship.research_knowledge_relationship_registry import (
    ResearchKnowledgeRelationshipRegistry,
)


@dataclass(frozen=True)
class Version:
    knowledge_id: str
    knowledge_version_id: str
    version: str


class Versions:
    def __init__(self, *versions: Version) -> None:
        self.items = {version.knowledge_version_id: version for version in versions}

    def get(self, knowledge_version_id: str) -> Version | None:
        return self.items.get(knowledge_version_id)


def build_relationship_environment() -> tuple[ResearchKnowledgeRelationshipRegistry, ResearchKnowledgeRelationshipAccess]:
    registry = ResearchKnowledgeRelationshipRegistry(
        Versions(Version("K-001", "KV-001", "1"), Version("K-001", "KV-002", "2"), Version("K-002", "KV-101", "1"), Version("K-003", "KV-201", "1"))
    )
    return registry, ResearchKnowledgeRelationshipAccess(registry)


def test_register_relationship_creates_record() -> None:
    registry, _ = build_relationship_environment()
    record = registry.register("rel-001", "KV-001", "KV-101", "supports")
    assert record.source_knowledge_version_id == "KV-001"
    assert record.target_knowledge_version_id == "KV-101"
    assert record.relationship_type == "SUPPORTS"


def test_register_relationship_rejects_unknown_knowledge() -> None:
    registry, _ = build_relationship_environment()
    with pytest.raises(ValueError, match="unknown source"):
        registry.register("rel-001", "KV-missing", "KV-101", "supports")
    with pytest.raises(ValueError, match="unknown target"):
        registry.register("rel-002", "KV-001", "KV-missing", "supports")


def test_register_relationship_rejects_self_reference() -> None:
    registry, _ = build_relationship_environment()
    with pytest.raises(ValueError, match="must be different"):
        registry.register("rel-001", "KV-001", "KV-001", "supports")


def test_register_relationship_rejects_duplicates() -> None:
    registry, _ = build_relationship_environment()
    registry.register("rel-001", "KV-001", "KV-101", "supports")
    with pytest.raises(ValueError, match="already registered"):
        registry.register("rel-002", "KV-001", "KV-101", "supports")
    assert registry.register("rel-003", "KV-101", "KV-001", "supports").relationship_type == "SUPPORTS"


def test_get_and_list_relationships() -> None:
    registry, access = build_relationship_environment()
    relationship = registry.register("rel-001", "KV-001", "KV-101", "refines")
    assert access.get("rel-001") is relationship
    assert access.exists("rel-001") is True
    assert access.list() == [relationship]
    with pytest.raises(FrozenInstanceError):
        relationship.relationship_type = "SUPPORTS"  # type: ignore[misc]


def test_list_for_knowledge_returns_associated_relationships() -> None:
    registry, access = build_relationship_environment()
    outgoing = registry.register("rel-out", "KV-001", "KV-101", "supports")
    incoming = registry.register("rel-in", "KV-201", "KV-001", "related_to")
    registry.register("rel-v2", "KV-002", "KV-101", "refines")
    assert set(access.list_for_knowledge_version("KV-001")) == {outgoing, incoming}
    assert access.list_for_knowledge_version("KV-002") == [registry.get("rel-v2")]


def test_register_relationship_does_not_modify_validated_knowledge() -> None:
    registry, access = build_relationship_environment()
    v1 = registry._knowledge_versions.get("KV-001")  # type: ignore[attr-defined]
    registry.register("rel-v1", "KV-001", "KV-101", "supports")
    registry.register("rel-v2", "KV-002", "KV-101", "supports")
    assert registry._knowledge_versions.get("KV-001") is v1  # type: ignore[attr-defined]
    assert access.list_for_knowledge_version("KV-001") != access.list_for_knowledge_version("KV-002")
