# Context Bridge

ChatGPT forgets you when you switch to Claude. Context Bridge fixes that: one click and your AI remembers.

A Chrome extension plus an Azure Functions backend that acts as a universal context management layer for major LLMs (ChatGPT, Claude, Gemini). Powered by Google ADK agents and OpenRouter via LiteLLM.

## Live Demo

| Component | URL |
|-----------|-----|
| Backend API | https://context-bridge-api-dxfhdzabfqgrdhc2.eastus-01.azurewebsites.net/api |
| Health Check | https://context-bridge-api-dxfhdzabfqgrdhc2.eastus-01.azurewebsites.net/api/health |

## Features

- Ghost Bridge: one-click context transfer between LLMs
- Memory Bank: user-controlled, plug-and-play memory modules
- Hush Protocol: PII redaction and prompt injection defense
- AI Personalities: prebuilt personas (Explain Simple, Senior Dev, Academic)
- Real-time Collaboration: share memory banks with teammates

## Architecture

```
+---------------------------+
|        Azure Backend      |
|  Azure Functions (Python) |
|  Google ADK Agents        |
|  LiteLLM -> OpenRouter    |
|  Cosmos DB (Storage)      |
+-------------+-------------+
              |
              | HTTPS API
              v
+---------------------------+
|     Chrome Extension      |
|  Side Panel UI            |
|  Content Scripts          |
|  Service Worker           |
+---------------------------+
```

## Project Structure

```
Context-Bridge/
  backend/          Azure Functions (Python)
  extension/        Chrome extension (vanilla JS + CSS)
  docs/             Documentation
  assets/           Images and icons
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| AI Framework | Google ADK + LiteLLM |
| AI Models | OpenRouter (configurable model) |
| Backend | Azure Functions (Python 3.11) |
| Database | Azure Cosmos DB |
| Extension | Vanilla JS + CSS |
| Auth | Supabase JWT (primary) + legacy JWT fallback |
| CI/CD | GitHub Actions |

## Getting Started

### Prerequisites
- Python 3.11
- Azure Functions Core Tools

### Backend Setup (Local)
```bash
cd backend
py -3.11 -m venv .venv311
.\.venv311\Scripts\Activate
pip install -r requirements.txt
func start
```

### Extension Setup
1. Open Chrome -> chrome://extensions
2. Enable Developer mode
3. Click Load unpacked -> select extension/

### Deploy to Azure
```bash
cd backend
func azure functionapp publish context-bridge-api
```

## Environment Variables

Create backend/local.settings.json:

```json
{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsStorage": "",
    "COSMOS_ENDPOINT": "your-cosmos-endpoint",
    "COSMOS_KEY": "your-cosmos-key",
    "OPENROUTER_API_KEY": "your-openrouter-key",
    "SUPABASE_URL": "your-supabase-url",
    "SUPABASE_JWT_SECRET": "your-supabase-jwt-secret",
    "JWT_SECRET_KEY": "your-legacy-jwt-secret",
    "ENCRYPTION_KEY": "your-32-byte-hex-key"
  }
}
```

## License

MIT License
