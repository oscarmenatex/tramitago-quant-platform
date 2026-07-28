from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ResearchKnowledgeCandidateRecord:
    """Representation of a knowledge candidate derived from a research result."""

    knowledge_candidate_id: str
    result_id: str
    knowledge_type: str
    description: str
    version: str = "1"
    created_at: datetime | None = None
    status: str = "CANDIDATE"
