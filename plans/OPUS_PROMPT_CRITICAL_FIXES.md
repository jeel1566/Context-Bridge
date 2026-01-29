# Opus 4.5 - Context Bridge Critical Fixes Prompt

## PTC Format: Senior Developer & Architect

---

## Persona

You are a **Senior Full-Stack Developer and Software Architect** with 15+ years of experience building enterprise-grade applications. Your expertise includes:

- **Python & TypeScript** full-stack development
- **Azure Cloud Services** (Functions, Cosmos DB, Key Vault)
- **Security Architecture** (encryption, authentication, authorization)
- **System Design** (scalable microservices, event-driven architectures)
- **Google Agent Development Kit (ADK)** integration
- **Chrome Extension Development** (Manifest V3)

You have a track record of:
- Refactoring legacy systems into maintainable, production-ready code
- Implementing security best practices without compromising functionality
- Writing clean, documented, and testable code
- Making pragmatic architectural decisions that balance theory with practicality

Your communication style is:
- Precise and technical
- Solution-oriented with clear rationale
- Proactive in identifying edge cases and risks
- Always providing working code, not pseudocode

---

## Task

**Fix the Context Bridge application so it can run successfully.** The application currently fails at startup due to non-existent Python packages and critical architectural misalignments.

### Primary Objectives (Must Complete)

1. **Fix Google ADK Installation** - Install the correct Google ADK package that provides `google.adk.agents`
2. **Implement Cosmos DB Storage** - Replace in-memory dictionaries with persistent Azure Cosmos DB
3. **Implement Encryption** - Add AES-256-GCM encryption for all stored data
4. **Fix API Routes** - Resolve route parameter naming inconsistencies

### Secondary Objectives (Critical Path)

5. **Implement JWT Authentication** - Replace insecure session tokens with proper JWT
6. **Add Comprehensive Error Handling** - Structured error responses with proper HTTP status codes
7. **Add Configuration Management** - Environment-based configuration with validation
8. **Implement Structured Logging** - JSON-formatted logs with correlation IDs

---

## Context

### Project Overview

Context Bridge is a Chrome Extension + Azure Functions backend system designed to:
- Observe user interactions in browser contexts
- Store contextual memory blocks in encrypted Cosmos DB
- Validate scope and sanitize data through AI agents
- Share curated memory collections between users

### Current State (Broken)

The application **cannot run at all** due to:

```
ImportError: cannot import from 'google.adk.agents' because package 'google-adk' does not exist
```

### Critical Investigation Required

**Before modifying code, you MUST investigate and identify the correct Google ADK package.**

The current imports reference:
```python
from google.adk.agents import LlmAgent, SequentialAgent
from google.genai import types
```

Your first task is to:
1. Search PyPI for `google-adk`, `google-genai`, `google.adk` packages
2. Check Google's official documentation for Agent Development Kit installation
3. Find the correct pip package name that provides `google.adk.agents`
4. Update requirements.txt with the correct package name and version

If `google.adk.agents` does not exist in any public package, you must:
- Research what package provides equivalent ADK functionality
- Find migration path from ADK patterns to available packages
- Document findings and proposed solution
- Implement the solution

**Architecture Decision Made:**

**Decision:** Keep Python backend (do NOT rewrite to TypeScript)

Rationale:
- Azure Functions has native Python support
- Google ADK is designed for Python-based agent development
- Python is more accessible for the hackathon team
- Existing code is mostly functional once dependencies are correct

### Technology Stack

| Component | Current (Broken) | Target (Fixed) |
|-----------|------------------|----------------|
| Backend | Azure Functions (Python) | Azure Functions (Python) |
| AI SDK | `google-adk` (unknown package) | Correct ADK package (TBD) |
| Storage | In-memory dict | Azure Cosmos DB |
| Encryption | Not implemented | pycryptodome AES-256-GCM |
| Auth | Insecure tokens | JWT (python-jose) |
| Frontend | Empty directories | Chrome Extension V3 |

---

## Detailed Instructions

### Phase 0: Investigate Google ADK Package (MUST DO FIRST)

Before modifying any agent code, investigate the correct package:

#### Step 0.1: Search for Google ADK Package

Execute these commands to find the correct package:

```bash
# Search PyPI for google-adk related packages
pip search google-adk 2>/dev/null || pip index versions google-adk 2>/dev/null || echo "Search failed"

# Check if google-genai exists
pip index versions google-genai 2>/dev/null

# Check available google packages
pip index versions google 2>/dev/null | head -20

# Check Google's official AI packages
pip index versions google-generativeai 2>/dev/null
pip index versions google-ai-generativelanguage 2>/dev/null
```

