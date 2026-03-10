"""
Memories Function - CRUD operations for Memory Bank

Endpoints:
- POST /api/memories - Create memory block
- GET /api/memories - List all memories
- GET /api/memories/:id - Get single memory
- PUT /api/memories/:id - Update memory
- DELETE /api/memories/:id - Delete memory

Uses Cosmos DB for persistent storage and AES-256-GCM encryption.
"""

import azure.functions as func
import json
import logging
import uuid
from datetime import datetime
from typing import Optional

from services import get_cosmos_service, get_encryption_service
from middleware import (
    require_auth,
    require_json_body,
    require_fields,
    handle_exception,
    NotFoundError,
    AuthorizationError,
    ValidationError,
    apply_cors_headers,
    handle_cors_preflight,
)

logger = logging.getLogger(__name__)


async def memories_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    Dispatches HTTP requests for memory CRUD operations and returns the corresponding HTTP response.
    
    Handles CORS preflight (OPTIONS), requires authentication, and routes authenticated requests to list, get, create, update, or delete memory handlers based on the HTTP method and optional memory id route parameter. All successful and error responses are returned with CORS headers applied; exceptions are converted to HTTP error responses by centralized exception handling.
    
    Parameters:
        req (func.HttpRequest): The incoming HTTP request.
    
    Returns:
        func.HttpResponse: An HTTP response representing the operation result (success or error) with CORS headers applied.
    """
    
    method = req.method
    memory_id = req.route_params.get('id')
    
    try:
        # Handle CORS preflight
        if method == 'OPTIONS':
            return handle_cors_preflight(req)
            
        # Authenticate request
        user = require_auth(req)
        user_id = user['id']
        
        response = None
        
        if method == 'GET':
            if memory_id:
                response = await get_memory(user_id, memory_id)
            else:
                response = await list_memories(user_id)
            
        elif method == 'POST':
            response = await create_memory(user_id, req)
            
        elif method == 'PUT':
            response = await update_memory(user_id, memory_id, req)
            
        elif method == 'DELETE':
            response = await delete_memory(user_id, memory_id)
            
        else:
            response = func.HttpResponse(
                json.dumps({"status": "error", "message": "Method not allowed"}),
                mimetype="application/json",
                status_code=405
            )
            
        return apply_cors_headers(response, req)
            
    except Exception as e:
        response = handle_exception(e)
        return apply_cors_headers(response, req)


async def list_memories(user_id: str) -> func.HttpResponse:
    """
    List all memories belonging to the specified user.
    
    Parameters:
        user_id (str): ID of the authenticated user whose memories should be listed.
    
    Returns:
        func.HttpResponse: HTTP 200 response with a JSON body containing:
            - "status": "success"
            - "data": list of memory objects (each will include `content`; `encryptedContent` is removed)
            - "count": number of memories returned
    
    Notes:
        - If an encryption service is configured, encrypted memories are decrypted for the response.
        - If decryption of an individual memory fails, its `content` is set to "[Decryption failed]" and processing continues.
    """
    
    cosmos = get_cosmos_service()
    encryption = get_encryption_service()
    
    # Query memories by user ID
    query = "SELECT * FROM c WHERE c.userId = @userId ORDER BY c.updatedAt DESC"
    parameters = [{"name": "@userId", "value": user_id}]
    
    memories = await cosmos.memories.query(query, parameters)
    
    # Decrypt content for response
    for memory in memories:
        if memory.get('encryptedContent') and encryption.is_configured:
            try:
                memory['content'] = encryption.decrypt(memory['encryptedContent'])
                del memory['encryptedContent']  # Don't expose encrypted data
            except Exception:
                logger.warning(f"Failed to decrypt memory {memory.get('id')}")
                memory['content'] = "[Decryption failed]"
    
    return func.HttpResponse(
        json.dumps({
            "status": "success",
            "data": memories,
            "count": len(memories)
        }),
        mimetype="application/json",
        status_code=200
    )


async def get_memory(user_id: str, memory_id: str) -> func.HttpResponse:
    """GET /api/memories/:id - Get single memory."""
    
    cosmos = get_cosmos_service()
    encryption = get_encryption_service()
    
    memory = await cosmos.memories.read(memory_id, user_id)
    
    if not memory:
        raise NotFoundError("Memory not found")
    
    if memory.get('userId') != user_id:
        raise AuthorizationError("Access denied")
    
    # Decrypt content
    if memory.get('encryptedContent') and encryption.is_configured:
        try:
            memory['content'] = encryption.decrypt(memory['encryptedContent'])
            del memory['encryptedContent']
        except Exception:
            logger.warning(f"Failed to decrypt memory {memory_id}")
            memory['content'] = "[Decryption failed]"
    
    return func.HttpResponse(
        json.dumps({"status": "success", "data": memory}),
        mimetype="application/json",
        status_code=200
    )


async def create_memory(user_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/memories - Create new memory block."""
    
    body = require_json_body(req)
    require_fields(body, ['title', 'content'])
    
    cosmos = get_cosmos_service()
    encryption = get_encryption_service()
    
    now = datetime.utcnow().isoformat() + 'Z'
    memory_id = str(uuid.uuid4())
    
    # Encrypt content before storage
    content = body.get('content')
    encrypted_content = None
    if encryption.is_configured:
        encrypted_content = encryption.encrypt(content)
    
    memory = {
        "id": memory_id,
        "userId": user_id,
        "title": body.get('title'),
        "content": content if not encryption.is_configured else None,  # Only store if not encrypted
        "encryptedContent": encrypted_content,
        "tags": body.get('tags', []),
        "personality": body.get('personality', 'senior-dev'),
        "privacyLevel": body.get('privacyLevel', 'local'),
        "isActive": body.get('isActive', True),
        "createdAt": now,
        "updatedAt": now
    }
    
    # Remove None values
    memory = {k: v for k, v in memory.items() if v is not None}
    
    await cosmos.memories.create(memory)
    
    # Return memory with decrypted content
    response_memory = memory.copy()
    response_memory['content'] = content
    if 'encryptedContent' in response_memory:
        del response_memory['encryptedContent']
    
    return func.HttpResponse(
        json.dumps({"status": "success", "data": response_memory}),
        mimetype="application/json",
        status_code=201
    )


