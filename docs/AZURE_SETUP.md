# Azure Setup Guide for Context Bridge

> Complete guide to setting up all Azure resources for the Context Bridge backend

---

## 📋 Prerequisites

Before starting, ensure you have:

- [ ] **Azure Account** with active subscription (free tier works)
- [ ] **Azure CLI** installed and logged in (`az login`)
- [ ] **Python 3.11+** installed locally
- [ ] **Azure Functions Core Tools** installed
- [ ] **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/)

---

## 🏗️ Azure Resources Overview

| Resource | Purpose | SKU/Tier |
|----------|---------|----------|
| **Resource Group** | Container for all resources | N/A |
| **Azure Functions App** | Backend API hosting | Consumption (Serverless) |
| **Azure Cosmos DB** | Memory storage database | Serverless |
| **Storage Account** | Functions runtime storage | Standard LRS |

---

## 📝 Step 1: Create Resource Group

```bash
# Set variables (customize these)
RESOURCE_GROUP="context-bridge-rg"
LOCATION="eastus"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION
```

---

## 📝 Step 2: Create Storage Account

> Required for Azure Functions runtime

```bash
STORAGE_ACCOUNT="contextbridgestorage"

az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS
```

---

## 📝 Step 3: Create Azure Functions App

```bash
FUNCTION_APP="context-bridge-api"

az functionapp create \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --storage-account $STORAGE_ACCOUNT \
  --consumption-plan-location $LOCATION \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --os-type Linux
```

---

## 📝 Step 4: Create Cosmos DB Account

```bash
COSMOS_ACCOUNT="context-bridge-cosmos"

# Create Cosmos DB account (Serverless for cost efficiency)
az cosmosdb create \
  --name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --kind GlobalDocumentDB \
  --capabilities EnableServerless \
  --default-consistency-level Session
```

### 4.1 Create Database and Containers

```bash
# Create database
az cosmosdb sql database create \
  --account-name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --name "contextbridge"

# Create memories container
az cosmosdb sql container create \
  --account-name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --database-name "contextbridge" \
  --name "memories" \
  --partition-key-path "/userId"

# Create shared container
az cosmosdb sql container create \
  --account-name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --database-name "contextbridge" \
  --name "shared" \
  --partition-key-path "/shareCode"
```

---

## 📝 Step 5: Configure Application Settings

### 5.1 Get Connection Strings

```bash
# Get Cosmos DB connection string
az cosmosdb keys list \
  --name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --type connection-strings \
  --query "connectionStrings[0].connectionString" \
  --output tsv
```

### 5.2 Set Environment Variables in Azure

```bash
# Generate encryption key (run locally)
ENCRYPTION_KEY=$(openssl rand -hex 32)

# Set all app settings
az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings \
    "GEMINI_API_KEY=your-gemini-api-key" \
    "COSMOS_CONNECTION=your-cosmos-connection-string" \
    "COSMOS_DATABASE=contextbridge" \
    "ENCRYPTION_KEY=$ENCRYPTION_KEY" \
    "GOOGLE_CLIENT_ID=your-google-oauth-client-id"
```

---

## 📝 Step 6: Configure CORS

```bash
az functionapp cors add \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --allowed-origins "*"
```

> ⚠️ **Note:** For production, replace `*` with specific origins like `https://chat.openai.com`, `https://claude.ai`, `https://gemini.google.com`

---

## 📝 Step 7: Deploy Backend Code

### Option A: Deploy from Local

```bash
cd backend
func azure functionapp publish $FUNCTION_APP
```

### Option B: GitHub Actions (Auto-Deploy)

1. Go to Azure Portal → Your Function App → Deployment Center
2. Connect to your GitHub repository
3. Enable GitHub Actions workflow
4. Push to `main` branch triggers auto-deploy

---

## 🔐 Environment Variables Summary

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `GEMINI_API_KEY` | Google Gemini API key | [Google AI Studio](https://aistudio.google.com/) |
| `COSMOS_CONNECTION` | Cosmos DB connection string | Azure Portal → Cosmos DB → Keys |
| `COSMOS_DATABASE` | Database name | `contextbridge` |
| `ENCRYPTION_KEY` | 256-bit hex key for AES encryption | `openssl rand -hex 32` |
| `GOOGLE_CLIENT_ID` | OAuth client ID (optional) | [Google Cloud Console](https://console.cloud.google.com/) |

---

## 🔍 Verification Checklist

After setup, verify everything works:

- [ ] **Function App running:** Visit `https://<function-app>.azurewebsites.net/api/health`
- [ ] **Cosmos DB accessible:** Check Azure Portal for successful connections
- [ ] **CORS configured:** Test API calls from extension
- [ ] **Environment variables set:** Go to Function App → Configuration → Application Settings

---

## 💰 Cost Estimate

| Service | Usage | Est. Monthly Cost |
|---------|-------|-------------------|
| Azure Functions | Up to 1M requests/month | **$0** (free tier) |
| Cosmos DB Serverless | ~1GB storage | **~$5** |
| Storage Account | Minimal | **~$0.05** |
| **Total** | | **~$5-10/month** |

---

## 🚨 Troubleshooting

### "Function app not found"
```bash
az functionapp show --name $FUNCTION_APP --resource-group $RESOURCE_GROUP
```

### "Cosmos DB connection failed"
- Verify connection string is correct
- Check firewall settings allow Azure services

### "CORS errors"
- Ensure allowed origins include your extension ID
- Try adding `https://*.chromiumapp.org` for extension testing

---

## 📚 Quick Reference Commands

```bash
# List all resources
az resource list --resource-group $RESOURCE_GROUP --output table

# View function app logs
az functionapp log tail --name $FUNCTION_APP --resource-group $RESOURCE_GROUP

# Restart function app
az functionapp restart --name $FUNCTION_APP --resource-group $RESOURCE_GROUP

# Delete everything (cleanup)
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

---

## 🔗 Useful Links

- [Azure Functions Python Docs](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python)
- [Cosmos DB Quick Start](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/quickstart-python)
- [Azure CLI Reference](https://learn.microsoft.com/en-us/cli/azure/)
- [Google AI Studio (Gemini)](https://aistudio.google.com/)
