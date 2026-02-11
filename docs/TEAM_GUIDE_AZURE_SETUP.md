# 🧑‍💻 Team Member Guide: Azure Backend Setup

> **Assigned To:** Team Member 2
> **Estimated Time:** 2-3 days
> **Dependencies:** Azure account with subscription

---

## 🎯 Your Mission

Complete the Azure infrastructure setup and deploy the backend. The detailed Azure setup steps are already documented, but you need to:

1. Execute the Azure setup commands
2. Configure environment variables
3. Set up GitHub Actions for auto-deploy
4. Verify all endpoints work

---

## 📁 Project Structure Overview

```
Context Bridge/
├── backend/                    # ← YOUR FOCUS AREA
│   ├── function_app.py         # Main Azure Functions entry
│   ├── functions/              # API endpoint implementations
│   │   ├── memories.py         # CRUD for memories
│   │   ├── sanitize.py         # PII removal endpoint
│   │   └── ...
│   ├── services/
│   │   ├── cosmos_client.py    # Database client
│   │   └── encryption.py       # AES-256 encryption
│   ├── agents/                 # ADK Agents (already done)
│   ├── requirements.txt        # Python dependencies
│   ├── host.json               # Azure Functions config
│   └── local.settings.json     # Local dev settings (DO NOT COMMIT)
│
├── .github/
│   └── workflows/              # ← CREATE THIS
│       └── azure-deploy.yml    # GitHub Actions workflow
│
├── docs/
│   └── AZURE_SETUP.md          # ← FOLLOW THIS GUIDE
│
└── extension/                  # Chrome Extension (NOT YOUR FOCUS)
```

---

## 📋 Your Tasks

### Task 1: Follow Azure Setup Guide

**Read and execute:** `docs/AZURE_SETUP.md`

This guide covers:
- Creating Resource Group
- Creating Storage Account
- Creating Azure Functions App
- Creating Cosmos DB
- Configuring environment variables

**Save these values somewhere safe:**
```
RESOURCE_GROUP=context-bridge-rg
FUNCTION_APP=context-bridge-api
COSMOS_ACCOUNT=context-bridge-cosmos
STORAGE_ACCOUNT=contextbridgestorage
```

---

### Task 2: Create GitHub Actions Workflow

**Create:** `.github/workflows/azure-deploy.yml`

```yaml
name: Deploy to Azure Functions

on:
  push:
    branches:
      - master
    paths:
      - 'backend/**'
  workflow_dispatch:

env:
  AZURE_FUNCTIONAPP_NAME: 'context-bridge-api'
  AZURE_FUNCTIONAPP_PACKAGE_PATH: 'backend'
  PYTHON_VERSION: '3.11'

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ env.PYTHON_VERSION }}

    - name: Install dependencies
      run: |
        cd ${{ env.AZURE_FUNCTIONAPP_PACKAGE_PATH }}
        python -m pip install --upgrade pip
        pip install -r requirements.txt --target=".python_packages/lib/site-packages"

    - name: Deploy to Azure Functions
      uses: Azure/functions-action@v1
      with:
        app-name: ${{ env.AZURE_FUNCTIONAPP_NAME }}
        package: ${{ env.AZURE_FUNCTIONAPP_PACKAGE_PATH }}
        publish-profile: ${{ secrets.AZURE_FUNCTIONAPP_PUBLISH_PROFILE }}
        scm-do-build-during-deployment: true
```

---

### Task 3: Create Service Principal & Add GitHub Secret

> **Note:** This replaces the old publish profile method with more secure Service Principal authentication.

1. **Create Service Principal:**
   ```bash
   # Get Function App resource ID
   FUNCTION_APP_ID=$(az functionapp show \
     --name context-bridge-api \
     --resource-group context-bridge-rg \
     --query id --output tsv)
   
   # Create Service Principal
   az ad sp create-for-rbac \
     --name "context-bridge-github-actions" \
     --role Contributor \
     --scopes $FUNCTION_APP_ID \
     --sdk-auth
   ```

2. **Add to GitHub Secrets:**
   - Go to GitHub repo → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `AZURE_CREDENTIALS`
   - Value: Paste the **entire JSON output** from the command above
   - Click "Add secret"

> ⚠️ **Save the output immediately!** The `clientSecret` is shown only once.

---

### Task 4: Create local.settings.json

**Create/Update:** `backend/local.settings.json`

```json
{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsFeatureFlags": "EnableWorkerIndexing",
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "GEMINI_API_KEY": "your-gemini-api-key",
    "COSMOS_CONNECTION": "your-cosmos-connection-string",
    "COSMOS_DATABASE": "contextbridge",
    "ENCRYPTION_KEY": "your-256-bit-hex-key",
    "GOOGLE_CLIENT_ID": "your-google-oauth-client-id"
  },
  "Host": {
    "CORS": "*",
    "LocalHttpPort": 7071
  }
}
```

> ⚠️ **This file should be in .gitignore!** Never commit secrets.

---

### Task 5: Verify Deployment

After deploying, test these endpoints:

| Endpoint | Method | Test |
|----------|--------|------|
| `/api/health` | GET | Should return `{"status": "healthy"}` |
| `/api/memories` | GET | Should return empty array `[]` |
| `/api/sanitize` | POST | Send test text, verify PII removed |

**Quick test with curl:**
```bash
# Health check
curl https://context-bridge-api.azurewebsites.net/api/health

# Get memories (should return [])
curl https://context-bridge-api.azurewebsites.net/api/memories
```

---

## ✅ Checklist

- [ ] Azure Resource Group created
- [ ] Azure Storage Account created
- [ ] Azure Functions App created and running
- [ ] Cosmos DB created with containers (`memories`, `shared`)
- [ ] Environment variables set in Azure Portal
- [ ] GitHub Actions workflow created
- [ ] Service Principal created and `AZURE_CREDENTIALS` secret added to GitHub
- [ ] Push to main triggers deployment
- [ ] `/api/health` returns 200 OK
- [ ] `/api/memories` returns 200 OK

---

## 🔐 Environment Variables to Set in Azure

| Variable | Where to Get |
|----------|--------------|
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/) |
| `COSMOS_CONNECTION` | Azure Portal → Cosmos DB → Keys → Primary Connection String |
| `COSMOS_DATABASE` | `contextbridge` |
| `ENCRYPTION_KEY` | Run: `openssl rand -hex 32` |
| `GOOGLE_CLIENT_ID` | [Google Cloud Console](https://console.cloud.google.com/) |

---

## 🚨 Common Issues

### "No module named 'azure.functions'"
```bash
pip install azure-functions
```

### "Cosmos DB connection failed"
- Check connection string is correct (no extra spaces)
- Verify firewall allows Azure services

### "GitHub Actions failing"
- Check `AZURE_CREDENTIALS` secret is correctly added
- Verify Service Principal has Contributor role on Function App
- Ensure JSON format is valid (no extra spaces/newlines)

### "CORS errors from extension"
```bash
az functionapp cors add \
  --name context-bridge-api \
  --resource-group context-bridge-rg \
  --allowed-origins "*"
```

---

## 🔗 Key Files

| File | Purpose |
|------|---------|
| `docs/AZURE_SETUP.md` | Step-by-step Azure commands |
| `backend/function_app.py` | Main Functions entry point |
| `backend/requirements.txt` | Python dependencies |
| `.github/workflows/azure-deploy.yml` | CI/CD workflow |

---

## ❓ Questions?

If you're stuck or have questions, reach out. Good luck! 🚀
