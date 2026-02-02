# Context Bridge

> **Your AI, Your Rules** — Universal Context Management for LLMs

A Chrome extension + Azure Python Backend that acts as a **universal context management layer** for major LLMs (ChatGPT, Claude, Gemini). Powered by **Google ADK** AI agents.

## 🚀 Features

- **Ghost Bridge** — One-click context transfer between LLMs
- **Memory Bank** — User-controlled "plug-and-play" memory modules
- **Hush Protocol** — AI-powered data sanitization + prompt injection defense
- **AI Personalities** — Pre-built personas (Explain Simple, Senior Dev, Academic)
- **Real-time Collaboration** — Share Memory Banks with teammates

## � Live Demo

| Component | URL |
|-----------|-----|
| **Backend API** | `https://context-bridge-api-dxfhdzabfqgrdhc2.eastus-01.azurewebsites.net/api` |
| **Health Check** | [/api/health](https://context-bridge-api-dxfhdzabfqgrdhc2.eastus-01.azurewebsites.net/api/health) |

## �🏗️ Architecture

```
┌─────────────────────────────────────┐
│           AZURE (Backend)           │
├─────────────────────────────────────┤
│  Azure Functions (Python 3.11)      │
│  ├── Google ADK Agents              │
│  │   ├── Scope Validator            │
│  │   └── Context Processor          │
│  └── Cosmos DB (Storage)            │
└─────────────────────────────────────┘
                  ▲
                  │ HTTPS API
                  ▼
┌─────────────────────────────────────┐
│      CHROME EXTENSION (Frontend)    │
├─────────────────────────────────────┤
│  • Side Panel UI                    │
│  • Content Scripts (DOM Observer)   │
│  • Service Worker                   │
└─────────────────────────────────────┘
```

## 📁 Project Structure

```
Context-Bridge/
├── backend/              # Azure Functions (Python)
│   ├── functions/        # API endpoints
│   ├── services/         # Cosmos DB, JWT, encryption
│   └── agents/           # Google ADK agents
├── extension/            # Chrome Extension
│   └── src/
│       ├── background/   # Service worker
│       ├── sidepanel/    # UI
│       └── content-scripts/
├── docs/                 # Documentation
└── .github/workflows/    # CI/CD
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| AI Framework | Google ADK (Agent Development Kit) |
| Backend | Azure Functions (Python 3.11) |
| Database | Azure Cosmos DB |
| Extension | Vanilla JS + CSS |
| CI/CD | GitHub Actions |

## 🚦 Getting Started

### Prerequisites
- Python 3.11
- Azure CLI
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
1. Open Chrome → `chrome://extensions`
2. Enable "Developer mode"
3. Click "Load unpacked" → select `extension/` folder

### Deploy to Azure
```bash
cd backend
func azure functionapp publish context-bridge-api
```

## 🔑 Environment Variables

Create `backend/local.settings.json`:
```json
{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsStorage": "",
    "COSMOS_ENDPOINT": "your-cosmos-endpoint",
    "COSMOS_KEY": "your-cosmos-key",
    "GOOGLE_CLIENT_ID": "your-google-client-id",
    "JWT_SECRET": "your-jwt-secret"
  }
}
```

## 📄 License

MIT License

---

Built with ❤️ using Google ADK and Azure Functions
