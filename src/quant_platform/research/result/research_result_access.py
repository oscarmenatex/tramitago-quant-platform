from __future__ import annotations

from typing import Optional

from quant_platform.research.result.research_result_record import (
    ResearchResultRecord,
)
from quant_platform.research.result.research_result_registry import (
    ResearchResultRegistry,
)


class ResearchResultAccess:
    """Read-only access adapter for research results."""

    def __init__(self, registry: ResearchResultRegistry) -> None:
        self._registry = registry

    def get(self, result_id: str) -> Optional[ResearchResultRecord]:
        return self._registry.get(result_id)

    def get_by_execution(self, execution_id: str) -> Optional[ResearchResultRecord]:
        return self._registry.get_by_execution(execution_id)
