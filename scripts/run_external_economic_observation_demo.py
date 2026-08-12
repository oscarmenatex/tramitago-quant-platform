"""Deterministic public demonstration of External Economic Observation."""

from datetime import datetime, timezone
from decimal import Decimal

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.external_economic_observation import (
    EconomicRealityReferenceTime,
    ExternalEconomicAuthority,
    MonetaryCoverage,
    ObservedMonetaryAssertion,
    ObservedPositionAssertion,
    PositionCoverage,
    SupportingEconomicEvidence,
    observe_external_economic_reality,
)


def main() -> None:
    authority = ExternalEconomicAuthority("independent-custodian-demo")
    reference_time = EconomicRealityReferenceTime(
        datetime(2026, 8, 12, 16, 0, tzinfo=timezone.utc)
    )
    instrument = InstrumentReference("figi", "DEMO-INSTRUMENT")
    currency = CurrencyReference("USD")
    source = SupportingEconomicEvidence(
        authority=authority,
        reference_time=reference_time,
        position_coverage=PositionCoverage.partial([instrument]),
        monetary_coverage=MonetaryCoverage.complete(),
        observed_positions=[ObservedPositionAssertion(instrument, Decimal("3"))],
        observed_monetary_balances=[ObservedMonetaryAssertion(currency, Decimal("0"))],
    )
    reality = observe_external_economic_reality([source])
    print("supporting evidence -> externally observed economic reality")
    print("authority:", reality.authority.value)
    print("economic reference time:", reality.reference_time.value.isoformat())
    print("position coverage complete:", reality.position_coverage.is_complete)
    print("monetary coverage complete:", reality.monetary_coverage.is_complete)
    print("observed position:", reality.observed_positions[0])
    print("supporting provenance:", reality.supporting_evidence)
    print("External Economic Observation demo passed.")


if __name__ == "__main__":
    main()
