/**
 * Context Bridge - Side Panel JavaScript
 * 
 * Updated for Supabase Authentication
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
    themeToggle: $('#theme-toggle'),
    personalitySelector: $('#personality-selector'),
    sharePanel: $('#share-panel'),
    shareLink: $('#share-link'),
    copyLinkBtn: $('#copy-link-btn'),
    inviteEmail: $('#invite-email'),
    inviteBtn: $('#invite-btn'),
    closeShareBtn: $('#close-share-btn'),
};

// ============================================
// Theme Management
// ============================================

function initTheme() {
    const savedTheme = localStorage.getItem('context-bridge-theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
    } else {
        // Default to dark
        document.documentElement.setAttribute('data-theme', 'dark');
    }
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';

    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('context-bridge-theme', newTheme);

    // Also save to chrome.storage for sync across windows
    chrome.storage.local.set({ theme: newTheme });
}

// ============================================
// Personality Management
// ============================================

async function initPersonality() {
    const result = await chrome.storage.local.get(['personality']);
    if (result.personality) {
        elements.personalitySelector.value = result.personality;
    }
}

function handlePersonalityChange() {
    const personality = elements.personalitySelector.value;
    chrome.storage.local.set({ personality });
}

// ============================================
// API Communication
// ============================================

async function sendMessage(type, data = {}) {
    return chrome.runtime.sendMessage({ type, ...data });
}

// ============================================
// Authentication (Supabase)
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

        // User info from Supabase - use avatar_url or picture
        const avatarUrl = status.user.user_metadata?.avatar_url ||
            status.user.user_metadata?.picture ||
            '';
        const userName = status.user.user_metadata?.full_name ||
            status.user.user_metadata?.name ||
            status.user.email;

        elements.userAvatar.src = avatarUrl;
        elements.userName.textContent = userName;
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
        } else if (result.error) {
            throw new Error(result.error);
        }
    } catch (error) {
        console.error('Login failed:', error);
        alert('Login failed: ' + (error.message || 'Please try again.'));
    } finally {
        elements.loginBtn.disabled = false;
        elements.loginBtn.textContent = 'Login';
    }
}

async function handleLogout() {
    try {
        await sendMessage('LOGOUT');
        updateAuthUI({ isAuthenticated: false, user: null });
        memories = [];
        renderMemories();
    } catch (error) {
        console.error('Logout failed:', error);
    }
}

// Listen for auth state changes from background
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'AUTH_STATE_CHANGED') {
        if (message.event === 'SIGNED_IN' && message.session) {
            updateAuthUI({ isAuthenticated: true, user: message.session.user });
            loadMemories();
        } else if (message.event === 'SIGNED_OUT') {
            updateAuthUI({ isAuthenticated: false, user: null });
            memories = [];
            renderMemories();
        }
    } else if (message.type === 'NEW_CONTEXT_AVAILABLE') {
        showEditor({
            title: message.data.title || 'Captured Context',
            content: message.data.content,
            tags: message.data.tags || [],
        });
    }
});

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
        <div class="flex flex-col items-center justify-center h-full text-center p-4 text-muted pt-10">
            <div style="font-size: 3rem; opacity: 0.3; margin-bottom: 1rem;">🧠</div>
            <p>No memories yet.</p>
            <p class="text-xs mt-2">Open ChatGPT, Claude, or Gemini and capture context to get started.</p>
        </div>
    `;
        return;
    }

    elements.memoriesList.innerHTML = memories.map(memory => `
    <div class="memory-item" data-id="${memory.id}">
        <div class="memory-header">
            <h3>${escapeHtml(memory.title)}</h3>
            <button class="btn-icon-sm share-btn" data-id="${memory.id}" title="Share">🔗</button>
        </div>
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
        item.addEventListener('click', (e) => {
            // Don't trigger edit if share button was clicked
            if (e.target.closest('.share-btn')) return;
            editMemory(item.dataset.id);
        });
    });

    $$('.share-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            openSharePanel(btn.dataset.id);
        });
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
        personality: elements.personalitySelector.value,
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

        // Check if this is a supported URL
        const supportedPatterns = [
            /chat\.openai\.com/,
            /chatgpt\.com/,
            /claude\.ai/,
            /gemini\.google\.com/
        ];

        const isSupported = supportedPatterns.some(p => p.test(tab.url));
        if (!isSupported) {
            alert('This page is not a supported AI chat. Supported: ChatGPT, Claude, Gemini');
            return;
        }

        let response;
        try {
            // Try to send message to content script
            response = await chrome.tabs.sendMessage(tab.id, { type: 'CAPTURE_CONTEXT' });
        } catch (error) {
            // Content script not loaded - inject it first
            console.log('Content script not loaded, injecting...');

            try {
                await chrome.scripting.executeScript({
                    target: { tabId: tab.id },
                    files: [
                        'src/content-scripts/platforms/base.js',
                        'src/content-scripts/platforms/chatgpt.js',
                        'src/content-scripts/platforms/claude.js',
                        'src/content-scripts/platforms/gemini.js',
                        'src/content-scripts/core/auto-discovery.js',
                        'src/content-scripts/processors/content-extractor.js',
                        'src/content-scripts/core/parser.js',
                        'src/content-scripts/core/button-injector.js',
                        'src/content-scripts/core/observer.js'
                    ]
                });

                // Wait for scripts to initialize
                await new Promise(resolve => setTimeout(resolve, 1000));

                // Try again
                response = await chrome.tabs.sendMessage(tab.id, { type: 'CAPTURE_CONTEXT' });
            } catch (injectError) {
                console.error('Script injection failed:', injectError);
                alert('Failed to initialize capture. Please refresh the page and try again.');
                return;
            }
        }

        if (response && response.messages && response.messages.length > 0) {
            const platform = response.platform || new URL(tab.url).hostname.replace('www.', '').split('.')[0];
            const platformNames = { chatgpt: 'ChatGPT', claude: 'Claude', gemini: 'Gemini' };
            const displayName = platformNames[platform] || platform;
            const timestamp = new Date().toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

            showEditor({
                title: `${displayName} Conversation - ${timestamp} `,
                content: response.messages.map(m => `${m.role}: ${m.content} `).join('\n\n'),
                tags: [platform, 'conversation'],
            });
        } else {
            alert('No conversation found on this page. Make sure there are messages in the chat.');
        }
    } catch (error) {
        console.error('Capture failed:', error);
        alert('Capture failed. Please refresh the ChatGPT/Claude/Gemini page and try again.');
    }
}

// ============================================
// Share Functionality
// ============================================

function openSharePanel(memoryId) {
    const memory = memories.find(m => m.id === memoryId);
    if (!memory) return;

    // Mock link generation
    const mockLink = `https://context-bridge.web.app/share/${memoryId}`;
    elements.shareLink.value = mockLink;
    elements.inviteEmail.value = '';

    elements.sharePanel.classList.remove('hidden');
    // Hide other panels if needed, or just overlay
    elements.memoryEditor.classList.add('hidden');
}

function closeSharePanel() {
    elements.sharePanel.classList.add('hidden');
}

function copyShareLink() {
    elements.shareLink.select();
    document.execCommand('copy');

    const originalText = elements.copyLinkBtn.textContent;
    elements.copyLinkBtn.textContent = 'Copied!';
    setTimeout(() => {
        elements.copyLinkBtn.textContent = originalText;
    }, 2000);
}

async function sendInvite() {
    const email = elements.inviteEmail.value.trim();
    if (!email) return;

    elements.inviteBtn.textContent = 'Sending...';
    elements.inviteBtn.disabled = true;

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));

    alert(`Invite sent to ${email}`);

    elements.inviteBtn.textContent = 'Invite';
    elements.inviteBtn.disabled = false;
    elements.inviteEmail.value = '';
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
            memories: [],
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
// Event Listeners
// ============================================

elements.loginBtn?.addEventListener('click', handleLogin);
elements.captureBtn?.addEventListener('click', captureContext);
elements.addMemoryBtn?.addEventListener('click', () => showEditor());
elements.cancelBtn?.addEventListener('click', hideEditor);
elements.memoryForm?.addEventListener('submit', saveMemory);
elements.syncBtn?.addEventListener('click', syncNow);
elements.themeToggle?.addEventListener('click', toggleTheme);
elements.personalitySelector?.addEventListener('change', handlePersonalityChange);
elements.closeShareBtn?.addEventListener('click', closeSharePanel);
elements.copyLinkBtn?.addEventListener('click', copyShareLink);
elements.inviteBtn?.addEventListener('click', sendInvite);

// Add logout handler to user info area (click on user avatar to logout)
elements.userInfo?.addEventListener('click', () => {
    if (confirm('Do you want to sign out?')) {
        handleLogout();
    }
});

// ============================================
// Initialization
// ============================================

async function init() {
    // Initialize theme
    initTheme();
    initPersonality();

    // Check auth and load data
    const isAuthenticated = await checkAuthStatus();
    if (isAuthenticated) {
        await loadMemories();
    }
}

init();
