"""Exceptions raised when Strategy Evaluation domain invariants are violated."""


class StrategyEvaluationDomainError(ValueError):
    """Base exception for violations of Strategy Evaluation domain invariants."""


class InvalidStrategyError(StrategyEvaluationDomainError):
    """Raised when a Strategy definition is invalid."""


class InvalidEvaluationContextError(StrategyEvaluationDomainError):
    """Raised when an EvaluationContext does not describe a valid context."""


class InconsistentStrategyEvaluationError(StrategyEvaluationDomainError):
    """Raised when a StrategyEvaluation cannot be traced consistently."""


class InvalidEvaluationCriteriaError(StrategyEvaluationDomainError):
    """Raised when EvaluationCriteria contains an invalid characterization."""


class InvalidEvaluationIdentityError(StrategyEvaluationDomainError):
    """Raised when an evaluation identifier cannot identify an evaluation."""


class DuplicateStrategyEvaluationError(StrategyEvaluationDomainError):
    """Raised when an evaluation identifier has already been registered."""


class KnowledgeNotFoundError(StrategyEvaluationDomainError):
    """Raised when the requested published Knowledge cannot be resolved."""


class KnowledgeVersionMismatchError(StrategyEvaluationDomainError):
    """Raised when published Knowledge does not have the requested version."""


class InvalidEvaluationInputError(StrategyEvaluationDomainError):
    """Raised when a process input is not a valid domain object."""


class InvalidEvaluationResultError(StrategyEvaluationDomainError):
    """Raised when an evaluator returns an invalid result."""


class StrategyEvaluatorExecutionError(StrategyEvaluationDomainError):
    """Raised when an evaluator cannot complete its calculation."""


class InvalidStrategyEvaluationComparisonError(StrategyEvaluationDomainError):
    """Raised when a StrategyEvaluationComparison violates an invariant."""


class InvalidComparisonResultError(StrategyEvaluationDomainError):
    """Raised when a ComparisonResult is invalid."""


class DuplicateStrategyEvaluationComparisonError(StrategyEvaluationDomainError):
    """Raised when a comparison identifier has already been registered."""


class StrategyEvaluationComparisonNotFoundError(StrategyEvaluationDomainError):
    """Raised when a requested comparison is not registered."""


class InvalidComparisonRequestError(StrategyEvaluationDomainError):
    """Raised when a comparison request violates the service contract."""


class IncompatibleEvaluationContextError(StrategyEvaluationDomainError):
    """Raised when evaluations do not share an EvaluationContext."""


class IncompatibleEvaluationCriteriaError(StrategyEvaluationDomainError):
    """Raised when evaluations do not share EvaluationCriteria."""


class IncompatibleKnowledgeReferenceError(StrategyEvaluationDomainError):
    """Raised when evaluations do not share an exact Knowledge reference."""


class IncompatibleEvaluationResultError(StrategyEvaluationDomainError):
    """Raised when evaluation results cannot be structurally compared."""


class StrategyEvaluationComparisonExecutionError(StrategyEvaluationDomainError):
    """Raised when a comparator cannot complete its calculation."""


class InvalidPublicationLifecycleRecordError(StrategyEvaluationDomainError):
    """Raised when an immutable publication lifecycle record is invalid."""


class DuplicatePublicationLifecycleIdError(StrategyEvaluationDomainError):
    """Raised when a lifecycle identity has already been registered."""


class PublicationLifecycleAlreadyRegisteredError(StrategyEvaluationDomainError):
    """Raised when a publication already has an initial lifecycle record."""


class PublicationLifecycleNotFoundError(StrategyEvaluationDomainError):
    """Raised when a requested publication lifecycle cannot be found."""


class InvalidPublicationLifecycleTransitionError(StrategyEvaluationDomainError):
    """Raised when a lifecycle transition violates the permitted state model."""


class PublicationAlreadySupersededError(InvalidPublicationLifecycleTransitionError):
    """Raised when a superseded publication receives another transition."""


class PublicationAlreadyWithdrawnError(InvalidPublicationLifecycleTransitionError):
    """Raised when a withdrawn publication receives another transition."""


class PublicationSuccessorNotFoundError(StrategyEvaluationDomainError):
    """Raised when the nominated successor publication does not exist."""


class PublicationSuccessorLifecycleNotFoundError(StrategyEvaluationDomainError):
    """Raised when the nominated successor has no registered lifecycle."""


class PublicationSuccessorNotActiveError(InvalidPublicationLifecycleTransitionError):
    """Raised when the nominated successor is not active."""


class PublicationLifecycleCycleError(InvalidPublicationLifecycleTransitionError):
    """Raised when a proposed succession would introduce a lifecycle cycle."""


class InvalidPublishedStrategyEvaluationError(StrategyEvaluationDomainError):
    """Raised when a published evaluation violates its public contract."""


class InvalidPublishedStrategyEvaluationComparisonError(StrategyEvaluationDomainError):
    """Raised when a published comparison violates its public contract."""


class InvalidPublicationRequestError(StrategyEvaluationDomainError):
    """Raised when a publication request is formally invalid."""


class DuplicatePublicationIdError(StrategyEvaluationDomainError):
    """Raised when a public publication identity is already registered."""


class StrategyEvaluationAlreadyPublishedError(StrategyEvaluationDomainError):
    """Raised when an evaluation source has already been published."""


class StrategyEvaluationComparisonAlreadyPublishedError(StrategyEvaluationDomainError):
    """Raised when a comparison source has already been published."""


class PublishedStrategyEvaluationNotFoundError(StrategyEvaluationDomainError):
    """Raised when a published evaluation cannot be found."""


class PublishedStrategyEvaluationComparisonNotFoundError(StrategyEvaluationDomainError):
    """Raised when a published comparison cannot be found."""


class PublicationProjectionError(StrategyEvaluationDomainError):
    """Raised when a source asset cannot be projected as public evidence."""
