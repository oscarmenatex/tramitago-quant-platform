from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from quant_platform.research.execution.research_execution_registry import (
    ResearchExecutionRegistry,
    COMPLETED,
)
from quant_platform.research.result.research_result_record import (
    ResearchResultRecord,
)

CREATED = "CREATED"


class ResearchResultRegistry:
    """Registry for recording research results (evidence)."""

    def __init__(self, execution_registry: ResearchExecutionRegistry) -> None:
        self._execution_registry = execution_registry
        self._results: Dict[str, ResearchResultRecord] = {}
        self._execution_to_result: Dict[str, str] = {}

    def register(self, result_id: str, execution_id: str) -> ResearchResultRecord:
        if not result_id:
            raise ValueError("result_id is required")

        execution = self._execution_registry.get(execution_id)
        if execution is None:
            raise ValueError(f"unknown execution '{execution_id}'")

        if execution.status != COMPLETED:
            raise ValueError("execution must be COMPLETED to register a result")

        if execution_id in self._execution_to_result:
            raise ValueError(
                f"result already registered for execution '{execution_id}'"
            )

        record = ResearchResultRecord(
            result_id=result_id,
            execution_id=execution_id,
            created_at=datetime.utcnow(),
            status=CREATED,
        )

        self._results[result_id] = record
        self._execution_to_result[execution_id] = result_id

        return record

    def get(self, result_id: str) -> Optional[ResearchResultRecord]:
        return self._results.get(result_id)

    def get_by_execution(self, execution_id: str) -> Optional[ResearchResultRecord]:
        rid = self._execution_to_result.get(execution_id)
        if rid is None:
            return None
        return self._results.get(rid)
