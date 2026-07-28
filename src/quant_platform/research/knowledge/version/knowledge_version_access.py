from __future__ import annotations

from typing import List, Optional

from quant_platform.research.knowledge.version.knowledge_version import (
    KnowledgeVersion,
    KnowledgeVersionSource,
)


class KnowledgeVersionAccess:
    """Read-only composition boundary for all reusable knowledge versions."""

    def __init__(self, *sources: KnowledgeVersionSource) -> None:
        if not sources:
            raise ValueError("at least one knowledge version source is required")
        self._sources = sources

    def get(self, knowledge_id: str) -> Optional[KnowledgeVersion]:
        for source in self._sources:
            version = source.get(knowledge_id)
            if version is not None:
                return version
        return None

    def exists(self, knowledge_id: str) -> bool:
        return bool(knowledge_id) and self.get(knowledge_id) is not None

    def list(self) -> List[KnowledgeVersion]:
        return [version for source in self._sources for version in source.list()]