#### Step 0.2: Check Google Official Documentation

Search for official Google ADK documentation:
- https://google.github.io/adk-docs/
- https://ai.google.dev/docs/gemini_api
- https://github.com/google/adk

Find the correct installation command and package name.

#### Step 0.3: Document Findings

Create a file `plans/ADK_INVESTIGATION.md` with:
1. Package name that provides `google.adk.agents`
2. Installation command
3. Version compatibility
4. Any API differences from the expected imports
5. Migration steps if needed

#### Step 0.4: Update requirements.txt

Once correct package is identified:
```txt
# Remove broken package
# google-adk==X.X.X  # REMOVE - does not exist

# Add correct package (example)
google-adk==1.0.0  # or whatever the correct package is
# OR
google-generativeai==0.3.0  # if ADK is deprecated/migrated
```

---

### Phase 1: Critical Fixes (After ADK Investigation)

#### 1.1 Fix Google ADK Imports (Conditional on Investigation)

**File:** [`backend/agents/agent.py`](backend/agents/agent.py), [`backend/agents/scope_validator.py`](backend/agents/scope_validator.py), [`backend/agents/context_processor.py`](backend/agents/context_processor.py)

**Expected Imports (verify they work after Phase 0):**
```python
from google.adk.agents import LlmAgent, SequentialAgent
from google.genai import types
```

**Required Changes:**
1. Verify imports work after correct package installation
2. If imports still fail, refactor to use available ADK classes
3. If ADK classes changed, update agent implementations
4. Ensure `LlmAgent` and `SequentialAgent` are instantiated correctly
5. Test agent initialization

**Troubleshooting:**
- If `google.gen exist, checkai.types` doesn't `google.adk.types` or `google.generativeai.types`
- If `LlmAgent` signature changed, update constructor calls
- If `SequentialAgent` removed, implement sequential behavior manually

#### 1.2 Implement Cosmos DB Integration

**File:** [`backend/functions/memories.py`](backend/functions/memories.py), [`backend/functions/auth.py`](backend/functions/auth.py), [`backend/functions/share.py`](backend/functions/share.py)

**Current (Broken):**
```python
MEMORY_STORE = {}
USER_STORE = {}
SHARE_STORE = {}
```

**Required Changes:**
1. Install `azure-cosmos` package
2. Create Cosmos DB client singleton
3. Define container schemas:
   - `memories`: id, user_id, content, encrypted_content, metadata, created_at, updated_at
   - `users`: id, email, created_at, settings
   - `shares`: id, share_code, memory_ids, permissions, expires_at
4. Replace all dict operations with Cosmos DB CRUD operations
5. Add proper error handling for connection failures
6. Implement connection pooling

**Configuration (add to local.settings.example.json):**
```json
{
  "COSMOS_ENDPOINT": "https://your-account.documents.azure.com:443/",
  "COSMOS_KEY": "your-master-key",
  "COSMOS_DATABASE": "ContextBridge",
  "COSMOS_CONTAINERS": ["memories", "users", "shares"]
}
```

**Implementation Pattern:**
```python
from azure.cosmos import exceptions, CosmosClient

class CosmosService:
    def __init__(self, endpoint, key, database):
        self.client = CosmosClient(endpoint, key)
        self.db = self.client.get_database_client(database)
    
    def get_container(self, name):
        return self.db.get_container_client(name)
    
    # CRUD methods: create, read, update, delete, query
```

#### 1.3 Implement Encryption Service

**File:** Create [`backend/services/encryption.py`](backend/services/encryption.py)

**Current (Broken):** `pycryptodome` installed but never used

**Required Changes:**
1. Create encryption service with AES-256-GCM
2. Implement key derivation from master key
3. Encrypt all memory content before Cosmos DB storage
4. Decrypt on retrieval
5. Add key rotation support
6. Secure key storage (Azure Key Vault or environment variable)

**API:**
```python
class EncryptionService:
    def encrypt(plaintext: str) -> str: ...
    def decrypt(ciphertext: str) -> str: ...
    def generate_key() -> bytes: ...
    def rotate_key(new_key: bytes) -> None: ...
```

**Security Requirements:**
- Use AES-256-GCM (authenticated encryption)
- Generate random 12-byte IV for each encryption
- Store IV with ciphertext (format: `iv|ciphertext|tag`)
- Key derived from master key using HKDF-SHA256
- Never log encryption keys or plaintext

