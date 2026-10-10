"""AI-specific error categories and exceptions."""

from typing import Any, Dict, Optional
from app.core.exceptions import AIProviderError


class AIAuthenticationError(AIProviderError):
    def __init__(self, message: str = "AI service authentication failed. Please verify API key configuration.") -> None:
        super().__init__(message=message, status_code=502, code="AI_AUTH_ERROR")


class AIRateLimitError(AIProviderError):
    def __init__(self, message: str = "AI rate limit reached. Please wait a moment before trying again.") -> None:
        super().__init__(message=message, status_code=429, code="AI_RATE_LIMIT")


class AIQuotaExceededError(AIProviderError):
    def __init__(self, message: str = "AI provider monthly quota exhausted.") -> None:
        super().__init__(message=message, status_code=503, code="AI_QUOTA_EXHAUSTED")


class AITimeoutError(AIProviderError):
    def __init__(self, message: str = "AI provider timed out. Please try again.") -> None:
        super().__init__(message=message, status_code=504, code="AI_TIMEOUT")


class AIMalformedOutputError(AIProviderError):
    def __init__(self, message: str = "AI provider returned malformed, unparseable output.") -> None:
        super().__init__(message=message, status_code=502, code="AI_MALFORMED_OUTPUT")


class AISchemaValidationError(AIProviderError):
    def __init__(self, message: str = "AI output failed schema validation rules.", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, status_code=502, code="AI_SCHEMA_VALIDATION_ERROR", details=details)


class AIRetryExhaustedError(AIProviderError):
    def __init__(self, message: str = "AI generation failed after maximum retry attempts.") -> None:
        super().__init__(message=message, status_code=503, code="AI_RETRIES_EXHAUSTED")


class AIUnsupportedModelError(AIProviderError):
    def __init__(self, message: str = "Configured AI model is not supported or no longer available.") -> None:
        super().__init__(message=message, status_code=502, code="AI_UNSUPPORTED_MODEL")

