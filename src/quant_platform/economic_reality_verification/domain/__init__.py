"""Domain API for Economic Reality Verification within CAP-007 Reconciliation."""

from .exceptions import EconomicRealityVerificationDomainError
from .verification import (
    EconomicRealityDimension,
    EconomicRealityVerification,
    EconomicRealityVerificationOutcome,
    EconomicRealityVerificationResult,
    verify_economic_reality,
)

__all__ = [
    "EconomicRealityDimension",
    "EconomicRealityVerification",
    "EconomicRealityVerificationDomainError",
    "EconomicRealityVerificationOutcome",
    "EconomicRealityVerificationResult",
    "verify_economic_reality",
]
