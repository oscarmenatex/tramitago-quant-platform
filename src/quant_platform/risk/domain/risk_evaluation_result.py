"""Immutable public result of a Risk acceptability evaluation."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json

from quant_platform.decision_model import DecisionProposal

from .exceptions import (
    InconsistentRiskConditionsError,
    InvalidDecisionProposalError,
    InvalidEvaluationOutcomeError,
    InvalidRiskEvaluationBasisReferenceError,
)


class RiskEvaluationOutcome(str, Enum):
    """Authorized outcomes represented by a Risk Evaluation Result."""

    ACCEPTED = "ACCEPTED"
    CONDITIONALLY_ACCEPTED = "CONDITIONALLY_ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True, init=False, eq=False)
class RiskEvaluationResult:
    """A structural, traceable representation of a completed Risk evaluation."""

    decision_proposal: DecisionProposal
    outcome: RiskEvaluationOutcome
    basis_reference: str
    conditions: tuple[str, ...]
    semantic_identity: str

    def __init__(
        self,
        decision_proposal: DecisionProposal,
        outcome: RiskEvaluationOutcome,
        basis_reference: str,
        conditions: Iterable[str] = (),
    ) -> None:
        if not isinstance(decision_proposal, DecisionProposal):
            raise InvalidDecisionProposalError(
                "A valid public DecisionProposal is required."
            )
        if not isinstance(outcome, RiskEvaluationOutcome):
            raise InvalidEvaluationOutcomeError(
                "An authorized RiskEvaluationOutcome is required."
            )
        if not isinstance(basis_reference, str) or not basis_reference.strip():
            raise InvalidRiskEvaluationBasisReferenceError(
                "Risk Evaluation Basis Reference must be a non-empty string."
            )

        try:
            supplied_conditions = tuple(conditions)
        except TypeError:
            raise InconsistentRiskConditionsError(
                "Risk conditions must be an iterable of non-empty strings."
            ) from None
        if any(not isinstance(item, str) or not item.strip() for item in supplied_conditions):
            raise InconsistentRiskConditionsError(
                "Risk conditions must be non-empty strings."
            )
        canonical_conditions = tuple(sorted(set(supplied_conditions)))
        if outcome is RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED:
            if not canonical_conditions:
                raise InconsistentRiskConditionsError(
                    "CONDITIONALLY_ACCEPTED requires at least one public Risk condition."
                )
        elif canonical_conditions:
            raise InconsistentRiskConditionsError(
                "Public Risk conditions are valid only for CONDITIONALLY_ACCEPTED."
            )

        object.__setattr__(self, "decision_proposal", decision_proposal)
        object.__setattr__(self, "outcome", outcome)
        object.__setattr__(self, "basis_reference", basis_reference)
        object.__setattr__(self, "conditions", canonical_conditions)
        object.__setattr__(
            self,
            "semantic_identity",
            self._identity_for(
                decision_proposal.semantic_identity,
                outcome,
                basis_reference,
                canonical_conditions,
            ),
        )

    @staticmethod
    def _identity_for(
        proposal_identity: str,
        outcome: RiskEvaluationOutcome,
        basis_reference: str,
        conditions: tuple[str, ...],
    ) -> str:
        canonical = json.dumps(
            {
                "basis_reference": basis_reference,
                "conditions": conditions,
                "decision_proposal": proposal_identity,
                "outcome": outcome.value,
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        return sha256(canonical.encode("utf-8")).hexdigest()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RiskEvaluationResult):
            return NotImplemented
        return self._identity_components == other._identity_components

    def __hash__(self) -> int:
        return hash(self._identity_components)

    @property
    def _identity_components(self) -> tuple[object, ...]:
        return (
            self.decision_proposal,
            self.outcome,
            self.basis_reference,
            self.conditions,
        )
