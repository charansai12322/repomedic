"""Custom exception hierarchy for RepoMedic."""

from typing import Optional


class RepoMedicError(Exception):
    """Base exception for all RepoMedic errors."""

    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR", details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ValidationError(RepoMedicError):
    """Raised when client input or configuration fails validation."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, error_code="VALIDATION_ERROR", details=details)


class ScanError(RepoMedicError):
    """Raised when repository cloning, extraction, or scanning encounters a fatal error."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, error_code="SCAN_ERROR", details=details)



class InvalidTargetError(ValidationError):
    """Raised when a repository URL or target is invalid, malformed, or rejected (e.g. SSRF)."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, details=details)
        self.error_code = "INVALID_TARGET_URL"


class ResourceLimitExceededError(RepoMedicError):
    """Raised when repository size, file count, or execution timeouts exceed safety boundaries."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, error_code="RESOURCE_LIMIT_EXCEEDED", details=details)


class ScannerExecutionError(RepoMedicError):
    """Raised when a required scanner encounters an unrecoverable runtime failure."""

    def __init__(self, scanner_name: str, message: str, details: Optional[dict] = None):
        super().__init__(f"Scanner '{scanner_name}' failed: {message}", error_code="SCANNER_EXECUTION_FAILED", details=details)
        self.scanner_name = scanner_name


class AIProviderError(RepoMedicError):
    """Raised when AI inference or model discovery fails."""

    def __init__(self, message: str, error_code: str = "AI_PROVIDER_ERROR", details: Optional[dict] = None):
        super().__init__(message, error_code=error_code, details=details)


class AuthenticationError(RepoMedicError):
    """Raised when API authentication fails."""

    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message, error_code="AUTHENTICATION_FAILED")


class JobNotFoundError(RepoMedicError):
    """Raised when a requested scan job ID does not exist."""

    def __init__(self, job_id: str):
        super().__init__(f"Scan job '{job_id}' not found.", error_code="JOB_NOT_FOUND", details={"job_id": job_id})
        self.job_id = job_id


class QueueFullError(RepoMedicError):
    """Raised when the asynchronous scan job queue is at maximum capacity."""

    def __init__(self, message: str = "Scan queue is full. Please retry shortly."):
        super().__init__(message, error_code="QUEUE_FULL")
