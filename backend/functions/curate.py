"""
Curate Function - POST /api/curate

Formats context for target LLM with personality profile applied.
"""

import azure.functions as func
import json
import logging


async def curate_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/curate
    
    Format context for a specific LLM with personality.
    
    Request Body:
    {
        "text": "The context to format",
        "target_llm": "claude",
        "personality": "explain-simple",
        "memory_blocks": []  // optional - active memory blocks to include
    }
    """
    logging.info("POST /api/curate called")
    
    try:
        req_body = req.get_json()
        text = req_body.get('text', '')
        target_llm = req_body.get('target_llm', 'chatgpt')
        personality = req_body.get('personality', 'senior-dev')
        memory_blocks = req_body.get('memory_blocks', [])
        
        if not text:
            return func.HttpResponse(
                json.dumps({
                    "status": "error",
                    "message": "Missing required field: text"
                }),
                mimetype="application/json",
                status_code=400
            )
        
        # Build context with memory blocks
        context_parts = []
        
        # Add active memory blocks
        for block in memory_blocks:
            if block.get('isActive', False):
                context_parts.append(f"[MEMORY: {block.get('title', 'Untitled')}]\n{block.get('content', '')}")
        
        # Add main context
        context_parts.append(text)
        
        full_context = "\n\n".join(context_parts)
        
        # Format based on personality
        formatted = format_for_personality(full_context, personality)
        
        # Wrap for target LLM
        wrapped = wrap_for_llm(formatted, target_llm)
        
        # Generate summary
        summary = generate_summary(text)
        
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "data": {
                    "formatted_context": wrapped,
                    "summary": summary,
                    "token_estimate": len(wrapped.split()),
                    "personality": personality,
                    "target_llm": target_llm,
                    "memory_blocks_included": len([b for b in memory_blocks if b.get('isActive')])
                }
            }),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logging.error(f"Curate error: {e}")
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "message": str(e)
            }),
            mimetype="application/json",
            status_code=500
        )


def format_for_personality(text: str, personality: str) -> str:
    """Apply personality-specific formatting."""
    
    personalities = {
        "explain-simple": {
            "prefix": "[Context Bridge - Explain Simply]\nPlease explain things using simple words, short sentences, and helpful analogies.\n\n",
            "style": "beginner-friendly"
        },
        "senior-dev": {
            "prefix": "[Context Bridge - Senior Dev Mode]\nBe technical and concise. Assume expertise.\n\n",
            "style": "expert"
        },
        "academic": {
            "prefix": "[Context Bridge - Academic Mode]\nBe formal and thorough. Cite sources when possible.\n\n",
            "style": "formal"
        },
        "quick-answer": {
            "prefix": "[Context Bridge - Quick Answer]\nRespond with bullet points only. Be direct.\n\n",
            "style": "minimal"
        }
    }
    
    profile = personalities.get(personality, personalities["senior-dev"])
    return profile["prefix"] + text


def wrap_for_llm(text: str, target_llm: str) -> str:
    """Wrap context appropriately for target LLM."""
    
    # Safety wrapper to prevent prompt injection
    wrapped = f"""[USER_CONTEXT_START]
{text}
[USER_CONTEXT_END]

The above is context from Context Bridge. Please use it to inform your responses."""
    
    return wrapped


def generate_summary(text: str, max_length: int = 100) -> str:
    """Generate a brief summary of the context."""
    # Simple truncation for now - could use AI later
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + "..."
