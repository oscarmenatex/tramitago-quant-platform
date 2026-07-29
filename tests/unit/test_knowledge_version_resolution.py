from dataclasses import FrozenInstanceError, dataclass

import pytest

from quant_platform.research.knowledge.confidence.research_knowledge_confidence_record import (
    ResearchKnowledgeConfidenceRecord,
)
from quant_platform.research.knowledge.consumption import (
    KnowledgeConsumptionAccess,
    KnowledgeLineageNotFoundError,
    KnowledgeVersionNotConsumableError,
    KnowledgeVersionNotFoundError,
)
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
    created_at: object | None = None


class Versions:
    def __init__(self, *items: Version) -> None: self.items = {item.knowledge_version_id: item for item in items}
    def get(self, key: str): return self.items.get(key)
    def exists(self, key: str) -> bool: return key in self.items
    def list(self): return list(self.items.values())


class Confidence:
    def __init__(self, *items): self.items = items
    def list(self): return list(self.items)


class Relationships:
    def __init__(self, *items): self.items = items
    def list_for_knowledge_version(self, key: str): return [item for item in self.items if key in (item.source_knowledge_version_id, item.target_knowledge_version_id)]


def access(status_v2: str = "VALIDATED") -> KnowledgeConsumptionAccess:
    return KnowledgeConsumptionAccess(
        Versions(Version("K-001", "KV-001", "1"), Version("K-001", "KV-002", "2", status_v2), Version("K-002", "KV-101", "1")),
        Confidence(ResearchKnowledgeConfidenceRecord("confidence-1", "KV-001", "HIGH"), ResearchKnowledgeConfidenceRecord("confidence-2", "KV-002", "LOW")),
        Relationships(ResearchKnowledgeRelationshipRecord("relationship-1", "KV-001", "KV-101", "SUPPORTS"), ResearchKnowledgeRelationshipRecord("relationship-2", "KV-002", "KV-101", "REFINES")),
    )


def test_resolve_returns_exact_versions_and_is_deterministic() -> None:
    consumption = access()
    v1 = consumption.resolve(" K-001 ", " 1 ")
    v2 = consumption.resolve("K-001", "2")
    assert (v1.knowledge_version_id, v2.knowledge_version_id) == ("KV-001", "KV-002")
    assert consumption.resolve("K-001", "1") == v1


def test_resolve_isolated_confidence_relationships_and_lineages() -> None:
    consumption = access()
    v1, v2, other = consumption.resolve("K-001", "1"), consumption.resolve("K-001", "2"), consumption.resolve("K-002", "1")
    assert (v1.confidence_reference, v2.confidence_reference) == ("confidence-1", "confidence-2")
    assert (v1.relationship_references, v2.relationship_references) == (("relationship-1",), ("relationship-2",))
    assert other.knowledge_version_id == "KV-101"


def test_resolve_rejects_missing_lineage_version_and_nonconsumable_version() -> None:
    with pytest.raises(KnowledgeLineageNotFoundError):
        access().resolve("missing", "1")
    with pytest.raises(KnowledgeVersionNotFoundError):
        access().resolve("K-001", "99")
    with pytest.raises(KnowledgeVersionNotConsumableError):
        access("CREATED").resolve("K-001", "2")


def test_resolved_record_is_immutable_and_public() -> None:
    record = access().resolve("K-001", "1")
    with pytest.raises(FrozenInstanceError):
        record.description = "changed"  # type: ignore[misc]
    assert not hasattr(record, "candidate_id") and not hasattr(record, "registry")
