from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from quant_platform.data.availability import DatasetAvailabilityAccess
from quant_platform.research.execution.research_execution_record import (
    ResearchExecutionRecord,
)
from quant_platform.research.research_registry import ResearchRegistry
from quant_platform.research.configuration.research_configuration_registry import (
    ResearchConfigurationRegistry,
)

CREATED = "CREATED"
RUNNING = "RUNNING"
COMPLETED = "COMPLETED"
FAILED = "FAILED"


class ResearchExecutionRegistry:
    """Registry for recording research executions (evidence)."""

    def __init__(
        self,
        config_registry: ResearchConfigurationRegistry,
        research_registry: ResearchRegistry,
        dataset_access: DatasetAvailabilityAccess,
    ) -> None:
        self._config_registry = config_registry
        self._research_registry = research_registry
        self._dataset_access = dataset_access
        self._executions: Dict[str, ResearchExecutionRecord] = {}

    def register(
        self, execution_id: str, configuration_id: str
    ) -> ResearchExecutionRecord:
        config = self._config_registry.get(configuration_id)
        if config is None:
            raise ValueError(f"unknown configuration '{configuration_id}'")

        research = self._research_registry.get(config.research_id)
        if research is None:
            raise ValueError(
                f"research referenced by configuration not found: '{config.research_id}'"
            )

        dataset = self._dataset_access.get(
            research.dataset_id, research.dataset_version
        )
        if dataset is None:
            raise ValueError(
                f"dataset referenced by research not available: '{research.dataset_id}'"
            )

        record = ResearchExecutionRecord(
            execution_id=execution_id,
            research_id=config.research_id,
            configuration_id=configuration_id,
            dataset_id=research.dataset_id,
            dataset_version=research.dataset_version,
            status=CREATED,
        )

        self._executions[execution_id] = record
        return record

    def get(self, execution_id: str) -> Optional[ResearchExecutionRecord]:
        return self._executions.get(execution_id)

    def start(self, execution_id: str) -> ResearchExecutionRecord:
        record = self._executions.get(execution_id)
        if record is None:
            raise ValueError(f"unknown execution '{execution_id}'")
        if record.status != CREATED:
            raise ValueError("execution must be in CREATED state to start")

        record.started_at = datetime.utcnow()
        record.status = RUNNING
        return record

    def complete(self, execution_id: str) -> ResearchExecutionRecord:
        record = self._executions.get(execution_id)
        if record is None:
            raise ValueError(f"unknown execution '{execution_id}'")
        if record.status != RUNNING:
            raise ValueError("execution must be RUNNING to complete")

        record.finished_at = datetime.utcnow()
        record.status = COMPLETED
        return record

    def fail(self, execution_id: str) -> ResearchExecutionRecord:
        record = self._executions.get(execution_id)
        if record is None:
            raise ValueError(f"unknown execution '{execution_id}'")
        if record.status != RUNNING:
            raise ValueError("execution must be RUNNING to fail")

        record.finished_at = datetime.utcnow()
        record.status = FAILED
        return record
