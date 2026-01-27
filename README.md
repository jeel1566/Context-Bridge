# Context Bridge

> **Your AI, Your Rules** — Universal Context Management for LLMs

![Context Bridge](assets/logo.png)

A cross-browser extension + Azure Python Backend that acts as a **universal context management layer** for major LLMs (ChatGPT, Claude, Gemini). Powered by **Gemini 3** AI models.

## 🚀 Features

- **Ghost Bridge** — One-click context transfer between LLMs
- **Memory Bank** — User-controlled "plug-and-play" memory modules
- **Hush Protocol** — AI-powered data sanitization + prompt injection defense
- **AI Personalities** — Pre-built personas (Explain Simple, Senior Dev, Academic)
- **Real-time Collaboration** — Share Memory Banks with teammates

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│           AZURE (Backend)           │
├─────────────────────────────────────┤
│  Azure Functions (Python)           │
│  ├── Gemini 3 Agents (ADK)          │
│  │   ├── Scope Validator (Flash)    │
│  │   └── Context Processor (Pro)    │
│  └── Cosmos DB (Storage)            │
└─────────────────────────────────────┘
                  ▲
                  │ API calls
                  ▼
┌─────────────────────────────────────┐
│      BROWSER EXTENSION (Frontend)   │
├─────────────────────────────────────┤
│  • Side Panel UI (Vue 3 + shadcn)   │
│  • Content Scripts (DOM Observer)   │
│  • Service Worker                   │
└─────────────────────────────────────┘
```

## 📁 Project Structure

```
Context-Bridge/
├── backend/          # Azure Functions (Python)
├── extension/        # Browser Extension (TypeScript + Vue)
├── docs/             # Documentation
└── assets/           # Icons and images
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| AI Models | Gemini 3 Flash + Pro |
| Backend | Azure Functions (Python) |
| Database | Azure Cosmos DB |
| Extension | TypeScript + Vue 3 + shadcn-vue |
| Styling | Tailwind CSS + Glassmorphism |

## 🚦 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Azure CLI
- Gemini API Key

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
func start
```

### Extension Setup
```bash
cd extension
npm install
npm run dev
```

## 📄 License

MIT License

---

Built for the **Gemini 3 Global Hackathon** 🏆
