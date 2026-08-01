"""Deterministic local demonstration of exact historical Knowledge resolution."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.unit.test_knowledge_version_resolution import access


def main() -> None:
    consumption = access()
    for version in ("1", "2"):
        record = consumption.resolve("K-001", version)
        print(f"K-001/{version} -> {record.knowledge_version_id}")


if __name__ == "__main__":
    main()
