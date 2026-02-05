# Supabase Auth and Azure Storage Fixes

## Executive Summary

The codebase has a hybrid authentication system combining Supabase Auth (new) with legacy Google OAuth + custom JWT (old). After the Supabase implementation, two main issues emerged:

1. **Authentication not working** - Supabase JWT validation fails due to missing configuration
2. **Memories not saving to Azure** - Cosmos DB not configured, falling back to in-memory storage

---

## Issue 1: Authentication Failures

### Root Cause 1.1: Missing SUPABASE_JWT_SECRET

**Location:** backend/middleware/supabase_auth.py:50-55

**Problem:** The validate_supabase_jwt() function returns None at line 55 because SUPABASE_JWT_SECRET is not configured in .env

**Evidence:**
```python
# backend/middleware/supabase_auth.py:50-55
config = get_supabase_config()
jwt_secret = config['jwt_secret']

if not jwt_secret:
    logger.warning("SUPABASE_JWT_SECRET not configured, JWT validation will fail")
    return None
```

**Impact:** All API calls with Supabase JWT tokens fail authentication.

---

### Root Cause 1.2: PKCE Code Challenge Bug

**Location:** extension/src/lib/supabase.js:72

**Problem:** The code challenge parameter is incorrectly set:

```javascript
// WRONG (line 72):
authUrl.searchParams.set('code_challenge', codeVerifier ? codeChallenge : undefined);

// SHOULD BE:
authUrl.searchParams.set('code_challenge', codeChallenge);
```

**Impact:** The OAuth flow may fail or use implicit flow instead of PKCE.

---

### Root Cause 1.3: User Sync Endpoint Mismatch

**Location:** extension/src/background/index.js:215 vs backend/function_app.py:78

**Problem:** The extension tries to POST to /auth/user, but the backend only accepts GET:

```javascript
// extension/src/background/index.js:215
await apiRequest('/auth/user', {
  method: 'POST',  // Wrong - endpoint is GET only
  body: JSON.stringify({})
});
```

```python
# backend/function_app.py:78-81
@app.route(route="auth/user", methods=["GET"])
def auth_user(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/auth/user - Get current user info."""
    return auth_handler(req)
```

**Impact:** User sync fails silently, user record not created in database.

---

## Issue 2: Azure Memory Storage Failures

### Root Cause 2.1: Cosmos DB Not Configured

**Location:** backend/.env:16-19

**Problem:** Cosmos DB configuration is commented out:

```python
#COSMOS_ENDPOINT=your_cosmos_endpoint
#COSMOS_KEY=your_cosmos_key
#COSMOS_DATABASE=contextbridge
```

**Evidence:** The CosmosService falls back to in-memory storage (line 268):

```python
# backend/services/cosmos.py:266-271
def _initialize_in_memory(self):
    """Initialize with in-memory storage."""
    self._memories = InMemoryStorage('memories')
    self._users = InMemoryStorage('users')
    self._shares = InMemoryStorage('shares')
    logger.warning("Using in-memory storage - data will not persist!")
```

**Impact:** All memories are lost when the Azure Function restarts.

---

### Root Cause 2.2: Missing Encryption Key

**Location:** backend/.env:22

**Problem:** Encryption key is not configured:

```python
#ENCRYPTION_KEY=your_encryption_key_here
```

**Impact:** The encryption service won't be configured, causing:
- Memories stored unencrypted (security risk)
- Potential failures when trying to encrypt/decrypt

---

### Root Cause 2.3: User ID Format Mismatch

**Location:** Multiple files

**Problem:** Supabase user IDs (UUIDs) differ from legacy Google OAuth user IDs:

| Auth System | User ID Source | Format |
|-------------|----------------|--------|
| Supabase | sub claim in JWT | UUID (e.g., abc123-def456...) |
| Legacy Google | Google's sub claim | UUID (different format) |

**Impact:** Existing users from the legacy system won't be able to access their memories after switching to Supabase.

---

## Issue 3: Additional Problems

### Problem 3.1: Missing CORS Configuration

**Location:** backend/function_app.py

**Problem:** No explicit CORS configuration for Azure Functions.

**Impact:** Browser extension requests may be blocked by CORS policies.

---

