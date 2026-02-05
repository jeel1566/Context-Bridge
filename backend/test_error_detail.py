"""Debug the exact error - ASCII only"""
import os
import sys

# Load .env
from dotenv import load_dotenv
load_dotenv()

print("="*70)
print("Testing LiteLlm creation")
print("="*70)

print("\n[1] Environment variables:")
print("  OPENROUTER_API_KEY:", os.getenv('OPENROUTER_API_KEY')[:20] + "...")
print("  OPENROUTER_MODEL:", os.getenv('OPENROUTER_MODEL'))

try:
    print("\n[2] Importing LiteLlm...")
    from google.adk.models.lite_llm import LiteLlm
    print("  Import successful")
    
    print("\n[3] Creating model...")
    model_name = f"openrouter/{os.getenv('OPENROUTER_MODEL')}"
    print(f"  Model name: {model_name}")
    
    model = LiteLlm(model=model_name)
    print(f"  SUCCESS! Model created: {type(model)}")
    
except Exception as e:
    print(f"\n[ERROR] Failed:")
    print(f"  Type: {type(e).__name__}")
    print(f"  Message: {str(e)}")
    
    print("\n[FULL TRACEBACK]")
    import traceback
    traceback.print_exc()
    
    # Print Pydantic validation details if available
    if hasattr(e, 'errors'):
        print("\n[PYDANTIC VALIDATION ERRORS]")
        for error in e.errors():
            print(f"  - {error}")
