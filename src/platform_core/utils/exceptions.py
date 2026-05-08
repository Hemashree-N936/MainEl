class PlatformError(Exception):
    """Base exception for platform-level failures."""


class ResourceNotFoundError(PlatformError):
    """Raised when a requested resource does not exist."""


class ExternalServiceError(PlatformError):
    """Raised when an external provider request fails."""
