"""Normative reliance disposition under an explicitly supplied authority."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from quant_platform.post_verification_qualification import (
    PostVerificationQualification,
    PostVerificationQualificationCondition,
)

from .exceptions import EconomicRealityRelianceDispositionDomainError


class EconomicRealityRelianceOutcome(Enum):
    RELIANCE_PERMITTED = "RELIANCE_PERMITTED"
    RELIANCE_PROHIBITED = "RELIANCE_PROHIBITED"


def _invalid(message: str) -> EconomicRealityRelianceDispositionDomainError:
    return EconomicRealityRelianceDispositionDomainError(message)


@dataclass(frozen=True, slots=True, init=False)
class EconomicRealityRelianceAuthority:
    """Immutable normative rules for public qualification conditions."""

    rules: frozenset[
        tuple[PostVerificationQualificationCondition, EconomicRealityRelianceOutcome]
    ]

    def __init__(
        self,
        rules: Mapping[
            PostVerificationQualificationCondition, EconomicRealityRelianceOutcome
        ],
    ) -> None:
        if not isinstance(rules, Mapping):
            raise _invalid("Reliance authority rules must be supplied as a mapping.")
        supplied = tuple(rules.items())
        if any(
            not isinstance(condition, PostVerificationQualificationCondition)
            or not isinstance(outcome, EconomicRealityRelianceOutcome)
            for condition, outcome in supplied
        ):
            raise _invalid("Reliance authority contains an invalid normative rule.")
        object.__setattr__(self, "rules", frozenset(supplied))

    def disposition_for(
        self, condition: PostVerificationQualificationCondition
    ) -> EconomicRealityRelianceOutcome:
        """Determine the normative outcome, failing when this authority is insufficient."""
        outcomes = tuple(
            outcome
            for governed_condition, outcome in self.rules
            if governed_condition is condition
        )
        if len(outcomes) != 1:
            raise _invalid(
                "The reliance authority is insufficient for this qualification."
            )
        return outcomes[0]


@dataclass(frozen=True, slots=True, init=False)
class EconomicRealityRelianceDisposition:
    """Immutable disposition derived from a qualification and explicit authority."""

    qualification: PostVerificationQualification
    authority: EconomicRealityRelianceAuthority
    outcome: EconomicRealityRelianceOutcome

    def __init__(self) -> None:
        raise _invalid(
            "EconomicRealityRelianceDisposition must be produced by "
            "dispose_economic_reality_reliance."
        )

    @classmethod
    def _create(
        cls,
        qualification: PostVerificationQualification,
        authority: EconomicRealityRelianceAuthority,
        outcome: EconomicRealityRelianceOutcome,
    ) -> "EconomicRealityRelianceDisposition":
        value = object.__new__(cls)
        object.__setattr__(value, "qualification", qualification)
        object.__setattr__(value, "authority", authority)
        object.__setattr__(value, "outcome", outcome)
        return value


def dispose_economic_reality_reliance(
    qualification: PostVerificationQualification,
    authority: EconomicRealityRelianceAuthority,
) -> EconomicRealityRelianceDisposition:
    """Publish the reliance disposition determined by the explicit authority."""
    if not isinstance(qualification, PostVerificationQualification):
        raise _invalid("A published PostVerificationQualification is required.")
    if not isinstance(authority, EconomicRealityRelianceAuthority):
        raise _invalid("A valid EconomicRealityRelianceAuthority is required.")
    outcome = authority.disposition_for(qualification.condition)
    return EconomicRealityRelianceDisposition._create(qualification, authority, outcome)
