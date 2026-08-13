"""Deterministic public demo for IT-042-001."""

from datetime import datetime, timezone
from decimal import Decimal

from quant_platform.core import InstrumentReference
from quant_platform.internal_economic_reality import (
    InternalEconomicRealityEvidence,
    InternalEconomicRealityProvenance,
    InternalEconomicRealityReferenceTime,
    qualify_internal_economic_reality,
)
from quant_platform.portfolio import PortfolioPosition, PortfolioState


state = PortfolioState(
    positions=(
        PortfolioPosition(InstrumentReference("FIGI", "IER-DEMO"), Decimal("3")),
    )
)
evidence = InternalEconomicRealityEvidence(
    state,
    InternalEconomicRealityReferenceTime(
        datetime(2026, 8, 12, 16, tzinfo=timezone.utc)
    ),
    InternalEconomicRealityProvenance("deterministic-internal-ledger"),
)
reality = qualify_internal_economic_reality((evidence,))

print("InternalEconomicRealityEvidence -> InternalEconomicReality")
print(f"portfolio state: {reality.portfolio_state}")
print(f"economic reference time: {reality.reference_time.value.isoformat()}")
print(f"provenance: {reality.supporting_evidence[0].provenance.value}")
print(f"supporting evidence: {reality.supporting_evidence}")
assert reality.portfolio_state is state
assert reality.supporting_evidence == (evidence,)
print("Internal Economic Reality Qualification demo passed.")
