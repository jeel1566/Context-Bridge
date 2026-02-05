"""
Authentication Middleware for Context Bridge

Provides Supabase JWT-based authentication for API endpoints.
Updated to use Supabase Auth instead of custom JWT.
"""

import os
import logging
from typing import Optional, Dict, Any
import azure.functions as func

from middleware.supabase_auth import validate_supabase_jwt, get_user_id_from_token

# Keep legacy JWT service as fallback for migration
try:
    from services.jwt_service import get_jwt_service, TokenExpiredError, TokenInvalidError
    LEGACY_JWT_AVAILABLE = True
except ImportError:
    LEGACY_JWT_AVAILABLE = False

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
    
    First tries Supabase JWT validation, falls back to legacy JWT if configured.
    
    Args:
        token: JWT access token
        
    Returns:
        User dict with id, email, etc. or None if invalid
    """
    # Try Supabase JWT validation first (primary method)
    supabase_user = validate_supabase_jwt(token)
    if supabase_user:
        return {
            "id": supabase_user["user_id"],  # Supabase UUID
            "email": supabase_user.get("email"),
            "name": supabase_user.get("name"),
            "picture": supabase_user.get("picture"),
            "provider": supabase_user.get("provider", "supabase"),
            "claims": supabase_user.get("raw_claims", {})
        }
    
    # Fallback to legacy JWT if available
    if LEGACY_JWT_AVAILABLE:
        jwt_service = get_jwt_service()
        
        if jwt_service.is_configured:
            try:
                claims = jwt_service.verify_access_token(token)
                logger.info("Using legacy JWT - consider migrating to Supabase")
                return {
                    "id": claims.get("sub"),
                    "email": claims.get("email"),
                    "claims": claims,
                    "legacy": True  # Flag for migration tracking
                }
            except TokenExpiredError:
                logger.debug("Legacy token expired")
            except TokenInvalidError as e:
                logger.debug(f"Invalid legacy token: {e}")
            except Exception as e:
                logger.warning(f"Legacy token validation error: {e}")
    
    return None


def authenticate_request(req: func.HttpRequest) -> Optional[Dict[str, Any]]:
    """
    Authenticate an incoming request.
    
    Checks for JWT token in Authorization header (Supabase or legacy).
    In DEV_MODE, allows unauthenticated requests with a guest user.
    
    Args:
        req: Azure Functions HTTP request
        
    Returns:
        User dict or None if not authenticated
    """
    # Try JWT authentication
    token = extract_token(req)
    if token:
        user = get_user_from_token(token)
        if user:
            return user
    
    # DEV MODE: Allow guest access for local development
    dev_mode = os.environ.get('DEV_MODE', 'false').lower() == 'true'
    if dev_mode:
        # Check for X-User-Id header in dev mode only
        user_id = req.headers.get('X-User-Id')
        if user_id:
            logger.warning("DEV_MODE: Using X-User-Id header")
            return {
                "id": user_id,
                "email": None,
                "dev_mode": True
            }
        
        # Allow guest access in dev mode
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
