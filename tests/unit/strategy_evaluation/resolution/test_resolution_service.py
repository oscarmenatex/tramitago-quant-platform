"""RS-001..RS-028 functional evidence for canonical publication resolution."""

from types import SimpleNamespace

import pytest

from quant_platform.strategy_evaluation import (
    ResolutionContext,
    StrategyEvaluationPublicationResolutionService,
)
from quant_platform.strategy_evaluation.domain.exceptions import (
    AmbiguousPublicationResolutionError,
    PublicationLifecycleNotFoundError,
    PublicationNotFoundError,
    PublicationNotResolvableError,
)
from quant_platform.strategy_evaluation.lifecycle.records import PublicationLifecycleStatus

from .conftest import (
    active_comparison,
    active_evaluation,
    published_comparison,
    published_evaluation,
)


class PublicationAccess:
    def __init__(self, publications=(), error=None):
        self.publications, self.error = tuple(publications), error

    def list(self):
        if self.error is not None:
            raise self.error
        return self.publications


class LifecycleAccess:
    def __init__(self, statuses=(), error=None):
        self.statuses, self.error = dict(statuses), error

    def has_lifecycle(self, publication_id):
        return publication_id in self.statuses

    def get_current(self, publication_id):
        if self.error is not None:
            raise self.error
        return SimpleNamespace(status=self.statuses[publication_id])


def service(
    boundaries,
    evaluation_access=None,
    evaluation_lifecycles=None,
    comparison_access=None,
    comparison_lifecycles=None,
):
    return StrategyEvaluationPublicationResolutionService(
        evaluation_access or boundaries[0], comparison_access or boundaries[1],
        evaluation_lifecycles or boundaries[2], comparison_lifecycles or boundaries[3],
    )


def test_rs_001_002_resolves_active_evaluation_and_comparison(boundaries):
    evaluation = active_evaluation(boundaries[4], boundaries[6])
    comparison = active_comparison(boundaries[5], boundaries[7])
    subject = service(boundaries)
    assert subject.resolve(ResolutionContext.for_evaluation("evaluation-A")).publication is evaluation
    assert subject.resolve(ResolutionContext.for_comparison("comparison-A")).publication is comparison


def test_rs_003_004_raises_normative_not_found_errors(boundaries):
    subject = service(boundaries)
    with pytest.raises(PublicationNotFoundError):
        subject.resolve(ResolutionContext.for_evaluation("missing"))
    publication = published_evaluation("publication-A", "evaluation-A")
    with pytest.raises(PublicationLifecycleNotFoundError):
        service(boundaries, PublicationAccess((publication,)), LifecycleAccess()).resolve(
            ResolutionContext.for_evaluation("evaluation-A")
        )


@pytest.mark.parametrize("status", [PublicationLifecycleStatus.SUPERSEDED, PublicationLifecycleStatus.WITHDRAWN])
def test_rs_005_006_026_027_excludes_terminal_candidates(boundaries, status):
    active = published_evaluation("publication-active", "evaluation-A")
    terminal = published_evaluation("publication-terminal", "evaluation-A")
    subject = service(
        boundaries,
        PublicationAccess((active, terminal)),
        LifecycleAccess({active.publication_id: PublicationLifecycleStatus.ACTIVE, terminal.publication_id: status}),
    )
    assert subject.resolve(ResolutionContext.for_evaluation("evaluation-A")).publication is active


def test_rs_007_024_028_rejects_multiple_active_candidates(boundaries):
    first = published_evaluation("publication-A", "evaluation-A")
    second = published_evaluation("publication-B", "evaluation-A")
    subject = service(
        boundaries, PublicationAccess((first, second)),
        LifecycleAccess({first.publication_id: PublicationLifecycleStatus.ACTIVE, second.publication_id: PublicationLifecycleStatus.ACTIVE}),
    )
    with pytest.raises(AmbiguousPublicationResolutionError):
        subject.resolve(ResolutionContext.for_evaluation("evaluation-A"))


def test_rs_023_024_rejects_candidates_without_active_lifecycle(boundaries):
    publication = published_evaluation("publication-A", "evaluation-A")
    subject = service(
        boundaries, PublicationAccess((publication,)),
        LifecycleAccess({publication.publication_id: PublicationLifecycleStatus.WITHDRAWN}),
    )
    with pytest.raises(PublicationNotResolvableError):
        subject.resolve(ResolutionContext.for_evaluation("evaluation-A"))


def test_rs_008_009_010_011_012_020_021_022_025_are_deterministic_and_read_only(boundaries):
    publication = active_evaluation(boundaries[4], boundaries[6])
    subject = service(boundaries)
    context = ResolutionContext.for_evaluation("evaluation-A")
    before = (boundaries[4].list(), boundaries[6].list())
    first, second = subject.resolve(context), subject.resolve(ResolutionContext.for_evaluation("evaluation-A"))
    assert first == second and first.publication is publication
    assert (boundaries[4].list(), boundaries[6].list()) == before
    with pytest.raises(TypeError):
        subject.resolve(object())


