"""Debug the exact error"""
import os
import sys

# Load .env
from dotenv import load_dotenv
load_dotenv()

print("Environment variables:")
print(f"  OPENROUTER_API_KEY: {os.getenv('OPENROUTER_API_KEY')[:20]}...")
print(f"  OPENROUTER_MODEL: {os.getenv('OPENROUTER_MODEL')}")

print("\n" + "="*70)
print("Testing LiteLlm creation step by step")
print("="*70 + "\n")

try:
    # Step 1: Import
    print("[1] Importing LiteLlm...")
    from google.adk.models.lite_llm import LiteLlm
    print("   ✓ Import successful\n")
    
    # Step 2: Get model name
    print("[2] Preparing model name...")
    model_name = f"openrouter/{os.getenv('OPENROUTER_MODEL')}"
    print(f"   Model name: {model_name}\n")
    
    # Step 3: Create model (this is where it's failing)
    print("[3] Creating model... (THIS IS WHERE ERROR HAPPENS)")
    print(f"   Calling: LiteLlm(model='{model_name}')")
    model = LiteLlm(model=model_name)
    print(f"   ✓ Model created: {type(model)}\n")
    
    print("✅ SUCCESS!")
    
except Exception as e:
    print(f"\n✗ FAILED at step with error:")
    print(f"   Error type: {type(e)}")
    print(f"   Error message: {str(e)}\n")
    
    print("Full traceback:")
    import traceback
    traceback.print_exc()
