"""Immutable qualification of internally asserted economic reality."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone

from quant_platform.portfolio import PortfolioState

from .exceptions import InternalEconomicRealityQualificationDomainError


def _invalid(message: str) -> InternalEconomicRealityQualificationDomainError:
    return InternalEconomicRealityQualificationDomainError(message)


@dataclass(frozen=True, slots=True)
class InternalEconomicRealityReferenceTime:
    """Qualification-local, unambiguous economic instant normalized to UTC."""

    value: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.value, datetime):
            raise _invalid("Economic reference time must be a datetime.")
        if self.value.tzinfo is None or self.value.utcoffset() is None:
            raise _invalid("Economic reference time must include an explicit UTC offset.")
        object.__setattr__(self, "value", self.value.astimezone(timezone.utc))


@dataclass(frozen=True, slots=True)
class InternalEconomicRealityProvenance:
    """Qualification-local identity of an internal source attesting a reality."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value:
            raise _invalid("Internal provenance must be a non-empty string.")
        if self.value != self.value.strip():
            raise _invalid("Internal provenance must not contain peripheral whitespace.")


@dataclass(frozen=True, slots=True)
class InternalEconomicRealityEvidence:
    """Internal attestation that a PortfolioState was effective at an instant."""

    portfolio_state: PortfolioState
    reference_time: InternalEconomicRealityReferenceTime
    provenance: InternalEconomicRealityProvenance

    def __post_init__(self) -> None:
        if not isinstance(self.portfolio_state, PortfolioState):
            raise _invalid("Evidence requires a public PortfolioState.")
        if not isinstance(
            self.reference_time, InternalEconomicRealityReferenceTime
        ):
            raise _invalid("Evidence requires an internal economic reference time.")
        if not isinstance(self.provenance, InternalEconomicRealityProvenance):
            raise _invalid("Evidence requires determinable internal provenance.")


def _evidence_key(evidence: InternalEconomicRealityEvidence) -> tuple[str, ...]:
    return (
        evidence.portfolio_state.semantic_identity,
        evidence.reference_time.value.isoformat(),
        evidence.provenance.value,
    )


@dataclass(frozen=True, slots=True, init=False)
class InternalEconomicReality:
    """PortfolioState asserted as internal economic reality at one instant."""

    portfolio_state: PortfolioState
    reference_time: InternalEconomicRealityReferenceTime
    supporting_evidence: tuple[InternalEconomicRealityEvidence, ...]

    def __init__(self) -> None:
        raise _invalid("InternalEconomicReality must be qualified from evidence.")

    @classmethod
    def _from_evidence(
        cls,
        supporting_evidence: tuple[InternalEconomicRealityEvidence, ...],
    ) -> "InternalEconomicReality":
        result = object.__new__(cls)
        object.__setattr__(result, "portfolio_state", supporting_evidence[0].portfolio_state)
        object.__setattr__(result, "reference_time", supporting_evidence[0].reference_time)
        object.__setattr__(result, "supporting_evidence", supporting_evidence)
        return result


def qualify_internal_economic_reality(
    evidence: Iterable[InternalEconomicRealityEvidence],
) -> InternalEconomicReality:
    """Publish the one internal reality constituted by compatible evidence."""
    try:
        supplied = tuple(evidence)
    except TypeError:
        raise _invalid("Supporting evidence must be a finite iterable.") from None
    if not supplied:
        raise _invalid("At least one internal economic reality evidence is required.")
    if any(not isinstance(item, InternalEconomicRealityEvidence) for item in supplied):
        raise _invalid("Supporting evidence contains an invalid value.")

    portfolio_state = supplied[0].portfolio_state
    reference_time = supplied[0].reference_time
    if any(item.portfolio_state != portfolio_state for item in supplied):
        raise _invalid("All evidence must assert the same PortfolioState.")
    if any(item.reference_time != reference_time for item in supplied):
        raise _invalid("All evidence must assert the same economic instant.")

    canonical_evidence = tuple(sorted(supplied, key=_evidence_key))
    return InternalEconomicReality._from_evidence(canonical_evidence)
