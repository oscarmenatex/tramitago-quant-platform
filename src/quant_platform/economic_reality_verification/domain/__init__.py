"""Economic Reality Verification domain API."""

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
