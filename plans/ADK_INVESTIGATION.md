# Google ADK Package Investigation

## Summary

**The `google-adk` package EXISTS and is available on PyPI.**

## Package Details

| Property | Value |
|----------|-------|
| **Package Name** | `google-adk` |
| **Current Version** | 1.23.0 |
| **PyPI URL** | https://pypi.org/project/google-adk/ |
| **Documentation** | https://google.github.io/adk-docs/ |
| **GitHub** | https://github.com/google/adk-python |

## Installation

```bash
# Stable Release (Recommended)
pip install google-adk

# Development Version (for latest features/fixes)
pip install git+https://github.com/google/adk-python.git@main
```

## Correct Import Patterns

### For Agents

```python
# Basic Agent (most common)
from google.adk.agents import Agent

# For multi-agent systems with LLM routing
from google.adk.agents import LlmAgent, BaseAgent

# For workflow agents (deterministic execution)
from google.adk.agents import SequentialAgent  # Runs sub-agents in order
from google.adk.agents import ParallelAgent    # Runs sub-agents concurrently
from google.adk.agents import LoopAgent        # Loops until condition met
```

### For Runners and Sessions

```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
```

### For Types

```python
from google.genai import types
```

> **Note**: `google.genai.types` is provided by the `google-adk` package (which depends on `google-genai`).

## Model Names

The current code uses **correct model names**:

| Model | Status | Release Date |
|-------|--------|--------------|
| `gemini-3-flash-preview` | ✅ Available | Dec 17, 2025 |
| `gemini-3-pro-preview` | ✅ Available | Nov 18, 2025 |

> **Note**: Gemini 3 models are the latest generation. As of Jan 21, 2026, `gemini-flash-latest` alias points to `gemini-3-flash-preview`.

## API Key Setup

The ADK uses the `GOOGLE_API_KEY` environment variable:

```bash
# .env file
GOOGLE_API_KEY=your-gemini-api-key
```

Or set in `local.settings.json` for Azure Functions:
```json
{
  "Values": {
    "GEMINI_API_KEY": "your-gemini-api-key"
  }
}
```

## Requirements.txt Changes

### Before (Broken)
```txt
google-adk>=1.0.0
google-genai>=1.0.0
```

### After (Fixed)
```txt
google-adk>=1.23.0
# Note: google-genai is a dependency of google-adk, no need to specify separately
```

## Code Migration Required

### agent.py - No Changes Needed

The imports and model names are already correct:

```python
from google.adk.agents import LlmAgent, SequentialAgent
from google.genai import types

orchestrator = LlmAgent(
    model='gemini-3-flash-preview',  # ✅ CORRECT
    ...
)
```

### scope_validator.py and context_processor.py

Model names are correct - no changes needed:
- `gemini-3-flash-preview` ✅
- `gemini-3-pro-preview` ✅

## Verification Steps

After installation, verify with:

```bash
# 1. Check package is installed
pip show google-adk

# 2. Verify imports work
python -c "from google.adk.agents import Agent, LlmAgent, SequentialAgent; print('✓ ADK imports work')"

# 3. Verify genai types
python -c "from google.genai import types; print('✓ genai types work')"
```

## Conclusion

The `google-adk` package is real and available. The only issue is:

1. **Package version constraint** - Should use `>=1.23.0` (latest stable)
2. **Virtual environment** - May have stale/incorrect packages - recommend recreating

✅ The imports (`from google.adk.agents import LlmAgent, SequentialAgent`) are **correct**
✅ The model names (`gemini-3-flash-preview`, `gemini-3-pro-preview`) are **correct**

Once the package is properly installed with a fresh venv, the ADK code should work.
