"""Qualification of verification evidence against an explicit required scope."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.economic_reality_verification import (
    EconomicRealityDimension,
    EconomicRealityVerification,
    EconomicRealityVerificationOutcome,
)

from .exceptions import PostVerificationQualificationDomainError


class PostVerificationQualificationCondition(Enum):
    CORROBORATED = "CORROBORATED"
    DIVERGENT = "DIVERGENT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


EconomicIdentity = InstrumentReference | CurrencyReference


def _invalid(message: str) -> PostVerificationQualificationDomainError:
    return PostVerificationQualificationDomainError(message)


@dataclass(frozen=True, slots=True)
class RequiredCorroborationRequirement:
    """One required economic dimension and its existing public identity."""

    dimension: EconomicRealityDimension
    identity: EconomicIdentity

    def __post_init__(self) -> None:
        valid = (
            self.dimension is EconomicRealityDimension.POSITION
            and isinstance(self.identity, InstrumentReference)
        ) or (
            self.dimension is EconomicRealityDimension.MONETARY_BALANCE
            and isinstance(self.identity, CurrencyReference)
        )
        if not valid:
            raise _invalid("The economic dimension and identity are incompatible.")


@dataclass(frozen=True, slots=True, init=False)
class RequiredCorroborationScope:
    """Immutable, non-empty, order-independent set of corroboration obligations."""

    requirements: frozenset[RequiredCorroborationRequirement]

    def __init__(
        self, requirements: Iterable[RequiredCorroborationRequirement]
    ) -> None:
        try:
            supplied = tuple(requirements)
        except TypeError:
            raise _invalid("Required corroboration scope must be a finite iterable.") from None
        if not supplied:
            raise _invalid("At least one corroboration requirement is required.")
        if any(not isinstance(item, RequiredCorroborationRequirement) for item in supplied):
            raise _invalid("Required corroboration scope contains an invalid value.")
        object.__setattr__(self, "requirements", frozenset(supplied))


@dataclass(frozen=True, slots=True, init=False)
class PostVerificationQualification:
    """Immutable qualification whose condition is derived from its sources."""

    verification: EconomicRealityVerification
    required_scope: RequiredCorroborationScope
    condition: PostVerificationQualificationCondition

    def __init__(self) -> None:
        raise _invalid(
            "PostVerificationQualification must be produced by qualify_post_verification."
        )

    @classmethod
    def _create(
        cls,
        verification: EconomicRealityVerification,
        required_scope: RequiredCorroborationScope,
        condition: PostVerificationQualificationCondition,
    ) -> "PostVerificationQualification":
        value = object.__new__(cls)
        object.__setattr__(value, "verification", verification)
        object.__setattr__(value, "required_scope", required_scope)
        object.__setattr__(value, "condition", condition)
        return value


def qualify_post_verification(
    verification: EconomicRealityVerification,
    required_scope: RequiredCorroborationScope,
) -> PostVerificationQualification:
    """Qualify only the required identities represented by an explicit scope."""
    if not isinstance(verification, EconomicRealityVerification):
        raise _invalid("A published EconomicRealityVerification is required.")
    if not isinstance(required_scope, RequiredCorroborationScope):
        raise _invalid("A valid RequiredCorroborationScope is required.")

    results = {
        (result.dimension, result.identity): result.outcome
        for result in verification.position_results | verification.monetary_results
    }
    required_outcomes = tuple(
        results.get((requirement.dimension, requirement.identity))
        for requirement in required_scope.requirements
    )
    if EconomicRealityVerificationOutcome.DISCREPANCY in required_outcomes:
        condition = PostVerificationQualificationCondition.DIVERGENT
    elif any(
        outcome is None
        or outcome is EconomicRealityVerificationOutcome.NOT_COMPARABLE
        for outcome in required_outcomes
    ):
        condition = PostVerificationQualificationCondition.INSUFFICIENT_EVIDENCE
    else:
        condition = PostVerificationQualificationCondition.CORROBORATED
    return PostVerificationQualification._create(
        verification, required_scope, condition
    )
