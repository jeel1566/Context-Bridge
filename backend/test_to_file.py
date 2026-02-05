"""Get the actual full error to file"""
import os
import sys
import traceback
from dotenv import load_dotenv
load_dotenv()

error_file = open("e:\\Context Bridge\\error_details.txt", 'w', encoding='utf-8')

try:
    print("Testing...", file=error_file, flush=True)
    
    from google.adk.models.lite_llm import LiteLlm
    from google.adk.agents import LlmAgent
    
    print("Creating model...", file=error_file, flush=True)
    model = LiteLlm(model=f"openrouter/{os.getenv('OPENROUTER_MODEL')}")
    print("Model created successfully", file=error_file, flush=True)
    
    print("Creating agent...", file=error_file, flush=True)
    agent = LlmAgent(
        model=model,
        name='test_agent',
        identity="Test agent",
        instruction="You are a test agent"
    )
    print(f"SUCCESS! Agent created: {agent.name}", file=error_file, flush=True)
    
except Exception as e:
    print("\n===== EXCEPTION =====", file=error_file, flush=True)
    print(f"Type: {type(e).__name__}", file=error_file, flush=True)
    print(f"Message: {str(e)}", file=error_file, flush=True)
    print("\n===== FULL TRACEBACK =====", file=error_file, flush=True)
    traceback.print_exc(file=error_file)
    
    # Print Pydantic validation details
    if hasattr(e, 'errors'):
        print("\n===== PYDANTIC ERRORS =====", file=error_file, flush=True)
        for err in e.errors():
            print(f"  {err}", file=error_file)
    
    error_file.flush()
    error_file.close()
    sys.exit(1)

error_file.close()
print("Check error_details.txt")
