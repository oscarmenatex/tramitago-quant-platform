"""Publication of an external failure and its capital-protection qualification."""

from dataclasses import dataclass

from .capital_protection import ExternalFailureCapitalProtectionQualification
from .domain import ExecutionDomainError
from .external_failure import ExternalFailure


@dataclass(frozen=True, slots=True, init=False)
class ExternalFailurePublication:
    """Immutable public pairing of one failure and its qualification."""

    external_failure: ExternalFailure
    capital_protection_qualification: ExternalFailureCapitalProtectionQualification

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise ExecutionDomainError(
            "ExternalFailurePublication must be produced by publish_external_failure."
        )

    @classmethod
    def _create(
        cls,
        external_failure: ExternalFailure,
        capital_protection_qualification: (
            ExternalFailureCapitalProtectionQualification
        ),
    ) -> "ExternalFailurePublication":
        publication = object.__new__(cls)
        object.__setattr__(publication, "external_failure", external_failure)
        object.__setattr__(
            publication,
            "capital_protection_qualification",
            capital_protection_qualification,
        )
        return publication


def publish_external_failure(
    external_failure: ExternalFailure,
    capital_protection_qualification: ExternalFailureCapitalProtectionQualification,
) -> ExternalFailurePublication:
    """Constitute one corresponding failure and qualification for publication."""
    if not isinstance(external_failure, ExternalFailure):
        raise ExecutionDomainError(
            "External failure publication requires an ExternalFailure."
        )
    if not isinstance(
        capital_protection_qualification,
        ExternalFailureCapitalProtectionQualification,
    ):
        raise ExecutionDomainError(
            "External failure publication requires an "
            "ExternalFailureCapitalProtectionQualification."
        )
    if capital_protection_qualification.external_failure is not external_failure:
        raise ExecutionDomainError(
            "External failure publication requires the qualification to reference "
            "the exact supplied ExternalFailure instance."
        )
    return ExternalFailurePublication._create(
        external_failure, capital_protection_qualification
    )


__all__ = ["ExternalFailurePublication", "publish_external_failure"]
