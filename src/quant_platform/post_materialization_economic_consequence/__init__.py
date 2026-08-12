"""Public contract for post-materialization economic consequence."""

from .domain import (
    PostMaterializationEconomicConsequence,
    PostMaterializationEconomicConsequenceDomainError,
    derive_post_materialization_consequence,
)

__all__ = [
    "PostMaterializationEconomicConsequence",
    "derive_post_materialization_consequence",
    "PostMaterializationEconomicConsequenceDomainError",
]
