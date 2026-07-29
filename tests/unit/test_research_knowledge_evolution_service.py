from dataclasses import dataclass
from datetime import datetime

import pytest

from quant_platform.research.knowledge.evolution.research_knowledge_evolution_registry import (
    ResearchKnowledgeEvolutionRegistry,
)
from quant_platform.research.knowledge.evolution.research_knowledge_evolution_service import (
    ResearchKnowledgeEvolutionService,
)


@dataclass(frozen=True)
class Version:
    knowledge_id: str
    knowledge_version_id: str
    version: str
    candidate_id: str = "candidate-001"
    result_id: str = "result-001"
    knowledge_type: str = "Pattern"
    description: str = "Original"
    status: str = "VALIDATED"
    created_at: datetime | None = None


class Versions:
    def __init__(self, versions: list[Version]) -> None:
        self._versions = {version.knowledge_version_id: version for version in versions}

    def get(self, knowledge_version_id: str) -> Version | None:
        return self._versions.get(knowledge_version_id)

    def exists(self, knowledge_version_id: str) -> bool:
        return knowledge_version_id in self._versions

    def list(self) -> list[Version]:
        return list(self._versions.values())


class Results:
    def get(self, result_id: str) -> object | None:
        return object() if result_id.startswith("result-") else None


def build_service(*versions: Version) -> tuple[ResearchKnowledgeEvolutionRegistry, ResearchKnowledgeEvolutionService]:
    registry = ResearchKnowledgeEvolutionRegistry(Versions(list(versions)), Results())
    return registry, ResearchKnowledgeEvolutionService(registry)


def test_evolve_creates_an_immutable_linear_version_with_full_traceability() -> None:
    v1 = Version("K-001", "KV-001", "1")
    registry, service = build_service(v1)

    v2 = service.evolve("KV-002", "KV-001", "result-002", "Updated")

    assert v2.knowledge_id == "K-001"
    assert v2.knowledge_version_id == "KV-002"
    assert v2.version == "2"
    assert v2.previous_knowledge_version_id == "KV-001"
    assert registry.get("KV-001") is v1
    assert v1.description == "Original"


def test_evolve_rejects_unknown_or_invalid_predecessor_and_unknown_evidence() -> None:
    registry, service = build_service(Version("K-001", "KV-001", "1"))
    with pytest.raises(ValueError, match="unknown knowledge version"):
        service.evolve("KV-002", "KV-missing", "result-002", "Updated")
    invalid = Version("K-002", "KV-invalid", "1", status="CREATED")
    _, invalid_service = build_service(invalid)
    with pytest.raises(ValueError, match="not in VALIDATED"):
        invalid_service.evolve("KV-invalid-2", "KV-invalid", "result-002", "Updated")
    with pytest.raises(ValueError, match="unknown evidence result"):
        service.evolve("KV-002", "KV-001", "missing", "Updated")
    assert registry.list() == []


def test_evolve_rejects_multiple_successors_and_identifier_cycles() -> None:
    _, service = build_service(Version("K-001", "KV-001", "1"))
    service.evolve("KV-002", "KV-001", "result-002", "Updated")
    with pytest.raises(ValueError, match="already has an evolved version"):
        service.evolve("KV-branch", "KV-001", "result-003", "Branch")
    with pytest.raises(ValueError, match="already registered"):
        service.evolve("KV-001", "KV-002", "result-003", "Cycle")


def test_versions_are_compatible_with_distinct_lineages_and_unique_pairs() -> None:
    _, first = build_service(Version("K-001", "KV-001", "1"))
    _, second = build_service(Version("K-002", "KV-101", "1"))
    assert first.evolve("KV-002", "KV-001", "result-002", "Updated").version == "2"
    assert second.evolve("KV-102", "KV-101", "result-002", "Updated").version == "2"
    registry, service = build_service(Version("K-001", "KV-001", "1"))
    service.evolve("KV-002", "KV-001", "result-002", "Updated")
    registry._versions["KV-duplicate"] = Version("K-001", "KV-duplicate", "3")  # type: ignore[assignment]
    with pytest.raises(ValueError, match="knowledge_id and version must be unique"):
        service.evolve("KV-003", "KV-002", "result-003", "Duplicate")


def test_evolution_chain_keeps_one_lineage_and_unique_version_ids() -> None:
    registry, service = build_service(Version("K-001", "KV-001", "1"))
    v2 = service.evolve("KV-002", "KV-001", "result-002", "V2")
    v3 = service.evolve("KV-003", "KV-002", "result-003", "V3")
    assert {v2.knowledge_id, v3.knowledge_id} == {"K-001"}
    assert {"KV-001", v2.knowledge_version_id, v3.knowledge_version_id} == {
        "KV-001", "KV-002", "KV-003"
    }
    assert v3.previous_knowledge_version_id == v2.knowledge_version_id
    assert registry.get_predecessor("KV-003") is v2


def test_evolution_record_has_only_the_corrected_contractual_data_fields() -> None:
    from quant_platform.research.knowledge.evolution.research_knowledge_evolution_record import (
        ResearchKnowledgeEvolutionRecord,
    )

    assert tuple(ResearchKnowledgeEvolutionRecord.__dataclass_fields__) == (
        "knowledge_version_id", "knowledge_id", "previous_knowledge_version_id",
        "candidate_id", "result_id", "evidence_result_id", "knowledge_type",
        "description", "version", "created_at", "status",
    )
