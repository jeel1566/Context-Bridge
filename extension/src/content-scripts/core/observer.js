/**
 * Context Bridge - Content Script Observer
 * 
 * Observes AI chat interfaces and captures context.
 * Supports: ChatGPT, Claude, Gemini
 */

// Platform detection
const platforms = {
    chatgpt: {
        match: /chat\.openai\.com/,
        messageSelector: '[data-message-author-role]',
        inputSelector: '#prompt-textarea',
    },
    claude: {
        match: /claude\.ai/,
        messageSelector: '[data-test-render-count]',
        inputSelector: '[contenteditable="true"]',
    },
    gemini: {
        match: /gemini\.google\.com/,
        messageSelector: 'message-content',
        inputSelector: 'rich-textarea',
    },
};

let currentPlatform = null;
let observer = null;

// ============================================
// Platform Detection
// ============================================

function detectPlatform() {
    const url = window.location.href;

    for (const [name, config] of Object.entries(platforms)) {
        if (config.match.test(url)) {
            return { name, config };
        }
    }

    return null;
}

// ============================================
// Context Capture
// ============================================

function captureContext() {
    if (!currentPlatform) return null;

    const { config } = currentPlatform;
    const messages = document.querySelectorAll(config.messageSelector);

    if (!messages.length) return null;

    const contextData = {
        platform: currentPlatform.name,
        url: window.location.href,
        timestamp: new Date().toISOString(),
        messages: [],
    };

    messages.forEach((msg, index) => {
        const role = msg.dataset?.messageAuthorRole ||
            (index % 2 === 0 ? 'user' : 'assistant');
        const content = msg.textContent?.trim() || '';

        if (content) {
            contextData.messages.push({ role, content });
        }
    });

    return contextData;
}

function captureSelectedText() {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) return null;

    return {
        platform: currentPlatform?.name || 'unknown',
        url: window.location.href,
        timestamp: new Date().toISOString(),
        selectedText: selection.toString().trim(),
        type: 'selection',
    };
}

// ============================================
// Message Handling
// ============================================

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    switch (message.type) {
        case 'CAPTURE_CONTEXT':
            sendResponse(captureContext());
            break;

        case 'CAPTURE_SELECTION':
            sendResponse(captureSelectedText());
            break;

        case 'GET_PLATFORM':
            sendResponse(currentPlatform ? currentPlatform.name : null);
            break;

        default:
            sendResponse({ error: 'Unknown message type' });
    }
    return true;
});

// ============================================
// DOM Observer
// ============================================

function setupObserver() {
    if (!currentPlatform) return;

    const { config } = currentPlatform;

    // Observe for new messages
    observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            if (mutation.addedNodes.length > 0) {
                // New content added - might be a new message
                // Debounce and notify background if needed
                debouncedNotify();
            }
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true,
    });
}

let notifyTimeout = null;
function debouncedNotify() {
    if (notifyTimeout) clearTimeout(notifyTimeout);
    notifyTimeout = setTimeout(() => {
        // Notify background about potential new context
        chrome.runtime.sendMessage({
            type: 'CONTEXT_UPDATED',
            data: { platform: currentPlatform?.name },
        }).catch(() => { });
    }, 1000);
}

// ============================================
// Keyboard Shortcuts
// ============================================

document.addEventListener('keydown', (event) => {
    // Ctrl/Cmd + Shift + S = Save selection as memory
    if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 's') {
        event.preventDefault();
        const selection = captureSelectedText();
        if (selection) {
            chrome.runtime.sendMessage({
                type: 'CAPTURED_CONTEXT',
                data: {
                    title: `Selection from ${currentPlatform?.name || 'page'}`,
                    content: selection.selectedText,
                    autoSave: false,
                },
            }).catch(console.error);
        }
    }

    // Ctrl/Cmd + Shift + C = Capture full context
    if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'c') {
        event.preventDefault();
        const context = captureContext();
        if (context) {
            chrome.runtime.sendMessage({
                type: 'CAPTURED_CONTEXT',
                data: {
                    title: `Conversation from ${currentPlatform?.name || 'chat'}`,
                    content: JSON.stringify(context.messages, null, 2),
                    autoSave: false,
                },
            }).catch(console.error);
        }
    }
});

// ============================================
// Initialization
// ============================================

function init() {
    currentPlatform = detectPlatform();

    if (currentPlatform) {
        console.log(`Context Bridge: Detected ${currentPlatform.name}`);
        setupObserver();
    } else {
        console.log('Context Bridge: No supported platform detected');
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
