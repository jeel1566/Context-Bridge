/**
 * Context Bridge - Background Service Worker
 * 
 * Handles:
 * - Side panel activation
 * - API communication with backend
 * - Authentication state management
 * - Message passing between content scripts and side panel
 */

//const API_BASE_URL = 'https://context-bridge.azurewebsites.net/api';
const API_BASE_URL = 'https://context-bridge-api-dxfhdzabfqgrdhc2.eastus-01.azurewebsites.net/api';

// ============================================
// Side Panel Management
// ============================================

chrome.sidePanel
  .setPanelBehavior({ openPanelOnActionClick: true })
  .catch((error) => console.error('Side panel error:', error));

// ============================================
// Authentication
// ============================================

let authToken = null;

async function getAuthToken() {
  if (authToken) return authToken;

  const result = await chrome.storage.local.get(['accessToken']);
  authToken = result.accessToken;
  return authToken;
}

async function setAuthToken(token) {
  authToken = token;
  await chrome.storage.local.set({ accessToken: token });
}

async function clearAuthToken() {
  authToken = null;
  await chrome.storage.local.remove(['accessToken', 'refreshToken', 'user']);
}

// ============================================
// API Client
// ============================================

async function apiRequest(endpoint, options = {}) {
  const token = await getAuthToken();

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    // Token expired - try to refresh
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      // Retry the request
      headers['Authorization'] = `Bearer ${await getAuthToken()}`;
      return fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers });
    } else {
      await clearAuthToken();
      throw new Error('Authentication required');
    }
  }

  return response;
}

async function refreshAccessToken() {
  try {
    const result = await chrome.storage.local.get(['refreshToken']);
    if (!result.refreshToken) return false;

    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refreshToken: result.refreshToken }),
    });

    if (response.ok) {
      const data = await response.json();
      await setAuthToken(data.data.access_token);
      return true;
    }
    return false;
  } catch (error) {
    console.error('Token refresh failed:', error);
    return false;
  }
}

// ============================================
// Message Handlers
// ============================================

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  handleMessage(message, sender)
    .then(sendResponse)
    .catch((error) => sendResponse({ error: error.message }));
  return true; // Keep the message channel open for async response
});

async function handleMessage(message, sender) {
  switch (message.type) {
    case 'GET_MEMORIES':
      return getMemories();

    case 'CREATE_MEMORY':
      return createMemory(message.data);

    case 'UPDATE_MEMORY':
      return updateMemory(message.id, message.data);

    case 'DELETE_MEMORY':
      return deleteMemory(message.id);

    case 'SYNC_MEMORIES':
      return syncMemories(message.data);

    case 'GET_AUTH_STATUS':
      return getAuthStatus();

    case 'LOGIN_WITH_GOOGLE':
      return loginWithGoogle();

    case 'LOGOUT':
      return logout();

    case 'CAPTURED_CONTEXT':
      return handleCapturedContext(message.data, sender.tab);

    case 'CAPTURE_AND_OPEN':
      return handleCaptureAndOpen(message.data, sender.tab);

    case 'OPEN_SIDE_PANEL':
      return openSidePanel(sender.tab);

    default:
      throw new Error(`Unknown message type: ${message.type}`);
  }
}

// ============================================
// Memory Operations
// ============================================

async function getMemories() {
  const response = await apiRequest('/memories');
  const data = await response.json();
  return data.data;
}

async function createMemory(memoryData) {
  const response = await apiRequest('/memories', {
    method: 'POST',
    body: JSON.stringify(memoryData),
  });
  const data = await response.json();
  return data.data;
}

async function updateMemory(id, memoryData) {
  const response = await apiRequest(`/memories/${id}`, {
    method: 'PUT',
    body: JSON.stringify(memoryData),
  });
  const data = await response.json();
  return data.data;
}

async function deleteMemory(id) {
  const response = await apiRequest(`/memories/${id}`, {
    method: 'DELETE',
  });
  return response.ok;
}

async function syncMemories(syncData) {
  const response = await apiRequest('/sync', {
    method: 'POST',
    body: JSON.stringify(syncData),
  });
  const data = await response.json();
  return data.data;
}

// ============================================
// Authentication
// ============================================

async function getAuthStatus() {
  const result = await chrome.storage.local.get(['user', 'accessToken']);
  return {
    isAuthenticated: !!result.accessToken,
    user: result.user || null,
  };
}

async function loginWithGoogle() {
  try {
    // Use Chrome Identity API for OAuth
    const authUrl = await chrome.identity.getAuthToken({
      interactive: true,
      scopes: ['openid', 'email', 'profile']
    });

    if (!authUrl) {
      throw new Error('Authentication cancelled');
    }

    // Exchange the token with our backend
    const response = await fetch(`${API_BASE_URL}/auth/google`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ idToken: authUrl }),
    });

    if (!response.ok) {
      throw new Error('Authentication failed');
    }

    const data = await response.json();

    // Store tokens
    await chrome.storage.local.set({
      accessToken: data.data.access_token,
      refreshToken: data.data.refresh_token,
      user: data.data.user,
    });

    authToken = data.data.access_token;

    return { success: true, user: data.data.user };
  } catch (error) {
    console.error('Login failed:', error);
    throw error;
  }
}

async function logout() {
  await clearAuthToken();
  return { success: true };
}

// ============================================
// Side Panel Operations
// ============================================

async function openSidePanel(tab) {
  try {
    if (tab && tab.windowId) {
      await chrome.sidePanel.open({ windowId: tab.windowId });
    }
    return { success: true };
  } catch (error) {
    console.error('Failed to open side panel:', error);
    return { error: error.message };
  }
}

async function handleCaptureAndOpen(contextData, tab) {
  try {
    // Open the side panel first
    if (tab && tab.windowId) {
      await chrome.sidePanel.open({ windowId: tab.windowId });
    }

    // Wait a moment for panel to open
    await new Promise(resolve => setTimeout(resolve, 300));

    // Capture context from the tab
    if (tab && tab.id) {
      const response = await chrome.tabs.sendMessage(tab.id, { type: 'CAPTURE_CONTEXT' });

      if (response && response.messages) {
        // Send to side panel
        chrome.runtime.sendMessage({
          type: 'NEW_CONTEXT_AVAILABLE',
          data: {
            title: `Conversation from ${contextData.title || 'AI Chat'}`,
            content: response.messages.map(m => `${m.role}: ${m.content}`).join('\n\n'),
            tags: [response.platform || 'chat'],
          }
        }).catch(() => {
          // Side panel might not be ready yet
        });
      }
    }

    return { success: true };
  } catch (error) {
    console.error('Capture and open failed:', error);
    return { error: error.message };
  }
}

// ============================================
// Context Capture
// ============================================

async function handleCapturedContext(contextData, tab) {
  // Process captured context from content script
  console.log('Captured context from:', tab?.url, contextData);

  // Optionally auto-create a memory
  if (contextData.autoSave) {
    return createMemory({
      title: contextData.title || 'Captured Context',
      content: contextData.content,
      tags: contextData.tags || [],
      personality: 'senior-dev',
    });
  }

  // Notify side panel about new context
  chrome.runtime.sendMessage({
    type: 'NEW_CONTEXT_AVAILABLE',
    data: contextData,
  }).catch(() => {
    // Side panel might not be open
  });

  return { received: true };
}

// ============================================
// Initialization
// ============================================

console.log('Context Bridge background service worker initialized');
