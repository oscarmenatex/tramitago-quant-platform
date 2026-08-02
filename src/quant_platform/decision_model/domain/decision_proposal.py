"""The immutable public Decision Proposal domain asset."""

from collections.abc import Iterable
from dataclasses import dataclass
from hashlib import sha256
import json

from quant_platform.strategy_evaluation.resolution import ResolutionResult


@dataclass(frozen=True, slots=True, init=False, eq=False)
class DecisionProposal:
    """A possible decision, traceable only to resolved public evidence.

    This asset deliberately stores public publication references rather than a
    Resolution result or any Strategy Evaluation implementation object.  Its
    semantic identity is derived solely from its decision intent and its
    canonical, order-independent evidence references.
    """

    decision_intent: str
    evidence_references: tuple[str, ...]
    semantic_identity: str

    @classmethod
    def from_resolutions(
        cls,
        decision_intent: str,
        resolutions: Iterable[ResolutionResult],
    ) -> "DecisionProposal":
        """Build a proposal from the authorized public Resolution contract.

        No resolution is performed here: callers provide evidence that has
        already been resolved by Strategy Evaluation.
        """
        if not isinstance(decision_intent, str) or not decision_intent.strip():
            raise ValueError("Decision intent must be a non-empty string.")

        resolved_evidence = tuple(resolutions)
        if not resolved_evidence:
            raise ValueError("A Decision Proposal requires public resolved evidence.")
        if any(not isinstance(item, ResolutionResult) for item in resolved_evidence):
            raise TypeError("Evidence must consist exclusively of ResolutionResult values.")

        evidence_references = tuple(sorted(item.publication_id for item in resolved_evidence))
        if len(set(evidence_references)) != len(evidence_references):
            raise ValueError("Public evidence references must be unique.")

        proposal = object.__new__(cls)
        object.__setattr__(proposal, "decision_intent", decision_intent)
        object.__setattr__(proposal, "evidence_references", evidence_references)
        object.__setattr__(
            proposal,
            "semantic_identity",
            cls._identity_for(decision_intent, evidence_references),
        )
        return proposal

    @staticmethod
    def _identity_for(decision_intent: str, evidence_references: tuple[str, ...]) -> str:
        canonical_representation = json.dumps(
            {
                "decision_intent": decision_intent,
                "evidence_references": evidence_references,
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        return sha256(canonical_representation.encode("utf-8")).hexdigest()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DecisionProposal):
            return NotImplemented
        return (
            self.decision_intent,
            self.evidence_references,
        ) == (
            other.decision_intent,
            other.evidence_references,
        )

    def __hash__(self) -> int:
        return hash((self.decision_intent, self.evidence_references))
