"""Custom exceptions for context operations."""


class ContextException(Exception):
    """Base exception for context operations."""

    pass


class ContextNotFoundException(ContextException):
    """Raised when a context entry is not found."""

    pass


class ContextAlreadyExistsException(ContextException):
    """Raised when attempting to create a duplicate context."""

    pass


class StorageException(ContextException):
    """Raised when storage operations fail."""

    pass