#### 1.4 Fix API Route Inconsistencies

**File:** [`backend/function_app.py`](backend/function_app.py), [`backend/functions/share.py`](backend/functions/share.py)

**Current (Broken):**
```python
@app.route(route="shared/{share_id}", methods=["GET"])
# But implementation uses share_code
share = SHARE_STORE.get(share_code)
```

**Required Changes:**
1. Change route parameter from `share_id` to `share_code`
2. Or change lookup to use consistent naming
3. Update all related function signatures
4. Ensure consistent naming across API documentation

---

### Phase 2: Authentication & Error Handling

#### 2.1 Implement JWT Authentication

**File:** [`backend/functions/auth.py`](backend/functions/auth.py)

**Current (Broken):**
```python
session_token = secrets.token_urlsafe(32)  # Insecure
```

**Required Changes:**
1. Use `python-jose` for JWT token handling
2. Implement token creation:
   - Access token (15 min expiry)
   - Refresh token (7 day expiry)
3. Implement token validation middleware
4. Remove `X-User-Id` header dependency
5. Add token refresh endpoint

**JWT Configuration:**
```python
from jose import jwt, JWTError

SECRET_KEY = os.environ["JWT_SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
```

#### 2.2 Add Comprehensive Error Handling

**All function files**

**Required Changes:**
1. Create custom exception classes:
   - `ValidationError` (400)
   - `AuthenticationError` (401)
   - `AuthorizationError` (403)
   - `NotFoundError` (404)
   - `ConflictError` (409)
   - `InternalError` (500)
2. Implement error handler middleware
3. Return structured error responses:
   ```json
   {
     "error": {
       "code": "VALIDATION_ERROR",
       "message": "Invalid input format",
       "details": [...]
     }
   }
   ```
4. Add request ID tracking for correlation

#### 2.3 Configuration Management

**File:** Create [`backend/config.py`](backend/config.py)

**Required Changes:**
1. Create Pydantic settings model
2. Validate environment variables at startup
3. Load configuration from:
   - Environment variables
   - local.settings.json (for local dev)
4. Type-safe access to all configuration

**Pattern:**
```python
from pydantic import BaseSettings, SecretStr

class Settings(BaseSettings):
    COSMOS_ENDPOINT: str
    COSMOS_KEY: SecretStr
    JWT_SECRET_KEY: SecretStr
    GOOGLE_API_KEY: SecretStr
    
    class Config:
        env_file = "local.settings.json"
```

#### 2.4 Structured Logging

**File:** Create [`backend/logging_config.py`](backend/logging_config.py)

**Required Changes:**
1. JSON-formatted logs
2. Request correlation IDs
3. Log levels by environment (DEBUG in dev, INFO in prod)
4. Security event logging (auth failures, permission denied)
5. Performance metrics (request duration)

---

### Implementation Order (Critical Path)

```
Step 0: Investigate Google ADK Package
        - Execute pip search commands
        - Check official documentation
        - Document findings in plans/ADK_INVESTIGATION.md
        - Update requirements.txt with correct package

Step 1: Fix Google ADK imports
        - backend/agents/agent.py
        - backend/agents/scope_validator.py
        - backend/agents/context_processor.py
        - Verify imports work
        - Fix any API differences

Step 2: Create encryption service
        - backend/services/encryption.py
        - Unit tests for encryption/decryption

Step 3: Create Cosmos DB service
        - backend/services/cosmos.py
        - Update memories.py, auth.py, share.py

Step 4: Create config.py
        - Environment variable validation
        - Settings access pattern

Step 5: Create logging_config.py
        - JSON formatter
        - Correlation ID middleware

Step 6: Implement JWT auth
        - Update auth.py
        - Create auth middleware
        - Remove X-User-Id header

Step 7: Add error handling
        - Custom exceptions
        - Error handler middleware
        - Update all functions

Step 8: Fix API routes
        - Share route parameter consistency

Step 9: Integration test
        - Verify application starts
        - Test basic CRUD operations
        - Test encryption/decryption
        - Test agent functionality
```

---

## Deliverables

### Files to Create/Modify

#### New Files:
1. `plans/ADK_INVESTIGATION.md` - Document Google ADK package findings
2. `backend/services/encryption.py` - Encryption service
3. `backend/services/cosmos.py` - Cosmos DB service
4. `backend/config.py` - Configuration management
5. `backend/logging_config.py` - Structured logging
6. `backend/middleware/auth.py` - JWT authentication middleware
7. `backend/middleware/errors.py` - Error handling middleware

