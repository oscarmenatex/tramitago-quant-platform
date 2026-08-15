"""Normative structural errors for the public Risk domain contract."""


class RiskEvaluationResultError(ValueError):
    """Base class for structural Risk Evaluation Result errors."""


class InvalidDecisionProposalError(RiskEvaluationResultError):
    """The evaluated Decision Proposal is absent or invalid."""


class InvalidEvaluationOutcomeError(RiskEvaluationResultError):
    """The evaluation outcome is absent or outside the authorized contract."""


class InvalidRiskConstraintError(RiskEvaluationResultError):
    """A public Risk constraint is structurally invalid."""


class InconsistentRiskConstraintsError(RiskEvaluationResultError):
    """The outcome and public Risk constraints are structurally inconsistent."""


class InvalidRiskEvaluationBasisReferenceError(RiskEvaluationResultError):
    """The Risk Evaluation Basis Reference is absent or invalid."""


class InvalidRiskContextReferenceError(RiskEvaluationResultError):
    """A Risk context reference is absent or structurally invalid."""


__all__ = [
    "InconsistentRiskConstraintsError",
    "InvalidDecisionProposalError",
    "InvalidEvaluationOutcomeError",
    "InvalidRiskConstraintError",
    "InvalidRiskContextReferenceError",
    "InvalidRiskEvaluationBasisReferenceError",
    "RiskEvaluationResultError",
]
