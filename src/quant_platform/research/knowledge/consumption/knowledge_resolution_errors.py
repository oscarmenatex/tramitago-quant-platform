"""Domain errors for exact public Knowledge version resolution."""


class KnowledgeResolutionError(ValueError):
    """Base error for public Knowledge version resolution."""


class InvalidKnowledgeIdentifierError(KnowledgeResolutionError):
    """Raised when a lineage identifier is not a non-empty string."""


class InvalidKnowledgeVersionError(KnowledgeResolutionError):
    """Raised when a version label is not a non-empty string."""


class KnowledgeLineageNotFoundError(KnowledgeResolutionError):
    """Raised when no published version belongs to the requested lineage."""


class KnowledgeVersionNotFoundError(KnowledgeResolutionError):
    """Raised when a lineage does not contain the requested version."""


class KnowledgeVersionNotConsumableError(KnowledgeResolutionError):
    """Raised when an exact version is not published for consumption."""


class AmbiguousKnowledgeVersionError(KnowledgeResolutionError):
    """Raised when a lineage/version pair maps to multiple versions."""
