"""Immutable verification between published internal and external realities."""

from dataclasses import dataclass
from datetime import timezone
from decimal import Decimal
from enum import Enum

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.external_economic_observation import (
    ExternallyObservedEconomicReality,
)
from quant_platform.internal_economic_reality import InternalEconomicReality

from .exceptions import EconomicRealityVerificationDomainError


class EconomicRealityDimension(Enum):
    POSITION = "POSITION"
    MONETARY_BALANCE = "MONETARY_BALANCE"


class EconomicRealityVerificationOutcome(Enum):
    AGREEMENT = "AGREEMENT"
    DISCREPANCY = "DISCREPANCY"
    NOT_COMPARABLE = "NOT_COMPARABLE"


EconomicIdentity = InstrumentReference | CurrencyReference


@dataclass(frozen=True, slots=True, init=False)
class EconomicRealityVerificationResult:
    """One conclusion for one dimension and economic identity."""

    dimension: EconomicRealityDimension
    identity: EconomicIdentity
    outcome: EconomicRealityVerificationOutcome
    internal_value: Decimal
    external_value: Decimal | None

    def __init__(self) -> None:
        raise EconomicRealityVerificationDomainError(
            "Verification results can only be produced by verify_economic_reality."
        )

    @classmethod
    def _create(
        cls,
        dimension: EconomicRealityDimension,
        identity: EconomicIdentity,
        outcome: EconomicRealityVerificationOutcome,
        internal_value: Decimal,
        external_value: Decimal | None,
    ) -> "EconomicRealityVerificationResult":
        result = object.__new__(cls)
        object.__setattr__(result, "dimension", dimension)
        object.__setattr__(result, "identity", identity)
        object.__setattr__(result, "outcome", outcome)
        object.__setattr__(result, "internal_value", internal_value)
        object.__setattr__(result, "external_value", external_value)
        return result


@dataclass(frozen=True, slots=True, init=False)
class EconomicRealityVerification:
    """Published, immutable verifying relation; it is not another reality."""

    internal_reality: InternalEconomicReality
    external_reality: ExternallyObservedEconomicReality
    position_results: frozenset[EconomicRealityVerificationResult]
    monetary_results: frozenset[EconomicRealityVerificationResult]

    def __init__(self) -> None:
        raise EconomicRealityVerificationDomainError(
            "EconomicRealityVerification must be produced by verify_economic_reality."
        )

    @classmethod
    def _create(
        cls,
        internal_reality: InternalEconomicReality,
        external_reality: ExternallyObservedEconomicReality,
        position_results: frozenset[EconomicRealityVerificationResult],
        monetary_results: frozenset[EconomicRealityVerificationResult],
    ) -> "EconomicRealityVerification":
        result = object.__new__(cls)
        object.__setattr__(result, "internal_reality", internal_reality)
        object.__setattr__(result, "external_reality", external_reality)
        object.__setattr__(result, "position_results", position_results)
        object.__setattr__(result, "monetary_results", monetary_results)
        return result


def _verify_dimension(
    *,
    dimension: EconomicRealityDimension,
    internal_values: dict[EconomicIdentity, Decimal],
    external_values: dict[EconomicIdentity, Decimal],
    explicitly_covered: frozenset[EconomicIdentity],
    coverage: object,
) -> frozenset[EconomicRealityVerificationResult]:
    identities = set(internal_values) | set(external_values) | set(explicitly_covered)
    results = []
    for identity in identities:
        internal_value = internal_values.get(identity, Decimal(0))
        if not coverage.covers(identity):
            outcome = EconomicRealityVerificationOutcome.NOT_COMPARABLE
            external_value = None
        else:
            external_value = external_values.get(identity, Decimal(0))
            outcome = (
                EconomicRealityVerificationOutcome.AGREEMENT
                if internal_value == external_value
                else EconomicRealityVerificationOutcome.DISCREPANCY
            )
        results.append(
            EconomicRealityVerificationResult._create(
                dimension, identity, outcome, internal_value, external_value
            )
        )
    return frozenset(results)


def verify_economic_reality(
    internal_reality: InternalEconomicReality,
    external_reality: ExternallyObservedEconomicReality,
) -> EconomicRealityVerification:
    """Verify two published realities referring to the same economic instant."""
    if not isinstance(internal_reality, InternalEconomicReality):
        raise EconomicRealityVerificationDomainError(
            "A published InternalEconomicReality is required."
        )
    if not isinstance(external_reality, ExternallyObservedEconomicReality):
        raise EconomicRealityVerificationDomainError(
            "A published ExternallyObservedEconomicReality is required."
        )
    internal_instant = internal_reality.reference_time.value.astimezone(timezone.utc)
    external_instant = external_reality.reference_time.value.astimezone(timezone.utc)
    if internal_instant != external_instant:
        raise EconomicRealityVerificationDomainError(
            "The realities must refer to the same economic instant."
        )

    state = internal_reality.portfolio_state
    positions = _verify_dimension(
        dimension=EconomicRealityDimension.POSITION,
        internal_values={x.instrument: x.quantity for x in state.positions},
        external_values={x.instrument: x.quantity for x in external_reality.observed_positions},
        explicitly_covered=external_reality.position_coverage.covered_identities,
        coverage=external_reality.position_coverage,
    )
    monetary = _verify_dimension(
        dimension=EconomicRealityDimension.MONETARY_BALANCE,
        internal_values={x.currency: x.amount for x in state.monetary_balances},
        external_values={x.currency: x.amount for x in external_reality.observed_monetary_balances},
        explicitly_covered=external_reality.monetary_coverage.covered_identities,
        coverage=external_reality.monetary_coverage,
    )
    return EconomicRealityVerification._create(
        internal_reality, external_reality, positions, monetary
    )