def test_rs_019_propagates_unexpected_access_errors(boundaries):
    error = RuntimeError("access failed")
    with pytest.raises(RuntimeError) as raised:
        service(boundaries, PublicationAccess(error=error)).resolve(
            ResolutionContext.for_evaluation("evaluation-A")
        )
    assert raised.value is error


@pytest.mark.parametrize(
    ("kind", "factory", "context", "access_slot", "lifecycle_slot"),
    [
        ("evaluation", published_evaluation, ResolutionContext.for_evaluation, "evaluation", "evaluation"),
        ("comparison", published_comparison, ResolutionContext.for_comparison, "comparison", "comparison"),
    ],
)
def test_comparison_and_evaluation_cover_lifecycle_cardinality_and_state(
    boundaries, kind, factory, context, access_slot, lifecycle_slot
):
    active = factory("publication-active", "source-A")
    terminal = factory("publication-terminal", "source-A")
    overrides = {
        f"{access_slot}_access": PublicationAccess((active, terminal)),
        f"{lifecycle_slot}_lifecycles": LifecycleAccess(
            {
                active.publication_id: PublicationLifecycleStatus.ACTIVE,
                terminal.publication_id: PublicationLifecycleStatus.SUPERSEDED,
            }
        ),
    }
    subject = service(boundaries, **overrides)
    before = tuple(access.list() for access in boundaries[:4])
    result = subject.resolve(context("source-A"))
    assert result.publication is active
    assert tuple(access.list() for access in boundaries[:4]) == before
    assert subject.resolve(context("source-A")) == result


@pytest.mark.parametrize(
    ("factory", "context", "access_slot", "lifecycle_slot"),
    [
        (published_evaluation, ResolutionContext.for_evaluation, "evaluation", "evaluation"),
        (published_comparison, ResolutionContext.for_comparison, "comparison", "comparison"),
    ],
)
def test_both_kinds_have_complete_error_cardinality_evidence(
    boundaries, factory, context, access_slot, lifecycle_slot
):
    candidate = factory("publication-A", "source-A")
    inactive = LifecycleAccess({candidate.publication_id: PublicationLifecycleStatus.WITHDRAWN})
    missing = LifecycleAccess()
    duplicate = factory("publication-B", "source-A")
    for lifecycle, expected in (
        (missing, PublicationLifecycleNotFoundError),
        (inactive, PublicationNotResolvableError),
    ):
        subject = service(
            boundaries,
            **{
                f"{access_slot}_access": PublicationAccess((candidate,)),
                f"{lifecycle_slot}_lifecycles": lifecycle,
            },
        )
        before = tuple(access.list() for access in boundaries[:4])
        with pytest.raises(expected):
            subject.resolve(context("source-A"))
        assert tuple(access.list() for access in boundaries[:4]) == before
    ambiguous = service(
        boundaries,
        **{
            f"{access_slot}_access": PublicationAccess((candidate, duplicate)),
            f"{lifecycle_slot}_lifecycles": LifecycleAccess(
                {
                    candidate.publication_id: PublicationLifecycleStatus.ACTIVE,
                    duplicate.publication_id: PublicationLifecycleStatus.ACTIVE,
                }
            ),
        },
    )
    with pytest.raises(AmbiguousPublicationResolutionError):
        ambiguous.resolve(context("source-A"))


@pytest.mark.parametrize("access_kind", ["evaluation-publication", "comparison-publication", "evaluation-lifecycle", "comparison-lifecycle"])
def test_rs_019_propagates_each_authorized_access_error_unchanged(boundaries, access_kind):
    error = RuntimeError(f"{access_kind} failed")
    publication = published_evaluation("publication-A", "source-A")
    kwargs = {}
    context = ResolutionContext.for_evaluation("source-A")
    if access_kind == "evaluation-publication":
        kwargs["evaluation_access"] = PublicationAccess(error=error)
    elif access_kind == "comparison-publication":
        context = ResolutionContext.for_comparison("source-A")
        kwargs["comparison_access"] = PublicationAccess(error=error)
    elif access_kind == "evaluation-lifecycle":
        kwargs["evaluation_access"] = PublicationAccess((publication,))
        kwargs["evaluation_lifecycles"] = LifecycleAccess(
            {publication.publication_id: PublicationLifecycleStatus.ACTIVE}, error
        )
    else:
        publication = published_comparison("publication-A", "source-A")
        context = ResolutionContext.for_comparison("source-A")
        kwargs["comparison_access"] = PublicationAccess((publication,))
        kwargs["comparison_lifecycles"] = LifecycleAccess(
            {publication.publication_id: PublicationLifecycleStatus.ACTIVE}, error
        )
    before = tuple(access.list() for access in boundaries[:4])
    with pytest.raises(RuntimeError) as raised:
        service(boundaries, **kwargs).resolve(context)
    assert raised.value is error and str(raised.value) == str(error)
    assert tuple(access.list() for access in boundaries[:4]) == before
