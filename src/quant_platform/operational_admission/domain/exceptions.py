"""Public error raised during operational admission recognition."""


class OperationalAdmissionDomainError(RuntimeError):
    """The Operational Admission contract could not be satisfied."""


__all__ = ["OperationalAdmissionDomainError"]
