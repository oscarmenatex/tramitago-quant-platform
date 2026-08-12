from datetime import datetime, timezone

import pytest

from quant_platform.external_economic_observation import (
    EconomicRealityReferenceTime,
    ExternalEconomicAuthority,
)


@pytest.fixture
def authority():
    return ExternalEconomicAuthority("independent-custodian")


@pytest.fixture
def reference_time():
    return EconomicRealityReferenceTime(
        datetime(2026, 8, 12, 16, 0, tzinfo=timezone.utc)
    )
