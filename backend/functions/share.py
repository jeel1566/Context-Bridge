"""
Share Function - Collaboration endpoints

Endpoints:
- POST /api/share - Generate share link
- GET /api/shared/:share_code - Access shared bank (note: parameter is share_code)
"""

import azure.functions as func
import json
import logging
import uuid
import secrets
from datetime import datetime, timedelta

from services import get_cosmos_service
from middleware import (
    require_auth,
    require_json_body,
    require_fields,
    handle_exception,
    authenticate_request,
    NotFoundError,
    ValidationError,
    GoneError,
)

logger = logging.getLogger(__name__)


async def share_handler(req: func.HttpRequest) -> func.HttpResponse:
    """Handle share-related requests."""
    
    method = req.method
    # Note: route parameter name matches the route definition in function_app.py
    share_code = req.route_params.get('share_code')
    
    try:
        if method == 'POST':
            return await create_share(req)
        elif method == 'GET' and share_code:
            return await get_shared(share_code)
        else:
            return func.HttpResponse(
                json.dumps({"status": "error", "message": "Invalid request"}),
                mimetype="application/json",
                status_code=400
            )
    except Exception as e:
        return handle_exception(e)


async def create_share(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/share - Generate share link for memory blocks."""
    
    user = require_auth(req)
    user_id = user['id']
    
    body = require_json_body(req)
    
    memory_ids = body.get('memoryIds', [])
    permissions = body.get('permissions', 'view')  # view or edit
    expires_hours = body.get('expiresIn', 24)  # Default 24 hours
    
    if not memory_ids:
        raise ValidationError("No memories selected", details=["memoryIds list cannot be empty"])
    
    if permissions not in ('view', 'edit'):
        raise ValidationError("Invalid permissions", details=["Must be 'view' or 'edit'"])
    
    if expires_hours < 1 or expires_hours > 720:  # Max 30 days
        raise ValidationError("Invalid expiration", details=["expiresIn must be between 1 and 720 hours"])
    
    cosmos = get_cosmos_service()
    
    # Verify user owns all the memories
    for mid in memory_ids:
        memory = await cosmos.memories.read(mid, user_id)
        if not memory or memory.get('userId') != user_id:
            raise ValidationError(f"Memory {mid} not found or not owned by you")
    
    # Generate secure share code
    share_code = secrets.token_urlsafe(16)
    share_id = str(uuid.uuid4())
    
    now = datetime.utcnow()
    expires_at = now + timedelta(hours=expires_hours)
    
    share = {
        "id": share_id,
        "shareCode": share_code,
        "ownerId": user_id,
        "memoryIds": memory_ids,
        "permissions": permissions,
        "createdAt": now.isoformat() + 'Z',
        "expiresAt": expires_at.isoformat() + 'Z',
        "accessCount": 0
    }
    
    await cosmos.shares.create(share)
    
    # Generate share URL (frontend will construct full URL)
    share_url = f"/shared/{share_code}"
    
    return func.HttpResponse(
        json.dumps({
            "status": "success",
            "data": {
                "shareCode": share_code,
                "shareUrl": share_url,
                "permissions": permissions,
                "expiresAt": expires_at.isoformat() + 'Z'
            }
        }),
        mimetype="application/json",
        status_code=201
    )


async def get_shared(share_code: str) -> func.HttpResponse:
    """GET /api/shared/:share_code - Access shared memory bank."""
    
    cosmos = get_cosmos_service()
    
    # Find share by share code
    query = "SELECT * FROM c WHERE c.shareCode = @shareCode"
    parameters = [{"name": "@shareCode", "value": share_code}]
    shares = await cosmos.shares.query(query, parameters)
    
    if not shares:
        raise NotFoundError("Share not found")
    
    share = shares[0]
    
    # Check expiry
    expires_at = datetime.fromisoformat(share['expiresAt'].rstrip('Z'))
    if datetime.utcnow() > expires_at:
        raise GoneError("Share link has expired")
    
    # Increment access count
    share['accessCount'] = share.get('accessCount', 0) + 1
    await cosmos.shares.update(share['id'], share)
    
    # Get memories
    from services import get_encryption_service
    encryption = get_encryption_service()
    
    memories = []
    for mid in share.get('memoryIds', []):
        memory = await cosmos.memories.read(mid, share.get('ownerId'))
        if memory:
            # Decrypt content if encrypted
            if memory.get('encryptedContent') and encryption.is_configured:
                try:
                    memory['content'] = encryption.decrypt(memory['encryptedContent'])
                    del memory['encryptedContent']
                except Exception:
                    memory['content'] = "[Decryption failed]"
            
            # Remove sensitive fields for shared access
            memory.pop('userId', None)
            memory.pop('_rid', None)
            memory.pop('_self', None)
            memory.pop('_etag', None)
            memory.pop('_attachments', None)
            memory.pop('_ts', None)
            
            memories.append(memory)
    
    return func.HttpResponse(
        json.dumps({
            "status": "success",
            "data": {
                "memories": memories,
                "permissions": share.get('permissions', 'view'),
                "expiresAt": share.get('expiresAt')
            }
        }),
        mimetype="application/json",
        status_code=200
    )
