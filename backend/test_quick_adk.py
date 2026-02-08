"""Quick test to check if ADK + LiteLLM works"""
import sys
import os

# Set environment
# os.environ['OPENROUTER_MODEL'] = 'openai/gpt-oss-120b'

if not os.environ.get('OPENROUTER_API_KEY'):
    print("Skipping test: OPENROUTER_API_KEY not found in environment")
    sys.exit(0)

try:
    from google.adk.models.lite_llm import LiteLlm
    print("✓ LiteLlm import successful")
    
    # Try to create a model
    model = LiteLlm(
        model="openrouter/openai/gpt-oss-120b",
        api_key=os.environ.get('OPENROUTER_API_KEY')
    )
    print(f"✓ LiteLlm model created: {model}")
    
    from google.adk.agents import LlmAgent
    print("✓ LlmAgent import successful")
    
    # Try to create an agent
    agent = LlmAgent(
        model=model,
        name='test_agent',
        instruction="You are a test agent"
    )
    print(f"✓ LlmAgent created: {agent.name}")
    
    print("\n✅ ALL IMPORTS AND SETUP SUCCESSFUL!")
    print("ADK + LiteLLM integration is working!")
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
