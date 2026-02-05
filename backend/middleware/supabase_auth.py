"""
Supabase JWT Validation Middleware for Context Bridge

Validates JWTs issued by Supabase Auth and extracts user information.
Uses the Supabase JWT secret for HS256 token verification.
"""

import os
import jwt
from typing import Dict, Any, Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_supabase_config() -> Dict[str, str]:
    """
    Get Supabase configuration from environment variables.
    Cached for performance.
    """
    return {
        'url': os.environ.get('SUPABASE_URL', ''),
        'anon_key': os.environ.get('SUPABASE_ANON_KEY', ''),
        'jwt_secret': os.environ.get('SUPABASE_JWT_SECRET', ''),
    }


def validate_supabase_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate a Supabase JWT token and extract user information.
    
    Args:
        token: The JWT token string (without 'Bearer ' prefix)
        
    Returns:
        Dict containing user info if valid, None if invalid
        
    The returned dict includes:
        - user_id: Supabase user UUID (from 'sub' claim)
        - email: User's email address
        - email_verified: Whether email is verified
        - role: User's role (usually 'authenticated')
        - aud: Audience claim
        - iat: Issued at timestamp
        - exp: Expiration timestamp
        - raw_claims: Full JWT payload for additional needs
    """
    config = get_supabase_config()
    jwt_secret = config['jwt_secret']
    
    if not jwt_secret:
        logger.warning("SUPABASE_JWT_SECRET not configured, JWT validation will fail")
        return None
    
    try:
        # Decode and verify the JWT
        # Supabase uses HS256 algorithm with the JWT secret
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=['HS256'],
            audience='authenticated',  # Supabase uses 'authenticated' as audience
            options={
                'verify_exp': True,
                'verify_aud': True,
                'verify_iss': True,
                'require': ['sub', 'aud', 'exp', 'iat']
            },
            issuer=config['url'].rstrip('/') + '/auth/v1' if config['url'] else None
        )
        
        # Extract user information from claims
        user_info = {
            'user_id': payload.get('sub'),  # Supabase user UUID
            'email': payload.get('email'),
            'email_verified': payload.get('email_verified', False),
            'role': payload.get('role', 'authenticated'),
            'aud': payload.get('aud'),
            'iat': payload.get('iat'),
            'exp': payload.get('exp'),
            'raw_claims': payload  # Full payload for additional needs
        }
        
        # Extract user metadata if present
        user_metadata = payload.get('user_metadata', {})
        if user_metadata:
            user_info['name'] = user_metadata.get('full_name') or user_metadata.get('name')
            user_info['picture'] = user_metadata.get('avatar_url') or user_metadata.get('picture')
        
        # App metadata (provider, etc.)
        app_metadata = payload.get('app_metadata', {})
        if app_metadata:
            user_info['provider'] = app_metadata.get('provider')
        
        logger.debug(f"Successfully validated Supabase JWT for user: {user_info['user_id']}")
        return user_info
        
    except jwt.ExpiredSignatureError:
        logger.info("Supabase JWT has expired")
        return None
    except jwt.InvalidAudienceError:
        logger.warning("Supabase JWT has invalid audience")
        return None
    except jwt.InvalidIssuerError:
        logger.warning("Supabase JWT has invalid issuer")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid Supabase JWT: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error validating Supabase JWT: {str(e)}")
        return None


def get_user_id_from_token(token: str) -> Optional[str]:
    """
    Quick helper to extract just the user ID from a Supabase JWT.
    
    Args:
        token: The JWT token string (without 'Bearer ' prefix)
        
    Returns:
        User ID (Supabase UUID) if valid, None otherwise
    """
    user_info = validate_supabase_jwt(token)
    return user_info['user_id'] if user_info else None


def get_email_hash(email: str) -> str:
    """
    Generate a hash of the user's email for secondary verification.
    Used as an additional security layer for data access.
    
    Args:
        email: User's email address
        
    Returns:
        SHA256 hash of the lowercase email
    """
    import hashlib
    if not email:
        return ''
    return hashlib.sha256(email.lower().strip().encode()).hexdigest()
