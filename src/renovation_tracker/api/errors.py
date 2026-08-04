"""Domain-specific exception hierarchy."""

class DomainError(Exception):
    """Base class for all application-specific errors.
    """
    error_code: str = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    """Raised when a requested resource does not exist."""
    error_code = "not_found"


class ValidationError(DomainError):
    """Raised for business-rule validation failures not caught by Pydantic.
    """
    error_code = "validation_error"


class ConflictError(DomainError):
    """Raised when a request conflicts with the current state of a resource.
    """
    error_code = "conflict"