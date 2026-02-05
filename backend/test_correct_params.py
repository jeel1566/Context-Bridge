"""Test with correct parameters"""
import os
from dotenv import load_dotenv
load_dotenv()

print("Testing with CORRECT parameters...")

try:
    from google.adk.models.lite_llm import LiteLlm
    from google.adk.agents import LlmAgent
    
    # Create model
    model = LiteLlm(model=f"openrouter/{os.getenv('OPENROUTER_MODEL')}")
    print(f"[1] Model created")
    
    # Create agent with CORRECT parameters
    agent = LlmAgent(
        model=model,
        name='test_agent',
        description="Test agent for ADK + LiteLLM integration",  # THIS instead of identity
        instruction="You are a test agent"  # THIS is the correct parameter
    )
    print(f"[2] Agent created: {agent.name}")
    
    print("\n===== SUCCESS! =====")
    print("ADK + LiteLLM integration working!")
    print(f"Model: {type(model).__name__}")
    print(f"Agent: {agent.name}")
    
except Exception as e:
    print(f"\nFAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
