"""Normative structural errors for the public Risk domain contract."""


class RiskEvaluationResultError(ValueError):
    """Base class for structural Risk Evaluation Result errors."""


class InvalidDecisionProposalError(RiskEvaluationResultError):
    """The evaluated Decision Proposal is absent or invalid."""


class InvalidEvaluationOutcomeError(RiskEvaluationResultError):
    """The evaluation outcome is absent or outside the authorized contract."""


class InconsistentRiskConditionsError(RiskEvaluationResultError):
    """The outcome and public Risk conditions are structurally inconsistent."""


class InvalidRiskEvaluationBasisReferenceError(RiskEvaluationResultError):
    """The Risk Evaluation Basis Reference is absent or invalid."""


__all__ = [
    "InconsistentRiskConditionsError",
    "InvalidDecisionProposalError",
    "InvalidEvaluationOutcomeError",
    "InvalidRiskEvaluationBasisReferenceError",
    "RiskEvaluationResultError",
]
