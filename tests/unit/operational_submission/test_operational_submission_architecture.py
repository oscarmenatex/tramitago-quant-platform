from pathlib import Path

import quant_platform.operational_submission as operational_submission
from quant_platform.operational_request import OperationalRequest
from quant_platform.operational_submission import OperationalSubmission


def test_public_api_is_limited_to_authorized_contracts() -> None:
    assert operational_submission.__all__ == [
        "OperationalSubmission",
        "submit",
        "OperationalPresentationBoundary",
        "OperationalSubmissionDomainError",
    ]


def test_submission_reuses_operational_request_contract() -> None:
    assert (
        OperationalSubmission.__annotations__["operational_request"]
        is OperationalRequest
    )


def test_dependency_direction_and_infrastructure_independence() -> None:
    root = Path("src/quant_platform/operational_submission")
    paths = tuple(root.rglob("*"))
    forbidden_names = {
        "adapter",
        "adapters",
        "broker",
        "gateway",
        "infrastructure",
        "persistence",
        "repository",
        "transport",
    }
    assert not any(path.name.lower() in forbidden_names for path in paths)

    source = "\n".join(
        path.read_text(encoding="utf-8") for path in paths if path.suffix == ".py"
    )
    forbidden_dependencies = (
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
        "quant_platform.data",
        "quant_platform.execution",
        "quant_platform.portfolio",
        "quant_platform.portfolio_transition",
        "quant_platform.risk",
    )
    assert not any(dependency in source for dependency in forbidden_dependencies)

    request_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("src/quant_platform/operational_request").rglob("*.py")
    )
    assert "quant_platform.operational_submission" not in request_source
