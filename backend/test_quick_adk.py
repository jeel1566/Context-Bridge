"""Quick test to check if ADK + LiteLLM works"""
import sys
import os


def test_quick_adk_integration():
    api_key = os.environ.get("OPENROUTER_API_KEY")
    model_name = os.environ.get("OPENROUTER_MODEL")
    if not api_key or not model_name:
        print("Skipping test: OPENROUTER_API_KEY or OPENROUTER_MODEL not found in environment")
        return

    try:
        from google.adk.models.lite_llm import LiteLlm
        print("OK LiteLlm import successful")

        # Try to create a model
        model = LiteLlm(
            model=f"openrouter/{model_name}",
            api_key=api_key
        )
        print(f"OK LiteLlm model created: {model}")

        from google.adk.agents import LlmAgent
        print("OK LlmAgent import successful")

        # Try to create an agent
        agent = LlmAgent(
            model=model,
            name='test_agent',
            instruction="You are a test agent"
        )
        print(f"OK LlmAgent created: {agent.name}")

        print("\nOK ALL IMPORTS AND SETUP SUCCESSFUL!")
        print("ADK + LiteLLM integration is working!")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        raise e


if __name__ == "__main__":
    try:
        test_quick_adk_integration()
    except Exception:
        sys.exit(1)
