/**
 * Context Bridge - Background Service Worker
 * 
 * Handles:
 * - Side panel activation
 * - API communication with backend
 * - Authentication state management via Supabase
 * - Message passing between content scripts and side panel
 */

import supabaseAuth from '../lib/supabase.js';

//const API_BASE_URL = 'https://context-bridge.azurewebsites.net/api';
const API_BASE_URL = 'https://context-bridge-api-dxfhdzabfqgrdhc2.eastus-01.azurewebsites.net/api';

// ============================================
// Side Panel Management
// ============================================

chrome.sidePanel
  .setPanelBehavior({ openPanelOnActionClick: true })
  .catch((error) => console.error('Side panel error:', error));

// ============================================
// Authentication (Supabase)
// ============================================

// Initialize auth on service worker start
supabaseAuth.initialize().then(session => {
  if (session) {
    console.log('Auth initialized with existing session');
  } else {
    console.log('No existing auth session');
  }
}).catch(console.error);

// Listen for auth state changes and notify UI
supabaseAuth.onAuthStateChange((event, session) => {
  console.log('Auth state changed:', event);
  // Broadcast to any open side panels
  chrome.runtime.sendMessage({
    type: 'AUTH_STATE_CHANGED',
    event,
    session: session ? {
      user: session.user,
      isAuthenticated: true
    } : null
  }).catch(() => {
    // Side panel might not be open
  });
});

async function getAuthToken() {
  return supabaseAuth.getAccessToken();
}

async function clearAuthToken() {
  await supabaseAuth.signOut();
}

// ============================================
// API Client
// ============================================

async function apiRequest(endpoint, options = {}) {
  const token = await getAuthToken();

  if (!token) {
    throw new Error('Not authenticated. Please log in first.');
  }

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
    'Authorization': `Bearer ${token}`,
  };

  let response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    // Token expired - try to refresh via Supabase
    try {
      await supabaseAuth.refreshSession();
      const newToken = await getAuthToken();
      if (newToken) {
        headers['Authorization'] = `Bearer ${newToken}`;
        response = await fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers });
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      await clearAuthToken();
      throw new Error('Session expired. Please log in again.');
    }
  }

  if (!response.ok) {
    let errorMsg = `API error ${response.status}`;
    try {
      const errorBody = await response.json();
      errorMsg = errorBody.error || errorBody.message || errorMsg;
    } catch { }
    console.error('API request failed:', errorMsg, endpoint);
    throw new Error(errorMsg);
  }

  return response;
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
// Authentication (Supabase OAuth)
// ============================================

async function getAuthStatus() {
  const session = await supabaseAuth.getSession();
  return {
    isAuthenticated: !!session?.access_token,
    user: session?.user || null,
  };
}

async function loginWithGoogle() {
  try {
    const result = await supabaseAuth.signInWithGoogle();

    if (result.session) {
      // Optionally sync user with backend (create/update user in Cosmos DB)
      try {
        await apiRequest('/auth/user', {
          method: 'POST',
          body: JSON.stringify({
            // Backend will extract user info from JWT
          })
        });
      } catch (error) {
        // Non-critical - user record will be created on first API call
        console.warn('User sync optional, continuing:', error);
      }

      return { success: true, user: result.user };
    }

    throw new Error('Authentication failed');
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
    console.log('Context Bridge: handleCaptureAndOpen called', { contextData, tabId: tab?.id, windowId: tab?.windowId });

    // Open the side panel first
    if (tab && tab.windowId) {
      await chrome.sidePanel.open({ windowId: tab.windowId });
      console.log('Context Bridge: Side panel opened');
    } else {
      console.warn('Context Bridge: No tab/windowId, cannot open side panel');
    }

    // Wait a moment for panel to open
    await new Promise(resolve => setTimeout(resolve, 500));

    // Capture context from the tab
    if (tab && tab.id) {
      console.log('Context Bridge: Sending CAPTURE_CONTEXT to tab', tab.id);

      let response;
      try {
        response = await chrome.tabs.sendMessage(tab.id, { type: 'CAPTURE_CONTEXT' });
      } catch (captureError) {
        console.error('Context Bridge: CAPTURE_CONTEXT failed', captureError);
        return { error: captureError.message };
      }

      console.log('Context Bridge: Capture response', JSON.stringify(response)?.substring(0, 500));

      if (response && response.messages && response.messages.length > 0) {
        // Send to side panel
        console.log('Context Bridge: Sending NEW_CONTEXT_AVAILABLE to side panel');
        chrome.runtime.sendMessage({
          type: 'NEW_CONTEXT_AVAILABLE',
          data: {
            title: `Conversation from ${contextData.title || 'AI Chat'}`,
            content: response.messages.map(m => `${m.role}: ${m.content}`).join('\n\n'),
            tags: [response.platform || 'chat'],
          }
        }).catch((err) => {
          console.error('Context Bridge: Failed to send to side panel', err);
        });
      } else {
        console.warn('Context Bridge: No messages captured. Response:', response);
      }
    } else {
      console.warn('Context Bridge: No tab.id, cannot capture');
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

console.log('Context Bridge background service worker initialized with Supabase auth');
