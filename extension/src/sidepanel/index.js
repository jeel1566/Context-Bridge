/**
 * Context Bridge - Side Panel JavaScript
 */

// ============================================
// State
// ============================================

let memories = [];
let currentEditId = null;

// ============================================
// DOM Elements
// ============================================

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

const elements = {
    loginBtn: $('#login-btn'),
    userInfo: $('#user-info'),
    userAvatar: $('#user-avatar'),
    userName: $('#user-name'),
    captureBtn: $('#capture-btn'),
    memoriesList: $('#memories-list'),
    addMemoryBtn: $('#add-memory-btn'),
    memoryEditor: $('#memory-editor'),
    editorTitle: $('#editor-title'),
    memoryForm: $('#memory-form'),
    memoryTitle: $('#memory-title'),
    memoryContent: $('#memory-content'),
    memoryTags: $('#memory-tags'),
    cancelBtn: $('#cancel-btn'),
    syncBtn: $('#sync-btn'),
    syncIndicator: $('#sync-indicator'),
    syncText: $('#sync-text'),
};

// ============================================
// API Communication
// ============================================

async function sendMessage(type, data = {}) {
    return chrome.runtime.sendMessage({ type, data, ...data });
}

// ============================================
// Authentication
// ============================================

async function checkAuthStatus() {
    try {
        const status = await sendMessage('GET_AUTH_STATUS');
        updateAuthUI(status);
        return status.isAuthenticated;
    } catch (error) {
        console.error('Auth check failed:', error);
        return false;
    }
}

function updateAuthUI(status) {
    if (status.isAuthenticated && status.user) {
        elements.loginBtn.classList.add('hidden');
        elements.userInfo.classList.remove('hidden');
        elements.userAvatar.src = status.user.picture || '';
        elements.userName.textContent = status.user.name || status.user.email;
    } else {
        elements.loginBtn.classList.remove('hidden');
        elements.userInfo.classList.add('hidden');
    }
}

async function handleLogin() {
    try {
        elements.loginBtn.disabled = true;
        elements.loginBtn.textContent = 'Logging in...';

        const result = await sendMessage('LOGIN_WITH_GOOGLE');

        if (result.success) {
            updateAuthUI({ isAuthenticated: true, user: result.user });
            await loadMemories();
        }
    } catch (error) {
        console.error('Login failed:', error);
        alert('Login failed. Please try again.');
    } finally {
        elements.loginBtn.disabled = false;
        elements.loginBtn.textContent = 'Login';
    }
}

// ============================================
// Memories
// ============================================

async function loadMemories() {
    try {
        memories = await sendMessage('GET_MEMORIES') || [];
        renderMemories();
    } catch (error) {
        console.error('Failed to load memories:', error);
        memories = [];
        renderMemories();
    }
}

