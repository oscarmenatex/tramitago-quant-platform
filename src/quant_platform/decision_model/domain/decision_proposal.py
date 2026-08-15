"""Immutable public Decision Proposal domain contracts."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json

from quant_platform.core import InstrumentReference
from quant_platform.strategy_evaluation.resolution import ResolutionResult


class ExposureOrientation(str, Enum):
    """Economic exposure orientations; these are not execution instructions."""

    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    FLAT = "FLAT"


@dataclass(frozen=True, slots=True)
class EconomicProposition:
    """A structured economic subject and exposure orientation."""

    instrument: InstrumentReference
    exposure_orientation: ExposureOrientation

    def __post_init__(self) -> None:
        if not isinstance(self.instrument, InstrumentReference):
            raise TypeError("A public InstrumentReference is required.")
        if not isinstance(self.exposure_orientation, ExposureOrientation):
            raise TypeError("An authorized ExposureOrientation is required.")

    @property
    def semantic_identity(self) -> str:
        canonical = json.dumps(
            {
                "exposure_orientation": self.exposure_orientation.value,
                "instrument": self.instrument.semantic_identity,
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        return sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True, init=False, eq=False)
class DecisionProposal:
    """A structured economic proposition backed by resolved public evidence."""

    economic_proposition: EconomicProposition
    evidence_references: tuple[str, ...]
    semantic_identity: str

    @classmethod
    def from_resolutions(
        cls,
        economic_proposition: EconomicProposition,
        resolutions: Iterable[ResolutionResult],
    ) -> "DecisionProposal":
        """Construct one proposal from an explicit proposition and evidence."""
        if not isinstance(economic_proposition, EconomicProposition):
            raise TypeError("A valid EconomicProposition is required.")

        resolved_evidence = tuple(resolutions)
        if not resolved_evidence:
            raise ValueError("A Decision Proposal requires public resolved evidence.")
        if any(not isinstance(item, ResolutionResult) for item in resolved_evidence):
            raise TypeError(
                "Evidence must consist exclusively of ResolutionResult values."
            )

        evidence_references = tuple(
            sorted(item.publication_id for item in resolved_evidence)
        )
        if len(set(evidence_references)) != len(evidence_references):
            raise ValueError("Public evidence references must be unique.")

        proposal = object.__new__(cls)
        object.__setattr__(proposal, "economic_proposition", economic_proposition)
        object.__setattr__(proposal, "evidence_references", evidence_references)
        object.__setattr__(
            proposal,
            "semantic_identity",
            cls._identity_for(economic_proposition, evidence_references),
        )
        return proposal

    @staticmethod
    def _identity_for(
        economic_proposition: EconomicProposition,
        evidence_references: tuple[str, ...],
    ) -> str:
        canonical_representation = json.dumps(
            {
                "economic_proposition": economic_proposition.semantic_identity,
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
        return self._identity_components == other._identity_components

    def __hash__(self) -> int:
        return hash(self._identity_components)

    @property
    def _identity_components(self) -> tuple[object, ...]:
        return self.economic_proposition, self.evidence_references
