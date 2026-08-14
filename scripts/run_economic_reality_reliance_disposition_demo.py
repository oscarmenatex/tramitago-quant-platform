"""Deterministic public demonstration for IT-045-001."""

from run_post_verification_qualification_demo import scope_for, verification

from quant_platform.economic_reality_reliance_disposition import (
    EconomicRealityRelianceAuthority,
    EconomicRealityRelianceOutcome as Outcome,
    dispose_economic_reality_reliance,
)
from quant_platform.post_verification_qualification import (
    PostVerificationQualificationCondition as Condition,
    qualify_post_verification,
)


qualification = qualify_post_verification(
    verification,
    scope_for(
        next(
            result.identity
            for result in verification.position_results
            if result.outcome.value == "AGREEMENT"
        )
    ),
)
permitting = EconomicRealityRelianceAuthority(
    {Condition.CORROBORATED: Outcome.RELIANCE_PERMITTED}
)
prohibiting = EconomicRealityRelianceAuthority(
    {Condition.CORROBORATED: Outcome.RELIANCE_PROHIBITED}
)
permitted = dispose_economic_reality_reliance(qualification, permitting)
prohibited = dispose_economic_reality_reliance(qualification, prohibiting)

assert qualification.condition is Condition.CORROBORATED
assert permitted.qualification is prohibited.qualification is qualification
assert permitted.authority is permitting and prohibited.authority is prohibiting
assert permitted.outcome is Outcome.RELIANCE_PERMITTED
assert prohibited.outcome is Outcome.RELIANCE_PROHIBITED
print("PostVerificationQualification + EconomicRealityRelianceAuthority")
print("Outcomes:", permitted.outcome.value, prohibited.outcome.value)
print("Qualification preserved: PASS")
print("Authority preserved: PASS")
print("Economic Reality Reliance Disposition demo: PASS")
