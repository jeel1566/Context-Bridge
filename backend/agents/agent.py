"""
Context Bridge - Main Agent Entry Point

This module exports the main agent functions for Context Bridge.
Previously used Google ADK orchestrator pattern, now simplified to direct
OpenRouter API calls.

The agent pipeline follows the Sandbox pattern:
- Scope Validator - Fast input/output validation
- Context Processor - Complex processing (PII, injection, personality, formatting)

Now using OpenRouter API: https://openrouter.ai/docs
"""

from .scope_validator import validate_input, validate_output
from .context_processor import process_context


# Export commonly used functions for direct API access
__all__ = [
    'validate_input',
    'validate_output',
    'process_context',
]