function renderMemories() {
    if (!memories.length) {
        elements.memoriesList.innerHTML = `
      <p class="empty-state">No memories yet. Capture your first context!</p>
    `;
        return;
    }

    elements.memoriesList.innerHTML = memories.map(memory => `
    <div class="memory-item" data-id="${memory.id}">
      <h3>${escapeHtml(memory.title)}</h3>
      <p>${escapeHtml(truncate(memory.content, 80))}</p>
      ${memory.tags?.length ? `
        <div class="memory-tags">
          ${memory.tags.slice(0, 3).map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
        </div>
      ` : ''}
    </div>
  `).join('');

    // Add click handlers
    $$('.memory-item').forEach(item => {
        item.addEventListener('click', () => editMemory(item.dataset.id));
    });
}

function truncate(text, length) {
    if (!text) return '';
    return text.length > length ? text.substring(0, length) + '...' : text;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================
// Memory Editor
// ============================================

function showEditor(memory = null) {
    currentEditId = memory?.id || null;
    elements.editorTitle.textContent = memory ? 'Edit Memory' : 'New Memory';

    elements.memoryTitle.value = memory?.title || '';
    elements.memoryContent.value = memory?.content || '';
    elements.memoryTags.value = memory?.tags?.join(', ') || '';

    elements.memoryEditor.classList.remove('hidden');
}

function hideEditor() {
    currentEditId = null;
    elements.memoryEditor.classList.add('hidden');
    elements.memoryForm.reset();
}

function editMemory(id) {
    const memory = memories.find(m => m.id === id);
    if (memory) {
        showEditor(memory);
    }
}

async function saveMemory(event) {
    event.preventDefault();

    const memoryData = {
        title: elements.memoryTitle.value.trim(),
        content: elements.memoryContent.value.trim(),
        tags: elements.memoryTags.value.split(',').map(t => t.trim()).filter(Boolean),
    };

    try {
        if (currentEditId) {
            await sendMessage('UPDATE_MEMORY', { id: currentEditId, data: memoryData });
        } else {
            await sendMessage('CREATE_MEMORY', { data: memoryData });
        }

        hideEditor();
        await loadMemories();
    } catch (error) {
        console.error('Failed to save memory:', error);
        alert('Failed to save. Please try again.');
    }
}

// ============================================
// Context Capture
// ============================================

async function captureContext() {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        if (!tab) {
            alert('No active tab found');
            return;
        }

        const response = await chrome.tabs.sendMessage(tab.id, { type: 'CAPTURE_CONTEXT' });

        if (response && response.messages) {
            showEditor({
                title: `Conversation from ${new URL(tab.url).hostname}`,
                content: response.messages.map(m => `${m.role}: ${m.content}`).join('\n\n'),
                tags: [response.platform || 'chat'],
            });
        } else {
            alert('No context found on this page');
        }
    } catch (error) {
        console.error('Capture failed:', error);
        alert('Cannot capture from this page. Make sure you\'re on a supported AI chat.');
    }
}

// ============================================
// Sync
// ============================================

async function syncNow() {
    try {
        elements.syncIndicator.classList.add('syncing');
        elements.syncText.textContent = 'Syncing...';

        const deviceId = await getDeviceId();
        const lastSync = await getLastSyncTime();

        await sendMessage('SYNC_MEMORIES', {
            deviceId,
            lastSyncAt: lastSync,
            memories: [], // Local changes would go here
        });

        await loadMemories();
        await setLastSyncTime(new Date().toISOString());

        elements.syncIndicator.classList.remove('syncing');
        elements.syncText.textContent = 'Synced';
    } catch (error) {
        console.error('Sync failed:', error);
        elements.syncIndicator.classList.remove('syncing');
        elements.syncIndicator.classList.add('error');
        elements.syncText.textContent = 'Sync failed';
    }
}

async function getDeviceId() {
    const result = await chrome.storage.local.get(['deviceId']);
    if (result.deviceId) return result.deviceId;

    const deviceId = 'device-' + Math.random().toString(36).substring(2, 15);
    await chrome.storage.local.set({ deviceId });
    return deviceId;
}

async function getLastSyncTime() {
    const result = await chrome.storage.local.get(['lastSyncAt']);
    return result.lastSyncAt || null;
}

async function setLastSyncTime(time) {
    await chrome.storage.local.set({ lastSyncAt: time });
}

// ============================================
// Message Listener
// ============================================

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'NEW_CONTEXT_AVAILABLE') {
        showEditor({
            title: message.data.title || 'Captured Context',
            content: message.data.content,
            tags: message.data.tags || [],
        });
    }
});

// ============================================
// Event Listeners
// ============================================

elements.loginBtn?.addEventListener('click', handleLogin);
elements.captureBtn?.addEventListener('click', captureContext);
elements.addMemoryBtn?.addEventListener('click', () => showEditor());
elements.cancelBtn?.addEventListener('click', hideEditor);
elements.memoryForm?.addEventListener('submit', saveMemory);
elements.syncBtn?.addEventListener('click', syncNow);

// ============================================
// Initialization
// ============================================

async function init() {
    const isAuthenticated = await checkAuthStatus();
    if (isAuthenticated) {
        await loadMemories();
    }
}

init();
