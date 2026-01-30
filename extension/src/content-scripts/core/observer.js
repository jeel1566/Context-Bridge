/**
 * Context Bridge - Content Script Observer
 * 
 * Observes AI chat interfaces and captures context.
 * Supports: ChatGPT, Claude, Gemini + auto-discovery for others
 */

// Global parser instance
let parser = null;
let buttonInjector = null;
let observer = null;

// ============================================
// Initialization
// ============================================

function initParser() {
    console.log('Context Bridge: Initializing parser...');

    // Create and initialize parser
    parser = new ContextBridgeParser();
    parser.init();

    // Initialize button injector
    buttonInjector = new ButtonInjector();
    buttonInjector.init(parser);

    const platform = parser.getDetectedPlatform();
    if (platform) {
        console.log(`Context Bridge: Detected platform - ${platform}`);
    } else {
        console.log('Context Bridge: No platform detected, using auto-discovery mode');
    }

    console.log('Context Bridge: Parser initialized successfully');
}

// ============================================
// Context Capture
// ============================================

async function captureContext() {
    if (!parser) {
        initParser();
    }

    try {
        const result = await parser.parse();

        if (!result || !result.success) {
            console.log('Context Bridge: No content captured');
            return null;
        }

        return {
            platform: result.platform,
            url: window.location.href,
            timestamp: new Date().toISOString(),
            messages: result.messages,
            confidence: result.confidence,
            method: result.method
        };
    } catch (error) {
        console.error('Context Bridge: Capture error', error);
        return null;
    }
}

function captureSelectedText() {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) return null;

    return {
        platform: parser?.getDetectedPlatform() || 'unknown',
        url: window.location.href,
        timestamp: new Date().toISOString(),
        selectedText: selection.toString().trim(),
        type: 'selection'
    };
}

// ============================================
// Message Handling
// ============================================

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    handleMessage(message)
        .then(sendResponse)
        .catch(error => sendResponse({ error: error.message }));
    return true; // Keep channel open for async
});

async function handleMessage(message) {
    switch (message.type) {
        case 'CAPTURE_CONTEXT':
            return captureContext();

        case 'CAPTURE_SELECTION':
            return captureSelectedText();

        case 'GET_PLATFORM':
            return parser?.getDetectedPlatform() || null;

        case 'REFRESH_BUTTON':
            if (buttonInjector) {
                buttonInjector.destroy();
                buttonInjector.init(parser);
            }
            return { success: true };

        default:
            return { error: 'Unknown message type' };
    }
}

// ============================================
// DOM Observer
// ============================================

function setupObserver() {
    observer = new MutationObserver((mutations) => {
        let hasNewContent = false;

        for (const mutation of mutations) {
            if (mutation.addedNodes.length > 0) {
                hasNewContent = true;
                break;
            }
        }

        if (hasNewContent) {
            debouncedNotify();

            // Clear parser cache on DOM changes
            if (parser) {
                parser.clearCache();
            }
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

let notifyTimeout = null;
function debouncedNotify() {
    if (notifyTimeout) clearTimeout(notifyTimeout);
    notifyTimeout = setTimeout(() => {
        chrome.runtime.sendMessage({
            type: 'CONTEXT_UPDATED',
            data: { platform: parser?.getDetectedPlatform() }
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
                    title: `Selection from ${parser?.getDetectedPlatform() || 'page'}`,
                    content: selection.selectedText,
                    autoSave: false
                }
            }).catch(console.error);
        }
    }

    // Ctrl/Cmd + Shift + C = Capture full context
    if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'c') {
        event.preventDefault();
        captureContext().then(context => {
            if (context && context.messages) {
                chrome.runtime.sendMessage({
                    type: 'CAPTURED_CONTEXT',
                    data: {
                        title: `Conversation from ${context.platform || 'chat'}`,
                        content: JSON.stringify(context.messages, null, 2),
                        autoSave: false
                    }
                }).catch(console.error);
            }
        });
    }
});

// ============================================
// Main Initialization
// ============================================

console.log('Context Bridge: Content script loaded on', window.location.href);

function init() {
    console.log('Context Bridge: Starting initialization...');
    // Wait a bit for dynamic content to load
    setTimeout(() => {
        try {
            initParser();
            setupObserver();
            console.log('Context Bridge: Fully initialized');
        } catch (error) {
            console.error('Context Bridge: Init error', error);
        }
    }, 500);
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
