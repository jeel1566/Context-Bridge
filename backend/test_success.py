"""Final test - does it actually work?"""
import os
from dotenv import load_dotenv
load_dotenv()

print("Testing ADK + LiteLLM integration...")

try:
    from google.adk.models.lite_llm import LiteLlm
    from google.adk.agents import LlmAgent
    
    # Create model
    model = LiteLlm(model=f"openrouter/{os.getenv('OPENROUTER_MODEL')}")
    print(f"[1] Model created: {type(model).__name__}")
    
    # Create agent
    agent = LlmAgent(
        model=model,
        name='test_agent',
        identity="Test agent",
        instruction="You are a test agent"
    )
    print(f"[2] Agent created: {agent.name}")
    
    print("\nSUCCESS! ADK + LiteLLM is working!")
    print("The issue was likely the ADK upgrade to 1.23.0")
    
except Exception as e:
    print(f"\nFAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
