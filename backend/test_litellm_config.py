"""Test different ways to configure LiteLlm"""
import os

# Set environment variable (LiteLLM standard way)
os.environ['OPENROUTER_API_KEY'] = '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'

print("Testing LiteLlm configuration methods...\n")

try:
    from google.adk.models.lite_llm import LiteLlm
    
    # Method 1: Just model name (rely on env var)
    print("[Test 1] Using only model name (env var for API key)")
    try:
        model1 = LiteLlm(model="openrouter/openai/gpt-oss-120b")
        print(f"✓ Method 1 works: {model1}")
    except Exception as e:
        print(f"✗ Method 1 failed: {e}")
    
    # Method 2: Check if there are other parameters
    print("\n[Test 2] Checking LiteLlm signature")
    import inspect
    sig = inspect.signature(LiteLlm)
    print(f"LiteLlm parameters: {sig}")
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
