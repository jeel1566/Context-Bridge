"""
Error Handling Middleware for Context Bridge

Provides custom exception classes and structured error responses.
"""

import logging
from typing import Optional, Dict, Any, List
import json
import azure.functions as func

logger = logging.getLogger(__name__)


# ============================================
# Custom Exception Classes
# ============================================

class ContextBridgeError(Exception):
    """Base exception for Context Bridge."""
    
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    
    def __init__(
        self,
        message: str,
        details: Optional[List[str]] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.details = details or []
        if error_code:
            self.error_code = error_code


class ValidationError(ContextBridgeError):
    """400 Bad Request - Invalid input data."""
    status_code = 400
    error_code = "VALIDATION_ERROR"


class AuthenticationError(ContextBridgeError):
    """401 Unauthorized - Authentication required or failed."""
    status_code = 401
    error_code = "AUTHENTICATION_ERROR"


class AuthorizationError(ContextBridgeError):
    """403 Forbidden - Insufficient permissions."""
    status_code = 403
    error_code = "AUTHORIZATION_ERROR"


class NotFoundError(ContextBridgeError):
    """404 Not Found - Resource doesn't exist."""
    status_code = 404
    error_code = "NOT_FOUND"


class ConflictError(ContextBridgeError):
    """409 Conflict - Resource already exists or state conflict."""
    status_code = 409
    error_code = "CONFLICT"


class GoneError(ContextBridgeError):
    """410 Gone - Resource no longer available (e.g., expired share)."""
    status_code = 410
    error_code = "GONE"


class RateLimitError(ContextBridgeError):
    """429 Too Many Requests - Rate limit exceeded."""
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"


class InternalError(ContextBridgeError):
    """500 Internal Server Error - Unexpected error."""
    status_code = 500
    error_code = "INTERNAL_ERROR"


class ServiceUnavailableError(ContextBridgeError):
    """503 Service Unavailable - Dependency unavailable."""
    status_code = 503
    error_code = "SERVICE_UNAVAILABLE"


# ============================================
# Error Response Builder
# ============================================

def create_error_response(
    error: ContextBridgeError,
    request_id: Optional[str] = None
) -> func.HttpResponse:
    """
    Create a structured HTTP error response.
    
    Args:
        error: The exception that occurred
        request_id: Optional request correlation ID
        
    Returns:
        Azure Functions HttpResponse with error details
    """
    body = {
        "error": {
            "code": error.error_code,
            "message": error.message,
        }
    }
    
    if error.details:
        body["error"]["details"] = error.details
    
    if request_id:
        body["error"]["requestId"] = request_id
    
    return func.HttpResponse(
        json.dumps(body),
        mimetype="application/json",
        status_code=error.status_code
    )


def handle_exception(
    exc: Exception,
    request_id: Optional[str] = None
) -> func.HttpResponse:
    """
    Convert any exception to an appropriate HTTP response.
    
    Args:
        exc: The exception to handle
        request_id: Optional request correlation ID
        
    Returns:
        Azure Functions HttpResponse
    """
    if isinstance(exc, ContextBridgeError):
        logger.warning(f"Application error: {exc.error_code} - {exc.message}")
        return create_error_response(exc, request_id)
    
    # Handle built-in exceptions
    if isinstance(exc, ValueError):
        error = ValidationError(str(exc))
        return create_error_response(error, request_id)
    
    if isinstance(exc, PermissionError):
        error = AuthorizationError(str(exc))
        return create_error_response(error, request_id)
    
    if isinstance(exc, FileNotFoundError):
        error = NotFoundError(str(exc))
        return create_error_response(error, request_id)
    
    # Log unexpected errors
    logger.exception(f"Unexpected error: {exc}")
    
    # Return generic error (don't expose internal details)
    error = InternalError("An unexpected error occurred")
    return create_error_response(error, request_id)


# ============================================
# Request Validation Helpers
# ============================================

def require_json_body(req: func.HttpRequest) -> Dict[str, Any]:
    """
    Extract and validate JSON body from request.
    
    Args:
        req: Azure Functions HTTP request
        
    Returns:
        Parsed JSON body as dict
        
    Raises:
        ValidationError: If body is missing or invalid JSON
    """
    try:
        body = req.get_json()
        if body is None:
            raise ValidationError("Request body is required")
        return body
    except ValueError as e:
        raise ValidationError("Invalid JSON in request body", details=[str(e)])


def require_fields(body: Dict[str, Any], fields: List[str]) -> None:
    """
    Validate that required fields are present in body.
    
    Args:
        body: Request body dict
        fields: List of required field names
        
    Raises:
        ValidationError: If any required fields are missing
    """
    missing = [f for f in fields if not body.get(f)]
    if missing:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing)}",
            details=[f"Field '{f}' is required" for f in missing]
        )


def get_user_id_from_request(req: func.HttpRequest) -> str:
    """
    Extract user ID from authenticated request.
    
    First checks for JWT token in Authorization header,
    falls back to X-User-Id header for backwards compatibility.
    
    Args:
        req: Azure Functions HTTP request
        
    Returns:
        User ID string
        
    Raises:
        AuthenticationError: If no valid authentication found
    """
    from .auth import get_user_from_token
    
    auth_header = req.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        user = get_user_from_token(token)
        if user:
            return user['id']
    
    # Fallback to legacy header (for development)
    user_id = req.headers.get('X-User-Id')
    if user_id:
        logger.warning("Using legacy X-User-Id header - migrate to JWT")
        return user_id
    
    raise AuthenticationError("Authentication required")


# Export
__all__ = [
    # Exceptions
    'ContextBridgeError',
    'ValidationError',
    'AuthenticationError',
    'AuthorizationError',
    'NotFoundError',
    'ConflictError',
    'GoneError',
    'RateLimitError',
    'InternalError',
    'ServiceUnavailableError',
    
    # Functions
    'create_error_response',
    'handle_exception',
    'require_json_body',
    'require_fields',
    'get_user_id_from_request',
]
