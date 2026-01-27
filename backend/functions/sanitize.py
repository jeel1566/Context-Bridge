"""
Sanitize Function - POST /api/sanitize

Main Sandbox processing endpoint that:
1. Validates input via Scope Validator
2. Processes via Context Processor  
3. Validates output via Scope Validator
4. Returns sanitized context
"""

import azure.functions as func
import json
import logging
from typing import Optional

# These imports will work when deployed
try:
    from agents import validate_input, validate_output, process_context
except ImportError:
    # For local testing
    import sys
    sys.path.insert(0, '..')
    from agents import validate_input, validate_output, process_context


async def sanitize_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/sanitize
    
    Sandbox processing endpoint for context sanitization.
    
    Request Body:
    {
        "text": "The context to sanitize",
        "personality": "senior-dev",  // optional
        "target_llm": "chatgpt"       // optional
    }
    
    Response:
    {
        "status": "success",
        "data": {
            "sanitized_text": "...",
            "pii_found": [...],
            "injection_detected": false,
            ...
        }
    }
    """
    logging.info("POST /api/sanitize called")
    
    try:
        # Parse request body
        req_body = req.get_json()
        text = req_body.get('text', '')
        personality = req_body.get('personality', 'senior-dev')
        target_llm = req_body.get('target_llm', 'chatgpt')
        
        if not text:
            return func.HttpResponse(
                json.dumps({
                    "status": "error",
                    "message": "Missing required field: text"
                }),
                mimetype="application/json",
                status_code=400
            )
        
        # ============================================
        # SANDBOX PATTERN - Step 1: Validate Input
        # ============================================
        input_validation = await validate_input(text)
        
        if not input_validation.get('allowed', False):
            logging.warning(f"Input rejected: {input_validation.get('reason')}")
            return func.HttpResponse(
                json.dumps({
                    "status": "rejected",
                    "stage": "input",
                    "reason": input_validation.get('reason', 'Content not allowed'),
                    "category": input_validation.get('category', 'invalid')
                }),
                mimetype="application/json",
                status_code=400
            )
        
        # ============================================
        # SANDBOX PATTERN - Step 2: Process Context
        # ============================================
        result = await process_context(
            text=text,
            personality=personality,
            target_llm=target_llm
        )
        
        # ============================================
        # SANDBOX PATTERN - Step 3: Validate Output
        # ============================================
        output_text = result.get('sanitized_text', '')
        output_validation = await validate_output(output_text)
        
        if not output_validation.get('allowed', False):
            logging.warning(f"Output rejected: {output_validation.get('reason')}")
            return func.HttpResponse(
                json.dumps({
                    "status": "rejected",
                    "stage": "output",
                    "reason": output_validation.get('reason', 'Output not allowed'),
                    "category": output_validation.get('category', 'invalid')
                }),
                mimetype="application/json",
                status_code=400
            )
        
        # ============================================
        # Success - Return sanitized context
        # ============================================
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "data": result
            }),
            mimetype="application/json",
            status_code=200
        )
        
    except ValueError as e:
        logging.error(f"Invalid JSON: {e}")
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "message": "Invalid JSON in request body"
            }),
            mimetype="application/json",
            status_code=400
        )
    except Exception as e:
        logging.error(f"Sanitize error: {e}")
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "message": str(e)
            }),
            mimetype="application/json",
            status_code=500
        )
