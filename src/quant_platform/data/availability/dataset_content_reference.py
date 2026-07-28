"""Reference to dataset content for availability."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetContentReference:
    """A resolvable reference for dataset content."""

    dataset_id: str
    version: str
    content_id: str
