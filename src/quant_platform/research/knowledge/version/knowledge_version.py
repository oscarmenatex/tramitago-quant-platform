from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Protocol


class KnowledgeVersion(Protocol):
    """Stable internal contract shared by every reusable knowledge version."""

    @property
    def knowledge_id(self) -> str: ...

    @property
    def knowledge_version_id(self) -> str: ...

    candidate_id: str
    result_id: str
    knowledge_type: str
    description: str
    version: str
    created_at: datetime | None
    status: str


class KnowledgeVersionSource(Protocol):
    """Read-only source of knowledge versions for the internal contract."""

    def get(self, knowledge_version_id: str) -> Optional[KnowledgeVersion]: ...

    def exists(self, knowledge_version_id: str) -> bool: ...

    def list(self) -> List[KnowledgeVersion]: ...
