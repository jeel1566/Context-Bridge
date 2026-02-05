"""Get the actual full error"""
import os
import sys
import traceback
from dotenv import load_dotenv
load_dotenv()

print("Testing...",  flush=True)

try:
    from google.adk.models.lite_llm import LiteLlm
    from google.adk.agents import LlmAgent
    
    print("Creating model...", flush=True)
    model = LiteLlm(model=f"openrouter/{os.getenv('OPENROUTER_MODEL')}")
    print("Model created", flush=True)
    
    print("Creating agent...", flush=True)
    agent = LlmAgent(
        model=model,
        name='test_agent',
        identity="Test agent",
        instruction="You are a test agent"
    )
    print("Agent created: " + agent.name, flush=True)
    
except Exception as e:
    print("\\n===== EXCEPTION =====", flush=True)
    print("Type: " + type(e).__name__, flush=True)
    print("Message: " + str(e)[:500], flush=True)
    print("\\n===== TRACEBACK =====", flush=True)
    traceback.print_exc(file=sys.stdout)
    sys.stdout.flush()
    sys.exit(1)
