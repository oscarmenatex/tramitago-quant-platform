"""Immutable contracts for externally observed economic reality."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Generic, TypeVar

from quant_platform.core import CurrencyReference, InstrumentReference

from .exceptions import ExternalEconomicObservationDomainError


def _invalid(message: str) -> ExternalEconomicObservationDomainError:
    return ExternalEconomicObservationDomainError(message)


def _finite_decimal(value: object, label: str) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise _invalid(f"{label} must be an exact, finite Decimal.")
    return value


@dataclass(frozen=True, slots=True)
class ExternalEconomicAuthority:
    """Capability-local identity of the authority making an observation."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value:
            raise _invalid("Authority must be a non-empty string.")
        if self.value != self.value.strip():
            raise _invalid("Authority must not contain peripheral whitespace.")


@dataclass(frozen=True, slots=True)
class EconomicRealityReferenceTime:
    """Unambiguous instant to which the asserted economic reality refers."""

    value: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.value, datetime):
            raise _invalid("Economic reference time must be a datetime.")
        if self.value.tzinfo is None or self.value.utcoffset() is None:
            raise _invalid("Economic reference time must include a UTC offset.")


@dataclass(frozen=True, slots=True)
class ObservedPositionAssertion:
    instrument: InstrumentReference
    quantity: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.instrument, InstrumentReference):
            raise _invalid("Observed position requires an InstrumentReference.")
        _finite_decimal(self.quantity, "Observed position quantity")


@dataclass(frozen=True, slots=True)
class ObservedMonetaryAssertion:
    currency: CurrencyReference
    amount: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.currency, CurrencyReference):
            raise _invalid("Observed monetary balance requires a CurrencyReference.")
        _finite_decimal(self.amount, "Observed monetary amount")


IdentityT = TypeVar("IdentityT", InstrumentReference, CurrencyReference)


@dataclass(frozen=True, slots=True, init=False)
class _Coverage(Generic[IdentityT]):
    is_complete: bool
    covered_identities: frozenset[IdentityT]

    def _initialize(
        self,
        is_complete: bool,
        identities: Iterable[IdentityT],
        identity_type: type[IdentityT],
    ) -> None:
        try:
            covered = frozenset(identities)
        except TypeError:
            raise _invalid("Coverage identities must be a finite iterable.") from None
        if any(not isinstance(item, identity_type) for item in covered):
            raise _invalid(f"Coverage requires {identity_type.__name__} values.")
        if is_complete and covered:
            raise _invalid("Complete coverage must not enumerate identities.")
        object.__setattr__(self, "is_complete", is_complete)
        object.__setattr__(self, "covered_identities", covered)

    def covers(self, identity: IdentityT) -> bool:
        """Return whether the identity is within this coverage."""
        return self.is_complete or identity in self.covered_identities


@dataclass(frozen=True, slots=True, init=False)
class PositionCoverage(_Coverage[InstrumentReference]):
    @classmethod
    def complete(cls) -> "PositionCoverage":
        result = cls()
        result._initialize(True, (), InstrumentReference)
        return result

    @classmethod
    def partial(
        cls, identities: Iterable[InstrumentReference] = ()
    ) -> "PositionCoverage":
        result = cls()
        result._initialize(False, identities, InstrumentReference)
        return result


@dataclass(frozen=True, slots=True, init=False)
class MonetaryCoverage(_Coverage[CurrencyReference]):
    @classmethod
    def complete(cls) -> "MonetaryCoverage":
        result = cls()
        result._initialize(True, (), CurrencyReference)
        return result

    @classmethod
    def partial(
        cls, identities: Iterable[CurrencyReference] = ()
    ) -> "MonetaryCoverage":
        result = cls()
        result._initialize(False, identities, CurrencyReference)
        return result


def _as_tuple(values: Iterable[object], label: str) -> tuple[object, ...]:
    try:
        return tuple(values)
    except TypeError:
        raise _invalid(f"{label} must be a finite iterable.") from None


def _canonical_positions(
    assertions: Iterable[ObservedPositionAssertion],
) -> tuple[ObservedPositionAssertion, ...]:
    values = _as_tuple(assertions, "Observed positions")
    if any(not isinstance(item, ObservedPositionAssertion) for item in values):
        raise _invalid("Observed positions contain an invalid assertion.")
    instruments = [item.instrument for item in values]
    if len(set(instruments)) != len(instruments):
        raise _invalid("Only one position assertion per instrument is allowed.")
    return tuple(sorted(values, key=lambda item: item.instrument.semantic_identity))


