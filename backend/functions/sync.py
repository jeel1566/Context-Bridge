"""
Sync Function - Cross-device memory synchronization

Endpoints:
- POST /api/sync - Sync memories between devices
- GET /api/sync/status - Get sync status

Handles bidirectional sync with conflict resolution.
"""

import azure.functions as func
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

from services import get_cosmos_service, get_encryption_service
from middleware import (
    require_auth,
    require_json_body,
    handle_exception,
    ValidationError,
)

logger = logging.getLogger(__name__)


async def sync_handler(req: func.HttpRequest) -> func.HttpResponse:
    """Handle sync-related requests."""
    
    method = req.method
    path = req.url.split('/api/sync')[-1].split('?')[0]
    
    try:
        user = require_auth(req)
        user_id = user['id']
        
        if method == 'POST' and (path == '' or path == '/'):
            return await sync_memories(user_id, req)
        elif method == 'GET' and path == '/status':
            return await get_sync_status(user_id)
        else:
            return func.HttpResponse(
                json.dumps({"status": "error", "message": "Invalid sync endpoint"}),
                mimetype="application/json",
                status_code=404
            )
    except Exception as e:
        return handle_exception(e)


async def sync_memories(user_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/sync - Sync memories between devices.
    
    Request body:
    {
        "deviceId": "device-unique-id",
        "lastSyncAt": "2026-01-28T10:00:00Z",  // Last sync timestamp
        "memories": [  // Local changes since lastSyncAt
            {
                "id": "memory-id",
                "title": "...",
                "content": "...",
                "updatedAt": "...",
                "deleted": false
            }
        ]
    }
    
    Response:
    {
        "status": "success",
        "data": {
            "syncedAt": "2026-01-28T10:30:00Z",
            "serverChanges": [...],  // Changes from server since lastSyncAt
            "conflicts": [...]  // Conflicts that need resolution
        }
    }
    """
    
    body = require_json_body(req)
    
    device_id = body.get('deviceId')
    last_sync_at = body.get('lastSyncAt')
    local_memories = body.get('memories', [])
    
    if not device_id:
        raise ValidationError("deviceId is required")
    
    cosmos = get_cosmos_service()
    encryption = get_encryption_service()
    
    now = datetime.utcnow()
    sync_timestamp = now.isoformat() + 'Z'
    
    # Get server memories updated since last sync
    if last_sync_at:
        query = """
            SELECT * FROM c 
            WHERE c.userId = @userId 
            AND c.updatedAt > @lastSync
        """
        parameters = [
            {"name": "@userId", "value": user_id},
            {"name": "@lastSync", "value": last_sync_at}
        ]
    else:
        # First sync - get all memories
        query = "SELECT * FROM c WHERE c.userId = @userId"
        parameters = [{"name": "@userId", "value": user_id}]
    
    server_memories = await cosmos.memories.query(query, parameters)
    
    # Decrypt server memories
    for memory in server_memories:
        if memory.get('encryptedContent') and encryption.is_configured:
            try:
                memory['content'] = encryption.decrypt(memory['encryptedContent'])
                del memory['encryptedContent']
            except Exception:
                memory['content'] = "[Decryption failed]"
    
    # Process local changes
    conflicts = []
    applied_changes = []
    
    for local_memory in local_memories:
        memory_id = local_memory.get('id')
        if not memory_id:
            continue
        
        # Check if this memory exists on server
        server_memory = await cosmos.memories.read(memory_id, user_id)
        
        if server_memory:
            # Memory exists - check for conflicts
            server_updated = server_memory.get('updatedAt', '')
            local_updated = local_memory.get('updatedAt', '')
            
            if server_updated > local_updated:
                # Server has newer version - conflict
                conflicts.append({
                    "memoryId": memory_id,
                    "local": local_memory,
                    "server": server_memory,
                    "resolution": "server_wins"  # Default resolution
                })
            else:
                # Local is newer - apply local changes
                await _apply_local_change(user_id, local_memory, cosmos, encryption)
                applied_changes.append(memory_id)
        else:
            if local_memory.get('deleted'):
                # Already deleted on server, nothing to do
                pass
            else:
                # New memory from client - create it
                await _create_memory_from_sync(user_id, local_memory, cosmos, encryption)
                applied_changes.append(memory_id)
    
    # Update sync record for this device
    await _update_sync_record(user_id, device_id, sync_timestamp, cosmos)
    
    return func.HttpResponse(
        json.dumps({
            "status": "success",
            "data": {
                "syncedAt": sync_timestamp,
                "serverChanges": server_memories,
                "appliedChanges": applied_changes,
                "conflicts": conflicts
            }
        }),
        mimetype="application/json",
        status_code=200
    )


async def _apply_local_change(
    user_id: str,
    local_memory: Dict[str, Any],
    cosmos,
    encryption
) -> None:
    """Apply a local memory change to the server."""
    
    memory_id = local_memory['id']
    
    if local_memory.get('deleted'):
        # Delete the memory
        await cosmos.memories.delete(memory_id, user_id)
    else:
        # Update the memory
        existing = await cosmos.memories.read(memory_id, user_id)
        if existing:
            # Encrypt content
            content = local_memory.get('content', '')
            if encryption.is_configured and content:
                existing['encryptedContent'] = encryption.encrypt(content)
                existing.pop('content', None)
            else:
                existing['content'] = content
            
            # Update fields
            for field in ['title', 'tags', 'personality', 'privacyLevel', 'isActive']:
                if field in local_memory:
                    existing[field] = local_memory[field]
            
            existing['updatedAt'] = datetime.utcnow().isoformat() + 'Z'
            await cosmos.memories.update(memory_id, existing, user_id)


async def _create_memory_from_sync(
    user_id: str,
    local_memory: Dict[str, Any],
    cosmos,
    encryption
) -> None:
    """Create a new memory from sync data."""
    
    now = datetime.utcnow().isoformat() + 'Z'
    
    content = local_memory.get('content', '')
    encrypted_content = None
    if encryption.is_configured and content:
        encrypted_content = encryption.encrypt(content)
    
    memory = {
        "id": local_memory['id'],
        "userId": user_id,
        "title": local_memory.get('title', 'Untitled'),
        "content": content if not encryption.is_configured else None,
        "encryptedContent": encrypted_content,
        "tags": local_memory.get('tags', []),
        "personality": local_memory.get('personality', 'senior-dev'),
        "privacyLevel": local_memory.get('privacyLevel', 'local'),
        "isActive": local_memory.get('isActive', True),
        "createdAt": local_memory.get('createdAt', now),
        "updatedAt": now
    }
    
    # Remove None values
    memory = {k: v for k, v in memory.items() if v is not None}
    
    await cosmos.memories.create(memory)


async def _update_sync_record(
    user_id: str,
    device_id: str,
    sync_timestamp: str,
    cosmos
) -> None:
    """Update the sync record for a device."""
    
    # Store sync metadata (could use a separate container or user document)
    # For simplicity, we'll use the users container
    try:
        user = await cosmos.users.read(user_id)
        if user:
            sync_devices = user.get('syncDevices', {})
            sync_devices[device_id] = {
                "lastSyncAt": sync_timestamp,
                "deviceId": device_id
            }
            user['syncDevices'] = sync_devices
            await cosmos.users.update(user_id, user)
    except Exception as e:
        logger.warning(f"Failed to update sync record: {e}")


async def get_sync_status(user_id: str) -> func.HttpResponse:
    """GET /api/sync/status - Get sync status for all devices."""
    
    cosmos = get_cosmos_service()
    
    try:
        user = await cosmos.users.read(user_id)
        sync_devices = user.get('syncDevices', {}) if user else {}
        
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "data": {
                    "devices": list(sync_devices.values()),
                    "lastSync": max(
                        (d.get('lastSyncAt', '') for d in sync_devices.values()),
                        default=None
                    )
                }
            }),
            mimetype="application/json",
            status_code=200
        )
    except Exception:
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "data": {"devices": [], "lastSync": None}
            }),
            mimetype="application/json",
            status_code=200
        )
