"""Immutable input contract for public publication resolution."""

from dataclasses import dataclass
from enum import StrEnum

from quant_platform.strategy_evaluation.domain.exceptions import (
    InvalidResolutionContextError,
)


class PublicationResolutionKind(StrEnum):
    """The only public publication families that can be resolved."""

    EVALUATION = "evaluation"
    COMPARISON = "comparison"


@dataclass(frozen=True, slots=True)
class ResolutionContext:
    """An immutable, source-only request for exactly one publication.

    ``source_id`` is the public identifier for an evaluation or comparison; it is deliberately
    not a publication or lifecycle reference.  The publication kind makes the request
    unambiguous even if the two source namespaces use the same identifier.
    """

    source_id: str
    publication_kind: PublicationResolutionKind

    def __post_init__(self) -> None:
        for label, value in (
            ("Resolution source identity", self.source_id),
        ):
            if not isinstance(value, str) or not value.strip():
                raise InvalidResolutionContextError(
                    f"{label} must be a non-empty string."
                )
        if not isinstance(self.publication_kind, PublicationResolutionKind):
            raise InvalidResolutionContextError(
                "Publication kind must be a PublicationResolutionKind."
            )

    @classmethod
    def for_evaluation(cls, evaluation_id: str) -> "ResolutionContext":
        """Create a request for a published strategy evaluation."""
        return cls(evaluation_id, PublicationResolutionKind.EVALUATION)

    @classmethod
    def for_comparison(cls, comparison_id: str) -> "ResolutionContext":
        """Create a request for a published strategy evaluation comparison."""
        return cls(comparison_id, PublicationResolutionKind.COMPARISON)