def _canonical_monetary(
    assertions: Iterable[ObservedMonetaryAssertion],
) -> tuple[ObservedMonetaryAssertion, ...]:
    values = _as_tuple(assertions, "Observed monetary balances")
    if any(not isinstance(item, ObservedMonetaryAssertion) for item in values):
        raise _invalid("Observed monetary balances contain an invalid assertion.")
    currencies = [item.currency for item in values]
    if len(set(currencies)) != len(currencies):
        raise _invalid("Only one monetary assertion per currency is allowed.")
    return tuple(sorted(values, key=lambda item: item.currency.semantic_identity))


@dataclass(frozen=True, slots=True, init=False)
class SupportingEconomicEvidence:
    authority: ExternalEconomicAuthority
    reference_time: EconomicRealityReferenceTime
    position_coverage: PositionCoverage
    monetary_coverage: MonetaryCoverage
    observed_positions: tuple[ObservedPositionAssertion, ...]
    observed_monetary_balances: tuple[ObservedMonetaryAssertion, ...]

    def __init__(
        self,
        *,
        authority: ExternalEconomicAuthority,
        reference_time: EconomicRealityReferenceTime,
        position_coverage: PositionCoverage,
        monetary_coverage: MonetaryCoverage,
        observed_positions: Iterable[ObservedPositionAssertion] = (),
        observed_monetary_balances: Iterable[ObservedMonetaryAssertion] = (),
    ) -> None:
        if not isinstance(authority, ExternalEconomicAuthority):
            raise _invalid("Evidence requires an ExternalEconomicAuthority.")
        if not isinstance(reference_time, EconomicRealityReferenceTime):
            raise _invalid("Evidence requires an EconomicRealityReferenceTime.")
        if not isinstance(position_coverage, PositionCoverage):
            raise _invalid("Evidence requires position coverage.")
        if not isinstance(monetary_coverage, MonetaryCoverage):
            raise _invalid("Evidence requires monetary coverage.")
        positions = _canonical_positions(observed_positions)
        monetary = _canonical_monetary(observed_monetary_balances)
        if any(not position_coverage.covers(item.instrument) for item in positions):
            raise _invalid("A position assertion exceeds its evidence coverage.")
        if any(not monetary_coverage.covers(item.currency) for item in monetary):
            raise _invalid("A monetary assertion exceeds its evidence coverage.")
        if not (
            positions
            or monetary
            or position_coverage.is_complete
            or monetary_coverage.is_complete
            or position_coverage.covered_identities
            or monetary_coverage.covered_identities
        ):
            raise _invalid("Evidence must contain meaningful economic coverage or facts.")
        object.__setattr__(self, "authority", authority)
        object.__setattr__(self, "reference_time", reference_time)
        object.__setattr__(self, "position_coverage", position_coverage)
        object.__setattr__(self, "monetary_coverage", monetary_coverage)
        object.__setattr__(self, "observed_positions", positions)
        object.__setattr__(self, "observed_monetary_balances", monetary)


def _evidence_key(evidence: SupportingEconomicEvidence) -> tuple[object, ...]:
    return (
        evidence.authority.value,
        evidence.reference_time.value.isoformat(),
        evidence.position_coverage.is_complete,
        tuple(
            sorted(
                x.semantic_identity
                for x in evidence.position_coverage.covered_identities
            )
        ),
        evidence.monetary_coverage.is_complete,
        tuple(
            sorted(
                x.semantic_identity
                for x in evidence.monetary_coverage.covered_identities
            )
        ),
        tuple((x.instrument.semantic_identity, str(x.quantity)) for x in evidence.observed_positions),
        tuple((x.currency.semantic_identity, str(x.amount)) for x in evidence.observed_monetary_balances),
    )


