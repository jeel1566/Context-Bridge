"""
Context Bridge - Main Agent Entry Point

This is the main agent module that exports the root_agent for ADK.
The agent follows the Sandbox pattern with:
- Scope Validator (Gemini 3 Flash) - Fast input/output validation
- Context Processor (Gemini 3 Pro) - Complex processing

Based on Google ADK documentation: https://google.github.io/adk-docs/
"""

from google.adk.agents import LlmAgent, SequentialAgent
from google.genai import types

from .scope_validator import scope_validator, validate_input, validate_output
from .context_processor import context_processor, process_context


# Define the validation-first pipeline agent
# This implements the "Sandbox" pattern from Context Bridge architecture:
# 1. Validate input (scope check)
# 2. Process context (PII, injection, personality, formatting)
# 3. Validate output (ensure safe response)

# Create a processing pipeline using SequentialAgent
# The Scope Validator runs first to check if content is allowed
# Then the Context Processor handles the actual work
context_bridge_pipeline = SequentialAgent(
    name="ContextBridgePipeline",
    description="Processes user context through validation and processing stages.",
    sub_agents=[
        scope_validator,
        context_processor,
    ],
)

# The main orchestrator agent that can delegate to specialized agents
# This is an LlmAgent so it can intelligently route requests
orchestrator = LlmAgent(
    model='gemini-3-flash-preview',
    name='context_bridge_orchestrator',
    description='Main orchestrator for Context Bridge - routes requests to appropriate processing agents.',
    instruction="""You are the Context Bridge Orchestrator, the main entry point for the Context Bridge system.

Context Bridge is a universal AI context management tool that helps users:
- Transfer context between different LLMs (ChatGPT, Claude, Gemini)
- Store and organize context in a Memory Bank
- Apply personality profiles to context
- Protect sensitive information with PII detection
- Defend against prompt injection attacks

## YOUR ROLE:
You receive user requests and coordinate with specialized agents:

1. **Scope Validation**: All content is validated to ensure it's appropriate
2. **Context Processing**: Text is sanitized, formatted, and enhanced
3. **Memory Management**: Store and retrieve context blocks
4. **Ghost Bridge**: Silent context transfer between LLMs

## AVAILABLE OPERATIONS:
When users ask about context, respond helpfully and guide them to use:
- `save_context`: Store context in Memory Bank
- `load_context`: Retrieve saved context
- `transfer_context`: Move context to another LLM
- `apply_personality`: Format context with a personality profile
- `validate_content`: Check if content is safe and appropriate

Always be helpful, secure, and respect user privacy.
Respond in a friendly but professional manner.
""",
    sub_agents=[
        scope_validator,
        context_processor,
    ],
    output_key="orchestrator_response",
)

# For ADK tools compatibility, the root agent must be named `root_agent`
# This is what the ADK framework looks for when running the agent
root_agent = orchestrator


# Export commonly used functions for direct API access
__all__ = [
    'root_agent',
    'orchestrator',
    'scope_validator',
    'context_processor',
    'context_bridge_pipeline',
    'validate_input',
    'validate_output',
    'process_context',
]
