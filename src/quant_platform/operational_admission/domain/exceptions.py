"""Public error raised by the Operational Admission capability."""


class OperationalAdmissionDomainError(RuntimeError):
    """The Operational Admission contract could not be satisfied."""


__all__ = ["OperationalAdmissionDomainError"]
