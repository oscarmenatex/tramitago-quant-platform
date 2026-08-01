from dataclasses import dataclass

from quant_platform.research.knowledge.confidence.research_knowledge_confidence_access import (
    ResearchKnowledgeConfidenceAccess,
)
from quant_platform.research.knowledge.confidence.research_knowledge_confidence_registry import (
    ResearchKnowledgeConfidenceRegistry,
)
from quant_platform.research.knowledge.consumption import KnowledgeConsumptionAccess
from quant_platform.research.knowledge.evolution.research_knowledge_evolution_registry import (
    ResearchKnowledgeEvolutionRegistry,
)
from quant_platform.research.knowledge.evolution.research_knowledge_evolution_service import (
    ResearchKnowledgeEvolutionService,
)
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
    candidate_id: str = "candidate-001"
    result_id: str = "result-001"
    knowledge_type: str = "Pattern"
    description: str = "V1"
    status: str = "VALIDATED"
    created_at: object | None = None


class BaseVersions:
    def __init__(self, *versions: Version) -> None:
        self._items = {item.knowledge_version_id: item for item in versions}

    def get(self, key: str): return self._items.get(key)
    def exists(self, key: str) -> bool: return key in self._items
    def list(self): return list(self._items.values())


class Results:
    def get(self, key: str): return object() if key.startswith("result-") else None


class AllVersions:
    def __init__(self, base: BaseVersions, evolution: ResearchKnowledgeEvolutionRegistry) -> None:
        self.base, self.evolution = base, evolution
    def get(self, key: str): return self.evolution.get(key)
    def exists(self, key: str) -> bool: return self.get(key) is not None
    def list(self): return self.base.list() + self.evolution.list()


def test_identity_contract_holds_across_the_knowledge_lifecycle() -> None:
    base = BaseVersions(Version("K-001", "KV-001", "1"), Version("K-002", "KV-101", "1"))
    evolution = ResearchKnowledgeEvolutionRegistry(base, Results())
    service = ResearchKnowledgeEvolutionService(evolution)
    v2 = service.evolve("KV-002", "KV-001", "result-002", "V2")
    v3 = service.evolve("KV-003", "KV-002", "result-003", "V3")
    versions = AllVersions(base, evolution)
    confidence = ResearchKnowledgeConfidenceRegistry(versions)
    relationships = ResearchKnowledgeRelationshipRegistry(versions)
    for number, version_id, level in (("1", "KV-001", "high"), ("2", "KV-002", "medium"), ("3", "KV-003", "low")):
        confidence.register(f"confidence-{number}", version_id, level)
    relationships.register("relationship-1", "KV-001", "KV-101", "supports")
    relationships.register("relationship-2", "KV-002", "KV-101", "refines")
    relationships.register("relationship-3", "KV-003", "KV-101", "related_to")
    consumption = KnowledgeConsumptionAccess(versions, ResearchKnowledgeConfidenceAccess(confidence), ResearchKnowledgeRelationshipAccess(relationships))

    public = {item.knowledge_version_id: item for item in consumption.list()}
    assert {public[key].knowledge_id for key in ("KV-001", "KV-002", "KV-003")} == {"K-001"}
    assert {public[key].version for key in ("KV-001", "KV-002", "KV-003")} == {"1", "2", "3"}
    assert v2.previous_knowledge_version_id == "KV-001"
    assert v3.previous_knowledge_version_id == "KV-002"
    assert public["KV-001"].confidence_reference == "confidence-1"
    assert public["KV-002"].confidence_reference == "confidence-2"
    assert public["KV-003"].confidence_reference == "confidence-3"
    assert public["KV-001"].relationship_references == ("relationship-1",)
    assert public["KV-002"].relationship_references == ("relationship-2",)
    assert public["KV-003"].relationship_references == ("relationship-3",)
    assert public["KV-101"].knowledge_id == "K-002"
