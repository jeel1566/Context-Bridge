"""
Authentication Middleware for Context Bridge

Provides JWT-based authentication for API endpoints.
"""

import logging
from typing import Optional, Dict, Any
import azure.functions as func

from services.jwt_service import get_jwt_service, TokenExpiredError, TokenInvalidError

logger = logging.getLogger(__name__)


def extract_token(req: func.HttpRequest) -> Optional[str]:
    """
    Extract Bearer token from Authorization header.
    
    Args:
        req: Azure Functions HTTP request
        
    Returns:
        Token string or None if not present
    """
    auth_header = req.headers.get('Authorization')
    
    if not auth_header:
        return None
    
    if not auth_header.startswith('Bearer '):
        return None
    
    return auth_header[7:]  # Remove 'Bearer ' prefix


def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate token and extract user information.
    
    Args:
        token: JWT access token
        
    Returns:
        User dict with id, email, etc. or None if invalid
    """
    jwt_service = get_jwt_service()
    
    if not jwt_service.is_configured:
        logger.warning("JWT not configured - authentication disabled")
        return None
    
    try:
        claims = jwt_service.verify_access_token(token)
        return {
            "id": claims.get("sub"),
            "email": claims.get("email"),
            "claims": claims
        }
    except TokenExpiredError:
        logger.debug("Token expired")
        return None
    except TokenInvalidError as e:
        logger.debug(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.warning(f"Token validation error: {e}")
        return None


def authenticate_request(req: func.HttpRequest) -> Optional[Dict[str, Any]]:
    """
    Authenticate an incoming request.
    
    Checks for JWT token in Authorization header.
    Falls back to X-User-Id header for backwards compatibility.
    In DEV_MODE, allows unauthenticated requests with a guest user.
    
    Args:
        req: Azure Functions HTTP request
        
    Returns:
        User dict or None if not authenticated
    """
    import os
    
    # Try JWT authentication first
    token = extract_token(req)
    if token:
        user = get_user_from_token(token)
        if user:
            return user
    
    # Fallback to legacy X-User-Id header (development only)
    user_id = req.headers.get('X-User-Id')
    if user_id:
        logger.warning("Using legacy X-User-Id header - should migrate to JWT")
        return {
            "id": user_id,
            "email": None,
            "legacy": True
        }
    
    # DEV MODE: Allow guest access for local development
    dev_mode = os.environ.get('DEV_MODE', 'false').lower() == 'true'
    if dev_mode:
        logger.warning("DEV_MODE enabled - using guest user (no auth required)")
        return {
            "id": "guest-local-dev",
            "email": "guest@localhost",
            "guest": True
        }
    
    return None


def require_auth(req: func.HttpRequest) -> Dict[str, Any]:
    """
    Require authentication for a request.
    
    Args:
        req: Azure Functions HTTP request
        
    Returns:
        User dict
        
    Raises:
        AuthenticationError: If not authenticated
    """
    from .errors import AuthenticationError
    
    user = authenticate_request(req)
    if not user:
        raise AuthenticationError("Authentication required")
    
    return user


# Export
__all__ = [
    'extract_token',
    'get_user_from_token',
    'authenticate_request',
    'require_auth',
]
