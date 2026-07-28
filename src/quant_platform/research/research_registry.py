"""Research definition registry management."""

from datetime import datetime
from typing import Dict

from quant_platform.data.availability import DatasetAvailabilityAccess
from quant_platform.research.research_record import ResearchRecord

INITIAL_STATUS = "DEFINED"


class ResearchRegistry:
    """Register and query research definitions."""

    def __init__(self, dataset_access: DatasetAvailabilityAccess) -> None:
        self._research: Dict[str, ResearchRecord] = {}
        self._dataset_access = dataset_access

    def register(
        self,
        research_id: str,
        name: str,
        objective: str,
        dataset_id: str,
        dataset_version: str,
    ) -> ResearchRecord:
        """Register a research definition associated to an available dataset."""
        if not research_id or not research_id.strip():
            raise ValueError("research_id must be provided")
        if not name or not name.strip():
            raise ValueError("name must be provided")
        if not objective or not objective.strip():
            raise ValueError("objective must be provided")
        if not dataset_id or not dataset_id.strip():
            raise ValueError("dataset_id must be provided")
        if not isinstance(dataset_version, str) or not dataset_version.strip():
            raise ValueError("dataset_version must be a non-empty string")

        dataset = self._dataset_access.get(dataset_id, dataset_version)
        if dataset is None:
            raise ValueError("dataset_id must refer to an available dataset")

        research = ResearchRecord(
            research_id=research_id,
            name=name,
            objective=objective,
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            created_at=datetime.now(),
            status=INITIAL_STATUS,
        )

        self._research[research_id] = research
        return research

    def get(self, research_id: str) -> ResearchRecord | None:
        """Return a previously registered research definition."""
        return self._research.get(research_id)
