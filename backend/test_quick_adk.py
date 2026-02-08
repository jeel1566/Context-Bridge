"""Quick test to check if ADK + LiteLLM works"""
import sys
import os

# Set environment
os.environ['OPENROUTER_API_KEY'] = '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'
os.environ['OPENROUTER_MODEL'] = 'openai/gpt-oss-120b'

try:
    from google.adk.models.lite_llm import LiteLlm
    print("✓ LiteLlm import successful")
    
    # Try to create a model
    model = LiteLlm(
        model="openrouter/openai/gpt-oss-120b",
        api_key=os.environ['OPENROUTER_API_KEY']
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
