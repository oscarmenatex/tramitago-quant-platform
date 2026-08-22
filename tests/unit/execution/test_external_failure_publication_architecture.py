from pathlib import Path

import quant_platform.execution as execution


def test_exact_it_034_014_public_surface_is_exported() -> None:
    assert {"ExternalFailurePublication", "publish_external_failure"} <= set(
        execution.__all__
    )
    assert execution.ExternalFailurePublication is not None
    assert execution.publish_external_failure is not None


def test_publication_has_no_downstream_or_infrastructure_dependency() -> None:
    source = Path(
        "src/quant_platform/execution/external_failure_publication.py"
    ).read_text(encoding="utf-8")
    forbidden = (
        "quant_platform.research",
        "knowledge",
        "observability",
        "repository",
        "registry",
        "event bus",
        "message queue",
        "transport",
        "delivery",
        "publication_id",
        "published_at",
        "current_publication",
        "latest_publication",
    )
    assert not any(term in source.lower() for term in forbidden)
