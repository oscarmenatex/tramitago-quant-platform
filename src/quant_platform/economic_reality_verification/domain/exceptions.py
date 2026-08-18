"""Public incompatibility for CAP-007 Reconciliation reality verification."""


class EconomicRealityVerificationDomainError(ValueError):
    """The supplied realities cannot constitute a valid verification."""
