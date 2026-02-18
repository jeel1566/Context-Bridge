#!/bin/bash
# Helper script to create Azure Service Principal
# This script works around Git Bash path conversion issues

echo "Creating Azure Service Principal for GitHub Actions..."
echo ""

# Prevent Git Bash from converting paths
export MSYS_NO_PATHCONV=1

# Create Service Principal
echo "Running: az ad sp create-for-rbac..."
SP_OUTPUT=$(az ad sp create-for-rbac \
  --name "context-bridge-github-actions" \
  --role Contributor \
  --scopes /subscriptions/d7bd98d0-fa87-45aa-ad6e-4c3325a0c4e7/resourceGroups/context-bridge-rg/providers/Microsoft.Web/sites/context-bridge-api \
  2>&1)

# Check if command succeeded
if [ $? -ne 0 ]; then
    echo "❌ Failed to create Service Principal"
    echo "$SP_OUTPUT"
    exit 1
fi

echo "✅ Service Principal created successfully!"
echo ""
echo "$SP_OUTPUT"
echo ""

# Extract values from output
APP_ID=$(echo "$SP_OUTPUT" | grep -o '"appId": "[^"]*' | cut -d'"' -f4)
PASSWORD=$(echo "$SP_OUTPUT" | grep -o '"password": "[^"]*' | cut -d'"' -f4)
TENANT=$(echo "$SP_OUTPUT" | grep -o '"tenant": "[^"]*' | cut -d'"' -f4)
SUBSCRIPTION_ID=$(az account show --query id --output tsv)

# Create AZURE_CREDENTIALS JSON
echo "Creating AZURE_CREDENTIALS JSON..."
cat > azure_credentials.json << EOF
{
  "clientId": "$APP_ID",
  "clientSecret": "$PASSWORD",
  "subscriptionId": "$SUBSCRIPTION_ID",
  "tenantId": "$TENANT"
}
EOF

echo ""
echo "✅ AZURE_CREDENTIALS JSON created!"
echo ""
echo "📋 Copy the following JSON and add it as a GitHub secret:"
echo "   Name: AZURE_CREDENTIALS"
echo "   Value:"
echo ""
cat azure_credentials.json
echo ""
echo ""
echo "⚠️  IMPORTANT: Save this JSON now! The clientSecret cannot be retrieved later."
echo ""
echo "📁 JSON also saved to: $(pwd)/azure_credentials.json"
