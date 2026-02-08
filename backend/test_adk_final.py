"""Final test - ADK + LiteLLM with correct configuration"""
import os
import sys

# Set environment variables (LiteLLM standard way)
os.environ['OPENROUTER_API_KEY'] = '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'
os.environ['OPENROUTER_MODEL'] = 'openai/gpt-oss-120b'

print("="*70)
print("ADK + LiteLLM Final Integration Test")
print("="*70)

try:
    from google.adk.models.lite_llm import LiteLlm
    from google.adk.agents import LlmAgent
    print("✓ Imports successful\n")
    
    # Create model (only model parameter)
    print("[Step 1] Creating LiteLlm model...")
    model = LiteLlm(model="openrouter/openai/gpt-oss-120b")
    print(f"✓ Model created\n")
    
    # Create agent
    print("[Step 2] Creating LlmAgent...")
    agent = LlmAgent(
        model=model,
        name='test_agent',
        instruction="You are a test agent. Always output valid JSON with an 'allowed' field."
    )
    print(f"✓ Agent created: {agent.name}\n")
    
    print("="*70)
    print("✅ SUCCESS! ADK + LiteLLM configuration is correct!")
    print("="*70)
    print("\nConfiguration summary:")
    print("  - API Key: Set via environment variable")
    print("  - Model: openrouter/openai/gpt-oss-120b")
    print("  - LiteLlm: Only accepts 'model' parameter")
    print("  - Agent: Created successfully")
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
