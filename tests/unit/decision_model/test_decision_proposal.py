"""Normative evidence for IT-029-001/002 v1.1."""

from dataclasses import FrozenInstanceError

import pytest

from quant_platform.core import InstrumentReference
from quant_platform.decision_model import (
    DecisionProposal,
    EconomicProposition,
    ExposureOrientation,
)
from quant_platform.strategy_evaluation.resolution import ResolutionResult


class PublicPublication:
    """Minimal public projection fixture; no Strategy Evaluation internals."""

    def __init__(self, publication_id: str) -> None:
        self.publication_id = publication_id


def resolution(publication_id: str) -> ResolutionResult:
    result = object.__new__(ResolutionResult)
    object.__setattr__(result, "publication", PublicPublication(publication_id))
    return result


def proposition(
    value: str = "BBG000B9XRY4",
    orientation: ExposureOrientation = ExposureOrientation.POSITIVE,
) -> EconomicProposition:
    return EconomicProposition(InstrumentReference("FIGI", value), orientation)


def proposal(
    *evidence_ids: str,
    economic_proposition: EconomicProposition | None = None,
) -> DecisionProposal:
    return DecisionProposal.from_resolutions(
        economic_proposition or proposition(),
        tuple(resolution(item) for item in evidence_ids),
    )


@pytest.mark.parametrize("orientation", list(ExposureOrientation))
def test_economic_proposition_accepts_each_authorized_orientation(
    orientation: ExposureOrientation,
) -> None:
    created = proposition(orientation=orientation)

    assert created.instrument == InstrumentReference("FIGI", "BBG000B9XRY4")
    assert created.exposure_orientation is orientation


@pytest.mark.parametrize(
    ("instrument", "orientation"),
    [
        (None, ExposureOrientation.POSITIVE),
        (InstrumentReference("FIGI", "A"), None),
        (InstrumentReference("FIGI", "A"), "POSITIVE"),
    ],
)
def test_economic_proposition_requires_public_structured_values(
    instrument: object, orientation: object
) -> None:
    with pytest.raises(TypeError):
        EconomicProposition(instrument, orientation)  # type: ignore[arg-type]


def test_economic_proposition_is_immutable() -> None:
    created = proposition()

    with pytest.raises(FrozenInstanceError):
        created.exposure_orientation = ExposureOrientation.FLAT  # type: ignore[misc]


def test_construction_preserves_explicit_proposition_and_public_evidence() -> None:
    supplied = proposition(orientation=ExposureOrientation.NEGATIVE)
    created = proposal("resolution-b", "resolution-a", economic_proposition=supplied)

    assert created.economic_proposition is supplied
    assert created.economic_proposition.instrument is supplied.instrument
    assert (
        created.economic_proposition.exposure_orientation
        is ExposureOrientation.NEGATIVE
    )
    assert created.evidence_references == ("resolution-a", "resolution-b")


def test_equivalent_inputs_are_equal_hashable_and_reproducible() -> None:
    first = proposal("resolution-b", "resolution-a")
    second = proposal("resolution-a", "resolution-b")

    assert first == second
    assert hash(first) == hash(second)
    assert first.semantic_identity == second.semantic_identity


def test_identity_changes_with_instrument_orientation_or_evidence() -> None:
    baseline = proposal("resolution-a")

    assert baseline != proposal(
        "resolution-a", economic_proposition=proposition("DIFFERENT")
    )
    assert baseline != proposal(
        "resolution-a",
        economic_proposition=proposition(orientation=ExposureOrientation.NEGATIVE),
    )
    assert baseline != proposal("resolution-b")


def test_proposal_is_immutable() -> None:
    created = proposal("resolution-a")

    with pytest.raises(FrozenInstanceError):
        created.economic_proposition = proposition(orientation=ExposureOrientation.FLAT)  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        created.evidence_references = ()  # type: ignore[misc]


def test_construction_requires_explicit_economic_proposition() -> None:
    with pytest.raises(TypeError):
        DecisionProposal.from_resolutions(None, (resolution("resolution-a"),))  # type: ignore[arg-type]


def test_construction_requires_one_or_more_resolutions() -> None:
    with pytest.raises(ValueError):
        DecisionProposal.from_resolutions(proposition(), ())


def test_construction_rejects_evidence_outside_public_contract() -> None:
    with pytest.raises(TypeError):
        DecisionProposal.from_resolutions(proposition(), (object(),))  # type: ignore[arg-type]


def test_construction_rejects_duplicate_evidence_atomically() -> None:
    with pytest.raises(ValueError):
        proposal("resolution-a", "resolution-a")


def test_construction_does_not_derive_or_replace_proposition() -> None:
    supplied = proposition(orientation=ExposureOrientation.FLAT)
    evidence = resolution("signal:buy")

    created = DecisionProposal.from_resolutions(supplied, (evidence,))

    assert created.economic_proposition is supplied
    assert created.economic_proposition.exposure_orientation is ExposureOrientation.FLAT
