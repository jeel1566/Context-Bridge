"""
Share Function - Collaboration endpoints

Endpoints:
- POST /api/share - Generate share link
- GET /api/shared/:shareId - Access shared bank
"""

import azure.functions as func
import json
import logging
import uuid
import secrets
from datetime import datetime, timedelta


# In-memory storage for shares (replace with Cosmos DB)
SHARE_STORE = {}


async def share_handler(req: func.HttpRequest) -> func.HttpResponse:
    """Handle share-related requests."""
    
    method = req.method
    share_id = req.route_params.get('share_id')
    
    user_id = req.headers.get('X-User-Id', 'anonymous')
    
    try:
        if method == 'POST':
            return await create_share(user_id, req)
        elif method == 'GET' and share_id:
            return get_shared(share_id)
        else:
            return func.HttpResponse(
                json.dumps({"status": "error", "message": "Invalid request"}),
                mimetype="application/json",
                status_code=400
            )
    except Exception as e:
        logging.error(f"Share error: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            mimetype="application/json",
            status_code=500
        )


async def create_share(user_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/share - Generate share link for memory blocks."""
    
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Invalid JSON"}),
            mimetype="application/json",
            status_code=400
        )
    
    memory_ids = body.get('memoryIds', [])
    permissions = body.get('permissions', 'view')  # view or edit
    expires_hours = body.get('expiresIn', 24)  # Default 24 hours
    
    if not memory_ids:
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "No memories selected"}),
            mimetype="application/json",
            status_code=400
        )
    
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
    
    SHARE_STORE[share_code] = share
    
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


def get_shared(share_code: str) -> func.HttpResponse:
    """GET /api/shared/:shareId - Access shared memory bank."""
    
    share = SHARE_STORE.get(share_code)
    
    if not share:
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Share not found"}),
            mimetype="application/json",
            status_code=404
        )
    
    # Check expiry
    expires_at = datetime.fromisoformat(share['expiresAt'].rstrip('Z'))
    if datetime.utcnow() > expires_at:
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Share link expired"}),
            mimetype="application/json",
            status_code=410
        )
    
    # Increment access count
    share['accessCount'] += 1
    SHARE_STORE[share_code] = share
    
    # Get memories (from memory store - in production, fetch from Cosmos DB)
    from .memories import MEMORY_STORE
    
    memories = [
        MEMORY_STORE.get(mid)
        for mid in share.get('memoryIds', [])
        if MEMORY_STORE.get(mid)
    ]
    
    return func.HttpResponse(
        json.dumps({
            "status": "success",
            "data": {
                "memories": memories,
                "permissions": share.get('permissions', 'view'),
                "owner": share.get('ownerId'),
                "expiresAt": share.get('expiresAt')
            }
        }),
        mimetype="application/json",
        status_code=200
    )
