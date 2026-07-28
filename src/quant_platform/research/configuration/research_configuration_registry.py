from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from quant_platform.research.research_registry import ResearchRegistry
from quant_platform.research.configuration.research_configuration_record import (
    ResearchConfigurationRecord,
)


class ResearchConfigurationRegistry:
    """Registry for research configuration metadata."""

    def __init__(self, research_registry: ResearchRegistry) -> None:
        self._research_registry = research_registry
        self._configurations: Dict[str, ResearchConfigurationRecord] = {}

    def register(
        self,
        configuration_id: str,
        research_id: str,
        access_policy: str,
        description: Optional[str] = None,
    ) -> ResearchConfigurationRecord:
        research = self._research_registry.get(research_id)
        if research is None:
            raise ValueError(
                f"Cannot register research configuration for unknown research '{research_id}'"
            )

        now = datetime.utcnow()
        record = ResearchConfigurationRecord(
            configuration_id=configuration_id,
            research_id=research_id,
            access_policy=access_policy,
            created_at=now,
            updated_at=now,
            description=description,
        )
        self._configurations[configuration_id] = record
        return record

    def get(self, configuration_id: str) -> Optional[ResearchConfigurationRecord]:
        return self._configurations.get(configuration_id)
