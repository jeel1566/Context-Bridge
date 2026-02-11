"""
Context Bridge - Main Agent Entry Point using Google ADK + LiteLLM

This module exports the ADK agent pipeline and orchestration functions.
Now using Google ADK for agent orchestration with LiteLLM gateway to OpenRouter.

The agent pipeline follows the Sandbox pattern:
- Scope Validator - Fast input/output validation
- Context Processor - Complex processing (PII, injection, personality, formatting)

Architecture: Google ADK → LiteLLM → OpenRouter (free tier)
"""

try:
    from google.adk.agents import SequentialAgent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    from .scope_validator import scope_validator, validate_input, validate_output
    from .context_processor import context_processor, process_context

    # Create pipeline orchestrator
    context_bridge_pipeline = SequentialAgent(
        name="ContextBridgePipeline",
        description="Processes user context through validation and processing stages.",
        sub_agents=[
            scope_validator,
            context_processor,
        ],
    )

    # Root agent for orchestration
    root_agent = context_bridge_pipeline

    # Export both pipeline and individual functions
    __all__ = [
        'root_agent',
        'context_bridge_pipeline',
        'scope_validator',
        'context_processor',
        'validate_input',
        'validate_output',
        'process_context',
    ]

except ImportError as e:
    import logging
    logging.getLogger(__name__).warning(
        f"ADK agent pipeline not available (missing dependency): {e}"
    )
    
    # Provide stub implementations so Azure Functions can still load
    root_agent = None
    context_bridge_pipeline = None
    scope_validator = None
    context_processor = None
    
    # Stub functions that return graceful errors
    async def validate_input(text: str) -> dict:
        """Stub implementation when Google ADK is not available"""
        return {
            "allowed": False,
            "reason": "Agent pipeline not available - Google ADK dependencies not installed",
            "category": "service_unavailable"
        }
    
    async def validate_output(text: str) -> dict:
        """Stub implementation when Google ADK is not available"""
        return {
            "allowed": False,
            "reason": "Agent pipeline not available - Google ADK dependencies not installed",
            "category": "service_unavailable"
        }
    
    async def process_context(text: str, personality: str = "senior-dev", target_llm: str = "chatgpt") -> dict:
        """Stub implementation when Google ADK is not available"""
        return {
            "sanitized_text": text,
            "pii_found": [],
            "injection_detected": False,
            "warning": "Agent pipeline not available - returning unsanitized text"
        }
    
    __all__ = [
        'root_agent',
        'context_bridge_pipeline',
        'scope_validator',
        'context_processor',
        'validate_input',
        'validate_output',
        'process_context',
    ]
