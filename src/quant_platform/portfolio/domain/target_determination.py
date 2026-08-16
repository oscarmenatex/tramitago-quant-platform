"""Public Portfolio Target Determination action and authority contract."""

from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from quant_platform.decision_model import ExposureOrientation
from quant_platform.risk import (
    RiskConstraint,
    RiskConstraintKind,
    RiskEvaluationOutcome,
    RiskEvaluationResult,
)

from .exceptions import (
    InvalidPortfolioTargetAuthorityError,
    InvalidPortfolioTargetCompositionError,
    InvalidPortfolioTargetInputError,
)
from .portfolio_state import MonetaryBalance, PortfolioPosition, PortfolioState

TargetComposition = tuple[
    Iterable[PortfolioPosition],
    Iterable[MonetaryBalance],
    Iterable[RiskEvaluationResult],
]


@runtime_checkable
class PortfolioTargetDeterminationAuthority(Protocol):
    basis_reference: str

    def determine(
        self,
        current_portfolio_state: PortfolioState,
        risk_evaluation_results: tuple[RiskEvaluationResult, ...],
    ) -> TargetComposition: ...

    def is_constraint_satisfied(
        self,
        constraint: RiskConstraint,
        target_portfolio_state: PortfolioState,
        risk_evaluation_result: RiskEvaluationResult,
    ) -> bool: ...


def _quantities(state: PortfolioState) -> dict[object, object]:
    return {item.instrument: item.quantity for item in state.positions}


def determine_target_portfolio(
    current_portfolio_state: PortfolioState,
    risk_evaluation_results: Iterable[RiskEvaluationResult],
    authority: PortfolioTargetDeterminationAuthority,
) -> PortfolioState:
    """Produce exactly one new validated Target PortfolioState."""
    if not isinstance(current_portfolio_state, PortfolioState):
        raise InvalidPortfolioTargetInputError(
            "A valid current PortfolioState is required."
        )
    try:
        candidates = tuple(risk_evaluation_results)
    except TypeError:
        raise InvalidPortfolioTargetInputError(
            "Risk candidates must be a finite iterable."
        ) from None
    if not candidates or any(
        not isinstance(x, RiskEvaluationResult) for x in candidates
    ):
        raise InvalidPortfolioTargetInputError(
            "One or more public Risk candidates are required."
        )
    if len(set(candidates)) != len(candidates):
        raise InvalidPortfolioTargetInputError("Risk candidates must be unique.")
    if any(x.outcome is RiskEvaluationOutcome.REJECTED for x in candidates):
        raise InvalidPortfolioTargetInputError("REJECTED Risk candidates are invalid.")
    if not isinstance(authority, PortfolioTargetDeterminationAuthority):
        raise InvalidPortfolioTargetAuthorityError(
            "A valid determination authority is required."
        )
    if (
        not isinstance(authority.basis_reference, str)
        or not authority.basis_reference.strip()
    ):
        raise InvalidPortfolioTargetAuthorityError(
            "Authority basis_reference must be non-empty."
        )
    considered = tuple(sorted(candidates, key=lambda x: x.semantic_identity))
    try:
        positions, balances, selected = authority.determine(
            current_portfolio_state, considered
        )
        contributors = tuple(selected)
        economic_target = PortfolioState(positions, balances)
    except Exception as error:
        raise InvalidPortfolioTargetCompositionError(
            "Authority failed to produce a valid composition."
        ) from error
    if any(not isinstance(x, RiskEvaluationResult) for x in contributors):
        raise InvalidPortfolioTargetCompositionError(
            "Contributors must be public Risk results."
        )
    if len(set(contributors)) != len(contributors) or not set(contributors).issubset(
        set(considered)
    ):
        raise InvalidPortfolioTargetCompositionError(
            "Contributors must be unique considered candidates."
        )
    instruments = [
        x.decision_proposal.economic_proposition.instrument for x in contributors
    ]
    if len(set(instruments)) != len(instruments):
        raise InvalidPortfolioTargetCompositionError(
            "Only one contributor per instrument is allowed."
        )
    current = _quantities(current_portfolio_state)
    target = _quantities(economic_target)
    for instrument in set(current) | set(target):
        if current.get(instrument) != target.get(instrument) and instrument not in set(
            instruments
        ):
            raise InvalidPortfolioTargetCompositionError(
                "Every position change requires a contributor."
            )
    for result in contributors:
        proposition = result.decision_proposal.economic_proposition
        quantity = target.get(proposition.instrument)
        orientation = proposition.exposure_orientation
        if (
            orientation is ExposureOrientation.POSITIVE
            and quantity is not None
            and quantity < 0
        ):
            raise InvalidPortfolioTargetCompositionError(
                "POSITIVE cannot produce negative exposure."
            )
        if (
            orientation is ExposureOrientation.NEGATIVE
            and quantity is not None
            and quantity > 0
        ):
            raise InvalidPortfolioTargetCompositionError(
                "NEGATIVE cannot produce positive exposure."
            )
        if orientation is ExposureOrientation.FLAT and quantity is not None:
            raise InvalidPortfolioTargetCompositionError(
                "FLAT requires no material position."
            )
        for constraint in result.constraints:
            if constraint.kind is RiskConstraintKind.MAX_EXECUTION_SIZE:
                continue
            try:
                satisfied = authority.is_constraint_satisfied(
                    constraint, economic_target, result
                )
            except Exception as error:
                raise InvalidPortfolioTargetCompositionError(
                    "A RiskConstraint could not be interpreted."
                ) from error
            if satisfied is not True:
                raise InvalidPortfolioTargetCompositionError(
                    "A RiskConstraint is unsupported or not satisfied."
                )
    return PortfolioState(
        economic_target.positions,
        economic_target.monetary_balances,
        current_portfolio_state=current_portfolio_state,
        considered_risk_evaluation_results=considered,
        contributing_risk_evaluation_results=contributors,
        determination_basis_reference=authority.basis_reference,
    )
