from dataclasses import FrozenInstanceError, dataclass

import pytest

from quant_platform.research.knowledge.confidence.research_knowledge_confidence_access import (
    ResearchKnowledgeConfidenceAccess,
)
from quant_platform.research.knowledge.confidence.research_knowledge_confidence_registry import (
    ResearchKnowledgeConfidenceRegistry,
)
from quant_platform.research.knowledge.confidence.research_knowledge_confidence_service import (
    ResearchKnowledgeConfidenceService,
)


@dataclass(frozen=True)
class Version:
    knowledge_id: str
    knowledge_version_id: str
    version: str
    status: str = "VALIDATED"


class Versions:
    def __init__(self, *versions: Version) -> None:
        self.versions = {version.knowledge_version_id: version for version in versions}

    def get(self, knowledge_version_id: str) -> Version | None:
        return self.versions.get(knowledge_version_id)


def build_confidence_environment() -> tuple[ResearchKnowledgeConfidenceRegistry, ResearchKnowledgeConfidenceService, ResearchKnowledgeConfidenceAccess]:
    registry = ResearchKnowledgeConfidenceRegistry(
        Versions(Version("K-001", "KV-001", "1"), Version("K-001", "KV-002", "2"), Version("K-002", "KV-101", "1"))
    )
    return registry, ResearchKnowledgeConfidenceService(registry), ResearchKnowledgeConfidenceAccess(registry)


def test_assess_creates_confidence_and_preserves_validated_knowledge() -> None:
    _, service, _ = build_confidence_environment()
    record = service.assess("confidence-001", "KV-001", "high")
    assert record.knowledge_version_id == "KV-001"
    assert record.confidence_level == "HIGH"


def test_assess_unknown_validated_knowledge_raises() -> None:
    _, service, _ = build_confidence_environment()
    with pytest.raises(ValueError, match="unknown knowledge version"):
        service.assess("confidence-001", "KV-missing", "high")


def test_assess_candidate_id_is_not_a_knowledge_version() -> None:
    _, service, _ = build_confidence_environment()
    with pytest.raises(ValueError, match="unknown knowledge version"):
        service.assess("confidence-001", "candidate-001", "high")


@pytest.mark.parametrize("confidence_id,version_id,level", [("", "KV-001", "high"), ("confidence-001", "", "high"), ("confidence-001", "KV-001", "uncertain")])
def test_assess_rejects_empty_or_invalid_inputs(confidence_id: str, version_id: str, level: str) -> None:
    _, service, _ = build_confidence_environment()
    with pytest.raises(ValueError):
        service.assess(confidence_id, version_id, level)


def test_assess_duplicate_confidence_id_raises() -> None:
    _, service, _ = build_confidence_environment()
    service.assess("confidence-001", "KV-001", "high")
    with pytest.raises(ValueError, match="already registered"):
        service.assess("confidence-001", "KV-002", "low")


def test_assess_duplicate_validated_knowledge_raises() -> None:
    _, service, _ = build_confidence_environment()
    service.assess("confidence-001", "KV-001", "high")
    with pytest.raises(ValueError, match="already registered for version"):
        service.assess("confidence-002", "KV-001", "low")


def test_registry_access_and_traceability_preserve_state() -> None:
    _, service, access = build_confidence_environment()
    v1 = service.assess("confidence-001", "KV-001", "high")
    v2 = service.assess("confidence-002", "KV-002", "low")
    other = service.assess("confidence-101", "KV-101", "medium")
    assert access.get("confidence-001") is v1
    assert {item.knowledge_version_id for item in access.list()} == {"KV-001", "KV-002", "KV-101"}
    assert v1.confidence_level == "HIGH" and v2.confidence_level == "LOW"
    assert other.confidence_level == "MEDIUM"
    with pytest.raises(FrozenInstanceError):
        v1.confidence_level = "LOW"  # type: ignore[misc]
