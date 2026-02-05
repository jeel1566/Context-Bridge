"""
Context Bridge - Main Agent Entry Point using Google ADK + LiteLLM

This module exports the ADK agent pipeline and orchestration functions.
Now using Google ADK for agent orchestration with LiteLLM gateway to OpenRouter.

The agent pipeline follows the Sandbox pattern:
- Scope Validator - Fast input/output validation
- Context Processor - Complex processing (PII, injection, personality, formatting)

Architecture: Google ADK → LiteLLM → OpenRouter (free tier)
"""

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
