"""Public errors raised by the Operational Submission capability."""


class OperationalSubmissionDomainError(RuntimeError):
    """The Operational Submission contract could not be satisfied."""


__all__ = ["OperationalSubmissionDomainError"]
