"""
Middleware package for Context Bridge

Provides request processing middleware:
- auth: JWT authentication
- errors: Exception handling and structured responses
"""

from .auth import (
    extract_token,
    get_user_from_token,
    authenticate_request,
    require_auth,
)
from .errors import (
    ContextBridgeError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    GoneError,
    RateLimitError,
    InternalError,
    ServiceUnavailableError,
    create_error_response,
    handle_exception,
    require_json_body,
    require_fields,
)
from .cors import (
    apply_cors_headers,
    handle_cors_preflight,
)

__all__ = [
    # Auth
    'extract_token',
    'get_user_from_token',
    'authenticate_request',
    'require_auth',
    
    # Errors
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
    'create_error_response',
    'handle_exception',
    'require_json_body',
    'require_fields',
    
    # CORS
    'apply_cors_headers',
    'handle_cors_preflight',
]