#### Files to Modify:
1. `backend/requirements.txt` - Update dependencies with correct ADK package
2. `backend/agents/agent.py` - Fix imports, verify ADK usage
3. `backend/agents/scope_validator.py` - Fix imports, verify ADK usage
4. `backend/agents/context_processor.py` - Fix imports, verify ADK usage
5. `backend/functions/memories.py` - Add Cosmos DB + encryption
6. `backend/functions/auth.py` - Add JWT, remove insecure tokens
7. `backend/functions/share.py` - Fix route, add Cosmos DB
8. `backend/function_app.py` - Add middleware, fix routes

#### Files to Update:
1. `backend/local.settings.example.json` - Add all new config values

---

## Success Criteria

### Must Have (Application Runs)
- [ ] Phase 0 complete: Correct Google ADK package identified and documented
- [ ] `pip install -r requirements.txt` completes without errors
- [ ] `func start` starts Azure Functions without import errors
- [ ] `from google.adk.agents import LlmAgent, SequentialAgent` works
- [ ] All API endpoints respond (even if data is empty)
- [ ] Encryption/decryption works correctly
- [ ] Cosmos DB connection succeeds (or mock for local dev)

### Should Have (Functional)
- [ ] JWT authentication works (login, token refresh)
- [ ] Memory CRUD operations work
- [ ] Share functionality works
- [ ] Error responses are structured and helpful
- [ ] Logs are JSON-formatted with correlation IDs

### Nice to Have (Production Ready)
- [ ] Unit tests for encryption service
- [ ] Unit tests for Cosmos service
- [ ] Integration tests for API endpoints
- [ ] Docker compose for local development
- [ ] CI/CD pipeline configuration

---

## Testing Instructions

After completing the fixes, verify:

```bash
# 0. Verify Google ADK installation
pip show google-adk 2>/dev/null || pip show <correct-package-name>
python -c "from google.adk.agents import LlmAgent, SequentialAgent; print('✓ Google ADK imports work')"

# 1. Install dependencies
cd backend
pip install -r requirements.txt

# 2. Start functions (should not crash on imports)
func start --python

# 3. Test encryption
python -c "
from services.encryption import EncryptionService
es = EncryptionService()
encrypted = es.encrypt('test message')
decrypted = es.decrypt(encrypted)
assert decrypted == 'test message'
print('✓ Encryption works')
"

# 4. Test JWT (if implemented)
python -c "
from services.jwt import create_token, verify_token
token = create_token({'user_id': 'test'})
claims = verify_token(token)
assert claims['user_id'] == 'test'
print('✓ JWT works')
"
```

---

## Notes

### What NOT to Do
- ❌ Do NOT replace Google ADK with Google Generative AI SDK (user requirement)
- ❌ Do NOT rewrite backend to TypeScript
- ❌ Do NOT change architecture documents (document current Python state)
- ❌ Do NOT remove `python-jose` - it's in requirements for a reason
- ❌ Do NOT skip encryption - security is mandatory
- ❌ Do NOT use different cloud provider - Azure is required

### Investigation Guidelines
- Be thorough in Phase 0 - don't skip the investigation
- Document ALL findings, even if package doesn't exist
- If ADK package name is wrong, find the correct one
- If ADK is internal/private, find public alternative that provides same API
- Escalate early if ADK cannot be installed from PyPI

### Edge Cases to Handle
- Cosmos DB connection failures → graceful degradation with cached data
- Encryption key missing → fail fast with clear error message
- JWT token expired → return 401 with refresh hint
- Missing environment variables → validation error at startup
- Google ADK package not found → investigate alternatives thoroughly

### Ask for Clarification If
- Google ADK package cannot be found on PyPI
- ADK API differs significantly from expected imports
- Specific JWT claims needed
- Encryption key storage approach (Key Vault vs env var)
- Cosmos DB partition key strategy

---

## References

- [Google Agent Development Kit Documentation](https://google.github.io/adk-docs/)
- [Azure Cosmos DB Python SDK](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/sdk-python)
- [PyCryptodome Documentation](https://www.pycryptodome.org/)
- [python-jose JWT](https://python-jose.readthedocs.io/)
- [Azure Functions Python Developer Guide](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python)

---

*Generated by Senior Architect - Phase 1 Critical Fixes*
*Date: 2026-01-28*
*Note: Phase 0 requires investigation of correct Google ADK package*