### Problem 3.2: Dev Mode Confusion

**Location:** backend/.env and backend/middleware/auth.py:115

**Problem:** DEV_MODE is not set in .env, but the code checks for it:

```python
# backend/middleware/auth.py:115
dev_mode = os.environ.get('DEV_MODE', 'false').lower() == 'true'
```

**Impact:** Unexpected behavior - may allow unauthenticated access in production if misconfigured.

---

### Problem 3.3: No Error Logging for Auth Failures

**Location:** extension/src/background/index.js:221-224

**Problem:** User sync errors are silently caught:

```javascript
} catch (error) {
  // Non-critical - user record will be created on first API call
  console.warn('User sync optional, continuing:', error);
}
```

**Impact:** Difficult to debug authentication issues.

---

## Fix Plan

### Phase 1: Authentication Fixes

1. Add Supabase Environment Variables
   - Add SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_JWT_SECRET to .env
   - Get SUPABASE_JWT_SECRET from Supabase Dashboard -> Project Settings -> API

2. Fix PKCE Code Challenge Bug
   - Update extension/src/lib/supabase.js:72 to use codeChallenge directly

3. Fix User Sync Endpoint
   - Change extension to use GET instead of POST for /auth/user
   - OR add POST endpoint to backend for user creation

4. Add User Creation on First Auth
   - Update /auth/user endpoint to create user if not exists
   - OR add new /api/auth/register endpoint

---

### Phase 2: Azure Storage Fixes

1. Configure Cosmos DB
   - Add COSMOS_ENDPOINT, COSMOS_KEY, COSMOS_DATABASE to .env
   - Ensure Cosmos DB containers exist: memories, users, shares

2. Configure Encryption Key
   - Generate and add ENCRYPTION_KEY to .env
   - Use a secure 32-byte (256-bit) key

3. Add User Migration Support
   - Create migration script to map legacy user IDs to Supabase user IDs
   - OR add user ID aliasing in the database

---

### Phase 3: Additional Improvements

1. Add CORS Configuration
   - Configure CORS in Azure Functions for extension origins

2. Add Better Error Logging
   - Log authentication failures with more details
   - Add error tracking (e.g., Sentry)

3. Add Health Check Endpoint
   - Verify all services are configured and working

---

## Required Configuration Values

### Supabase Configuration

Get these from Supabase Dashboard:

```env
SUPABASE_URL=https://czmpxzvcbwyxjhwrlgri.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN6bXB4enZjYnd5eGhod3JsZ3JpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAyMDA0ODUsImV4cCI6MjA4NTc3NjQ4NX0.f-Y7FQKbFElHI7BuI8LwkDR4bGz3-7NI3GO8EgJFaPQ
SUPABASE_JWT_SECRET=<GET_FROM_SUPABASE_DASHBOARD>
```

To get SUPABASE_JWT_SECRET:
1. Go to Supabase Dashboard -> Project Settings -> API
2. Find "JWT Secret" (not "anon key" or "service_role key")
3. Copy the value

---

### Azure Cosmos DB Configuration

```env
COSMOS_ENDPOINT=https://<your-account>.documents.azure.com:443/
COSMOS_KEY=<your-primary-key>
COSMOS_DATABASE=contextbridge
```

---

### Encryption Key

Generate a secure 32-byte key:

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

Then add to .env:
```env
ENCRYPTION_KEY=<generated-32-byte-key>
```

---

## Testing Checklist

After fixes are applied, verify:

- User can sign in with Google via Supabase
- Access token is validated by backend
- User record is created in Cosmos DB on first auth
- Memories can be created and saved to Cosmos DB
- Memories persist after Azure Function restart
- Token refresh works automatically
- Logout clears session properly
- CORS allows extension requests
- Error logs show useful information

---

## Files to Modify

| File | Changes |
|------|---------|
| backend/.env | Add Supabase, Cosmos DB, and Encryption config |
| extension/src/lib/supabase.js | Fix PKCE code challenge bug |
| extension/src/background/index.js | Fix user sync endpoint method |
| backend/functions/auth.py | Add user creation on first auth |
| backend/function_app.py | Add CORS configuration |
| backend/middleware/auth.py | Add better error logging |