@dataclass(frozen=True, slots=True, init=False)
class ExternallyObservedEconomicReality:
    authority: ExternalEconomicAuthority
    reference_time: EconomicRealityReferenceTime
    position_coverage: PositionCoverage
    monetary_coverage: MonetaryCoverage
    observed_positions: tuple[ObservedPositionAssertion, ...]
    observed_monetary_balances: tuple[ObservedMonetaryAssertion, ...]
    supporting_evidence: tuple[SupportingEconomicEvidence, ...]

    def __init__(self) -> None:
        raise _invalid(
            "ExternallyObservedEconomicReality must be published from evidence."
        )

    @classmethod
    def _from_evidence(
        cls,
        *,
        authority: ExternalEconomicAuthority,
        reference_time: EconomicRealityReferenceTime,
        position_coverage: PositionCoverage,
        monetary_coverage: MonetaryCoverage,
        observed_positions: tuple[ObservedPositionAssertion, ...],
        observed_monetary_balances: tuple[ObservedMonetaryAssertion, ...],
        supporting_evidence: tuple[SupportingEconomicEvidence, ...],
    ) -> "ExternallyObservedEconomicReality":
        result = object.__new__(cls)
        object.__setattr__(result, "authority", authority)
        object.__setattr__(result, "reference_time", reference_time)
        object.__setattr__(result, "position_coverage", position_coverage)
        object.__setattr__(result, "monetary_coverage", monetary_coverage)
        object.__setattr__(result, "observed_positions", observed_positions)
        object.__setattr__(result, "observed_monetary_balances", observed_monetary_balances)
        object.__setattr__(result, "supporting_evidence", supporting_evidence)
        return result


def _merge_coverage(
    evidence: tuple[SupportingEconomicEvidence, ...],
    attribute: str,
) -> PositionCoverage | MonetaryCoverage:
    coverages = [getattr(item, attribute) for item in evidence]
    coverage_type = type(coverages[0])
    if any(item.is_complete for item in coverages):
        return coverage_type.complete()
    identities = frozenset().union(*(item.covered_identities for item in coverages))
    return coverage_type.partial(identities)


def _merge_assertions(
    assertions: Iterable[ObservedPositionAssertion | ObservedMonetaryAssertion],
    identity_attribute: str,
    value_attribute: str,
) -> tuple[ObservedPositionAssertion | ObservedMonetaryAssertion, ...]:
    merged: dict[object, ObservedPositionAssertion | ObservedMonetaryAssertion] = {}
    for assertion in assertions:
        identity = getattr(assertion, identity_attribute)
        previous = merged.get(identity)
        if previous is not None and getattr(previous, value_attribute) != getattr(
            assertion, value_attribute
        ):
            raise _invalid(f"Contradictory evidence for {identity_attribute}.")
        merged[identity] = assertion
    return tuple(
        sorted(
            merged.values(),
            key=lambda item: getattr(item, identity_attribute).semantic_identity,
        )
    )


def observe_external_economic_reality(
    evidence: Iterable[SupportingEconomicEvidence],
) -> ExternallyObservedEconomicReality:
    """Publish the single external reality constituted by compatible evidence."""
    supplied = _as_tuple(evidence, "Supporting evidence")
    if not supplied:
        raise _invalid("At least one supporting evidence unit is required.")
    if any(not isinstance(item, SupportingEconomicEvidence) for item in supplied):
        raise _invalid("Supporting evidence contains an invalid value.")
    typed = tuple(supplied)
    authority = typed[0].authority
    reference_time = typed[0].reference_time
    if any(item.authority != authority for item in typed):
        raise _invalid("All evidence must have one authority.")
    if any(item.reference_time != reference_time for item in typed):
        raise _invalid("All evidence must have one economic reference time.")
    positions = _merge_assertions(
        (assertion for item in typed for assertion in item.observed_positions),
        "instrument",
        "quantity",
    )
    monetary = _merge_assertions(
        (assertion for item in typed for assertion in item.observed_monetary_balances),
        "currency",
        "amount",
    )
    canonical_evidence = tuple(sorted(typed, key=_evidence_key))
    return ExternallyObservedEconomicReality._from_evidence(
        authority=authority,
        reference_time=reference_time,
        position_coverage=_merge_coverage(typed, "position_coverage"),
        monetary_coverage=_merge_coverage(typed, "monetary_coverage"),
        observed_positions=positions,
        observed_monetary_balances=monetary,
        supporting_evidence=canonical_evidence,
    )
