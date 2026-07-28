from __future__ import annotations

from typing import Optional

from quant_platform.research.execution.research_execution_record import (
    ResearchExecutionRecord,
)
from quant_platform.research.execution.research_execution_registry import (
    ResearchExecutionRegistry,
)


class ResearchExecutionAccess:
    """Read-only access adapter for executions."""

    def __init__(self, registry: ResearchExecutionRegistry) -> None:
        self._registry = registry

    def get(self, execution_id: str) -> Optional[ResearchExecutionRecord]:
        return self._registry.get(execution_id)
