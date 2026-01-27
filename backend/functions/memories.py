"""
Memories Function - CRUD operations for Memory Bank

Endpoints:
- POST /api/memories - Create memory block
- GET /api/memories - List all memories
- GET /api/memories/:id - Get single memory
- PUT /api/memories/:id - Update memory
- DELETE /api/memories/:id - Delete memory
"""

import azure.functions as func
import json
import logging
import uuid
from datetime import datetime
from typing import Optional


# In-memory storage for development (replace with Cosmos DB in production)
MEMORY_STORE = {}


async def memories_handler(req: func.HttpRequest) -> func.HttpResponse:
    """Handle all memory-related requests."""
    
    method = req.method
    memory_id = req.route_params.get('id')
    
    # Get user ID from auth header (simplified for now)
    user_id = req.headers.get('X-User-Id', 'anonymous')
    
    try:
        if method == 'GET':
            if memory_id:
                return get_memory(user_id, memory_id)
            return list_memories(user_id)
            
        elif method == 'POST':
            return await create_memory(user_id, req)
            
        elif method == 'PUT':
            return await update_memory(user_id, memory_id, req)
            
        elif method == 'DELETE':
            return delete_memory(user_id, memory_id)
            
        else:
            return func.HttpResponse(
                json.dumps({"status": "error", "message": "Method not allowed"}),
                mimetype="application/json",
                status_code=405
            )
            
    except Exception as e:
        logging.error(f"Memories error: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            mimetype="application/json",
            status_code=500
        )


def list_memories(user_id: str) -> func.HttpResponse:
    """GET /api/memories - List all memories for user."""
    
    user_memories = [
        m for m in MEMORY_STORE.values()
        if m.get('userId') == user_id
    ]
    
    # Sort by updated date, newest first
    user_memories.sort(key=lambda x: x.get('updatedAt', ''), reverse=True)
    
    return func.HttpResponse(
        json.dumps({
            "status": "success",
            "data": user_memories,
            "count": len(user_memories)
        }),
        mimetype="application/json",
        status_code=200
    )


def get_memory(user_id: str, memory_id: str) -> func.HttpResponse:
    """GET /api/memories/:id - Get single memory."""
    
    memory = MEMORY_STORE.get(memory_id)
    
    if not memory:
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Memory not found"}),
            mimetype="application/json",
            status_code=404
        )
    
    if memory.get('userId') != user_id:
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Unauthorized"}),
            mimetype="application/json",
            status_code=403
        )
    
    return func.HttpResponse(
        json.dumps({"status": "success", "data": memory}),
        mimetype="application/json",
        status_code=200
    )


async def create_memory(user_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/memories - Create new memory block."""
    
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Invalid JSON"}),
            mimetype="application/json",
            status_code=400
        )
    
    # Validate required fields
    if not body.get('title') or not body.get('content'):
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Missing title or content"}),
            mimetype="application/json",
            status_code=400
        )
    
    now = datetime.utcnow().isoformat() + 'Z'
    memory_id = str(uuid.uuid4())
    
    memory = {
        "id": memory_id,
        "userId": user_id,
        "title": body.get('title'),
        "content": body.get('content'),
        "tags": body.get('tags', []),
        "personality": body.get('personality', 'senior-dev'),
        "privacyLevel": body.get('privacyLevel', 'local'),
        "isActive": body.get('isActive', True),
        "createdAt": now,
        "updatedAt": now
    }
    
    MEMORY_STORE[memory_id] = memory
    
    return func.HttpResponse(
        json.dumps({"status": "success", "data": memory}),
        mimetype="application/json",
        status_code=201
    )


async def update_memory(user_id: str, memory_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """PUT /api/memories/:id - Update memory block."""
    
    memory = MEMORY_STORE.get(memory_id)
    
    if not memory:
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Memory not found"}),
            mimetype="application/json",
            status_code=404
        )
    
    if memory.get('userId') != user_id:
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Unauthorized"}),
            mimetype="application/json",
            status_code=403
        )
    
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Invalid JSON"}),
            mimetype="application/json",
            status_code=400
        )
    
    # Update allowed fields
    for field in ['title', 'content', 'tags', 'personality', 'privacyLevel', 'isActive']:
        if field in body:
            memory[field] = body[field]
    
    memory['updatedAt'] = datetime.utcnow().isoformat() + 'Z'
    MEMORY_STORE[memory_id] = memory
    
    return func.HttpResponse(
        json.dumps({"status": "success", "data": memory}),
        mimetype="application/json",
        status_code=200
    )


def delete_memory(user_id: str, memory_id: str) -> func.HttpResponse:
    """DELETE /api/memories/:id - Delete memory block."""
    
    memory = MEMORY_STORE.get(memory_id)
    
    if not memory:
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Memory not found"}),
            mimetype="application/json",
            status_code=404
        )
    
    if memory.get('userId') != user_id:
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Unauthorized"}),
            mimetype="application/json",
            status_code=403
        )
    
    del MEMORY_STORE[memory_id]
    
    return func.HttpResponse(
        json.dumps({"status": "success", "message": "Memory deleted"}),
        mimetype="application/json",
        status_code=200
    )
