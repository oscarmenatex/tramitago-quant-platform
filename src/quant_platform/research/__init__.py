"""Quantitative research components."""

from quant_platform.research.configuration import (
    ResearchConfigurationRecord,
    ResearchConfigurationRegistry,
)
from quant_platform.research.dataset_consumer import ResearchDatasetConsumer
from quant_platform.research.research_record import ResearchRecord
from quant_platform.research.research_registry import ResearchRegistry
from quant_platform.research.result.research_result_record import (
    ResearchResultRecord,
)
from quant_platform.research.result.research_result_registry import (
    ResearchResultRegistry,
)
from quant_platform.research.result.research_result_access import (
    ResearchResultAccess,
)
from quant_platform.research.knowledge.research_knowledge_record import (
    ResearchKnowledgeRecord,
)
from quant_platform.research.knowledge.research_knowledge_registry import (
    ResearchKnowledgeRegistry,
)
from quant_platform.research.knowledge.research_knowledge_access import (
    ResearchKnowledgeAccess,
)
from quant_platform.research.knowledge.candidate.research_knowledge_candidate_record import (
    ResearchKnowledgeCandidateRecord,
)
from quant_platform.research.knowledge.candidate.research_knowledge_candidate_registry import (
    ResearchKnowledgeCandidateRegistry,
)
from quant_platform.research.knowledge.candidate.research_knowledge_candidate_access import (
    ResearchKnowledgeCandidateAccess,
)
from quant_platform.research.knowledge.validation.research_validated_knowledge_record import (
    ResearchValidatedKnowledgeRecord,
)
from quant_platform.research.knowledge.validation.research_validated_knowledge_registry import (
    ResearchValidatedKnowledgeRegistry,
)
from quant_platform.research.knowledge.validation.research_validated_knowledge_access import (
    ResearchValidatedKnowledgeAccess,
)
from quant_platform.research.knowledge.validation.research_knowledge_validation_service import (
    ResearchKnowledgeValidationService,
)
from quant_platform.research.knowledge.confidence.research_knowledge_confidence_record import (
    ResearchKnowledgeConfidenceRecord,
)
from quant_platform.research.knowledge.confidence.research_knowledge_confidence_registry import (
    ResearchKnowledgeConfidenceRegistry,
)
from quant_platform.research.knowledge.confidence.research_knowledge_confidence_access import (
    ResearchKnowledgeConfidenceAccess,
)
from quant_platform.research.knowledge.confidence.research_knowledge_confidence_service import (
    ResearchKnowledgeConfidenceService,
)
from quant_platform.research.knowledge.relationship.research_knowledge_relationship_record import (
    ResearchKnowledgeRelationshipRecord,
)
from quant_platform.research.knowledge.relationship.research_knowledge_relationship_registry import (
    ResearchKnowledgeRelationshipRegistry,
)
from quant_platform.research.knowledge.relationship.research_knowledge_relationship_access import (
    ResearchKnowledgeRelationshipAccess,
)
from quant_platform.research.knowledge.version.knowledge_version import KnowledgeVersion
from quant_platform.research.knowledge.version.knowledge_version_access import (
    KnowledgeVersionAccess,
)

__all__ = [
    "ResearchDatasetConsumer",
    "ResearchRecord",
    "ResearchRegistry",
    "ResearchConfigurationRecord",
    "ResearchConfigurationRegistry",
    "ResearchResultRecord",
    "ResearchResultRegistry",
    "ResearchResultAccess",
    "ResearchKnowledgeRecord",
    "ResearchKnowledgeRegistry",
    "ResearchKnowledgeAccess",
    "ResearchKnowledgeCandidateRecord",
    "ResearchKnowledgeCandidateRegistry",
    "ResearchKnowledgeCandidateAccess",
    "ResearchValidatedKnowledgeRecord",
    "ResearchValidatedKnowledgeRegistry",
    "ResearchValidatedKnowledgeAccess",
    "ResearchKnowledgeValidationService",
    "ResearchKnowledgeConfidenceRecord",
    "ResearchKnowledgeConfidenceRegistry",
    "ResearchKnowledgeConfidenceAccess",
    "ResearchKnowledgeConfidenceService",
    "ResearchKnowledgeRelationshipRecord",
    "ResearchKnowledgeRelationshipRegistry",
    "ResearchKnowledgeRelationshipAccess",
    "KnowledgeVersion",
    "KnowledgeVersionAccess",
]
