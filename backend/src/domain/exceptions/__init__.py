class DomainError(Exception):
    """Base error for domain rule violations."""


class DomainValidationError(DomainError, ValueError):
    """Raised when an entity would be created in an invalid state."""


class EntityNotFoundError(DomainError):
    """Raised when a requested domain entity does not exist."""
