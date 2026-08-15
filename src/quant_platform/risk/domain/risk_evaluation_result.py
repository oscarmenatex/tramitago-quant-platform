"""Immutable public result of a completed Risk evaluation."""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from hashlib import sha256
import json

from quant_platform.decision_model import DecisionProposal

from .exceptions import (
    InconsistentRiskConstraintsError,
    InvalidDecisionProposalError,
    InvalidEvaluationOutcomeError,
    InvalidRiskConstraintError,
    InvalidRiskContextReferenceError,
    InvalidRiskEvaluationBasisReferenceError,
)


class RiskEvaluationOutcome(str, Enum):
    """Authorized outcomes represented by a Risk Evaluation Result."""

    ACCEPTED = "ACCEPTED"
    CONDITIONALLY_ACCEPTED = "CONDITIONALLY_ACCEPTED"
    REJECTED = "REJECTED"


class RiskConstraintKind(str, Enum):
    """Quantitative limits that Risk may impose on a proposal."""

    MAX_CAPITAL = "MAX_CAPITAL"
    MAX_EXPOSURE = "MAX_EXPOSURE"
    MAX_SIZE = "MAX_SIZE"
    MAX_EXECUTION_SIZE = "MAX_EXECUTION_SIZE"


@dataclass(frozen=True, slots=True)
class RiskConstraint:
    """An exact quantitative limit already determined by Risk."""

    kind: RiskConstraintKind
    limit: Decimal
    unit: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, RiskConstraintKind):
            raise InvalidRiskConstraintError(
                "An authorized RiskConstraintKind is required."
            )
        if not isinstance(self.limit, Decimal) or not self.limit.is_finite():
            raise InvalidRiskConstraintError(
                "Risk constraint limit must be an exact, finite Decimal."
            )
        if not isinstance(self.unit, str) or not self.unit.strip():
            raise InvalidRiskConstraintError(
                "Risk constraint unit must be a non-empty string."
            )
        object.__setattr__(self, "unit", self.unit.strip())

    @property
    def _canonical_components(self) -> tuple[str, str, str]:
        return self.kind.value, str(self.limit.normalize()), self.unit


@dataclass(frozen=True, slots=True, init=False, eq=False)
class RiskEvaluationResult:
    """A structural, traceable representation of a completed Risk evaluation."""

    decision_proposal: DecisionProposal
    outcome: RiskEvaluationOutcome
    basis_reference: str
    constraints: tuple[RiskConstraint, ...]
    context_references: tuple[str, ...]
    semantic_identity: str

    def __init__(
        self,
        decision_proposal: DecisionProposal,
        outcome: RiskEvaluationOutcome,
        basis_reference: str,
        constraints: Iterable[RiskConstraint] = (),
        context_references: Iterable[str] = (),
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
            supplied_constraints = tuple(constraints)
        except TypeError:
            raise InvalidRiskConstraintError(
                "Risk constraints must be an iterable of RiskConstraint values."
            ) from None
        if any(not isinstance(item, RiskConstraint) for item in supplied_constraints):
            raise InvalidRiskConstraintError(
                "Risk constraints must contain only RiskConstraint values."
            )
        canonical_constraints = tuple(
            sorted(
                set(supplied_constraints), key=lambda item: item._canonical_components
            )
        )
        if outcome is RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED:
            if not canonical_constraints:
                raise InconsistentRiskConstraintsError(
                    "CONDITIONALLY_ACCEPTED requires at least one RiskConstraint."
                )
        elif canonical_constraints:
            raise InconsistentRiskConstraintsError(
                "Risk constraints are valid only for CONDITIONALLY_ACCEPTED."
            )

        try:
            supplied_context_references = tuple(context_references)
        except TypeError:
            raise InvalidRiskContextReferenceError(
                "Risk context references must be an iterable of public strings."
            ) from None
        if any(
            not isinstance(item, str) or not item.strip()
            for item in supplied_context_references
        ):
            raise InvalidRiskContextReferenceError(
                "Risk context references must be non-empty public strings."
            )
        canonical_context_references = tuple(
            sorted({item.strip() for item in supplied_context_references})
        )

        object.__setattr__(self, "decision_proposal", decision_proposal)
        object.__setattr__(self, "outcome", outcome)
        object.__setattr__(self, "basis_reference", basis_reference)
        object.__setattr__(self, "constraints", canonical_constraints)
        object.__setattr__(self, "context_references", canonical_context_references)
        object.__setattr__(
            self,
            "semantic_identity",
            self._identity_for(
                decision_proposal.semantic_identity,
                outcome,
                basis_reference,
                canonical_constraints,
                canonical_context_references,
            ),
        )

    @staticmethod
    def _identity_for(
        proposal_identity: str,
        outcome: RiskEvaluationOutcome,
        basis_reference: str,
        constraints: tuple[RiskConstraint, ...],
        context_references: tuple[str, ...],
    ) -> str:
        canonical = json.dumps(
            {
                "basis_reference": basis_reference,
                "constraints": [item._canonical_components for item in constraints],
                "context_references": context_references,
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
            self.constraints,
            self.context_references,
        )