async def update_memory(user_id: str, memory_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """PUT /api/memories/:id - Update memory block."""
    
    cosmos = get_cosmos_service()
    encryption = get_encryption_service()
    
    memory = await cosmos.memories.read(memory_id, user_id)
    
    if not memory:
        raise NotFoundError("Memory not found")
    
    if memory.get('userId') != user_id:
        raise AuthorizationError("Access denied")
    
    body = require_json_body(req)
    
    # Update allowed fields
    for field in ['title', 'tags', 'personality', 'privacyLevel', 'isActive']:
        if field in body:
            memory[field] = body[field]
    
    # Handle content update with encryption
    if 'content' in body:
        content = body['content']
        if encryption.is_configured:
            memory['encryptedContent'] = encryption.encrypt(content)
            memory.pop('content', None)  # Remove unencrypted content
        else:
            memory['content'] = content
    
    memory['updatedAt'] = datetime.utcnow().isoformat() + 'Z'
    
    await cosmos.memories.update(memory_id, memory, user_id)
    
    # Return memory with decrypted content
    response_memory = memory.copy()
    if 'encryptedContent' in response_memory and encryption.is_configured:
        response_memory['content'] = body.get('content') or encryption.decrypt(response_memory['encryptedContent'])
        del response_memory['encryptedContent']
    
    return func.HttpResponse(
        json.dumps({"status": "success", "data": response_memory}),
        mimetype="application/json",
        status_code=200
    )


async def delete_memory(user_id: str, memory_id: str) -> func.HttpResponse:
    """DELETE /api/memories/:id - Delete memory block."""
    
    cosmos = get_cosmos_service()
    
    memory = await cosmos.memories.read(memory_id, user_id)
    
    if not memory:
        raise NotFoundError("Memory not found")
    
    if memory.get('userId') != user_id:
        raise AuthorizationError("Access denied")
    
    await cosmos.memories.delete(memory_id, user_id)
    
    return func.HttpResponse(
        json.dumps({"status": "success", "message": "Memory deleted"}),
        mimetype="application/json",
        status_code=200
    )