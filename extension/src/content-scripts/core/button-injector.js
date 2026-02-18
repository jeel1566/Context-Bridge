/**
 * Context Bridge - Capture Button Injector
 * 
 * Injects a floating capture button near AI platform input areas.
 * The button opens the side panel and captures context.
 */

class ButtonInjector {
    constructor() {
        this.buttonId = 'context-bridge-capture-btn';
        this.observer = null;
        this.retryAttempts = 0;
        this.maxRetries = 10;
        this.retryDelay = 1000;
    }

    /**
     * Initialize button injection
     * @param {Object} parser - DOMParser instance
     */
    init(parser) {
        this.parser = parser;
        this.injectButton();
        this.setupObserver();
    }

    /**
     * Inject the capture button into the page
     */
    injectButton() {
        // Don't duplicate
        if (document.getElementById(this.buttonId)) {
            return;
        }

        const inputSelector = this.parser?.getInputSelector() || this.findInputArea();
        if (!inputSelector) {
            // Retry later if input not found yet
            if (this.retryAttempts < this.maxRetries) {
                this.retryAttempts++;
                setTimeout(() => this.injectButton(), this.retryDelay);
            }
            return;
        }

        const inputArea = document.querySelector(inputSelector);
        if (!inputArea) {
            if (this.retryAttempts < this.maxRetries) {
                this.retryAttempts++;
                setTimeout(() => this.injectButton(), this.retryDelay);
            }
            return;
        }

        // Find the container to position relative to
        const container = this.findButtonContainer(inputArea);
        if (!container) return;

        // Create and inject button
        const button = this.createButton();
        this.positionButton(button, container);

        // Insert into DOM
        container.style.position = container.style.position || 'relative';
        container.appendChild(button);

        console.log('Context Bridge: Capture button injected');
    }

    /**
     * Find input area without parser
     * @returns {string|null}
     */
    findInputArea() {
        const selectors = [
            '#prompt-textarea',                    // ChatGPT
            '[contenteditable="true"]',            // Claude
            'rich-textarea',                       // Gemini
            'textarea[placeholder*="message"]',   // Generic
            'textarea[placeholder*="Message"]',
            'textarea[rows]'
        ];

        for (const selector of selectors) {
            if (document.querySelector(selector)) {
                return selector;
            }
        }

        return null;
    }

    /**
     * Find appropriate container for button
     * @param {Element} inputArea 
     * @returns {Element|null}
     */
    findButtonContainer(inputArea) {
        // Go up to find a suitable container
        let container = inputArea.parentElement;

        for (let i = 0; i < 5 && container; i++) {
            const rect = container.getBoundingClientRect();
            if (rect.width > 200 && rect.height > 40) {
                return container;
            }
            container = container.parentElement;
        }

        return inputArea.parentElement;
    }

    /**
     * Create the capture button element
     * @returns {HTMLElement}
     */
    createButton() {
        const button = document.createElement('button');
        button.id = this.buttonId;
        button.title = 'Capture Context with Context Bridge';
        button.setAttribute('aria-label', 'Capture Context');

        // Bridge emoji + capture icon
        button.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/>
                <circle cx="12" cy="13" r="3"/>
            </svg>
        `;

        // Apply styles
        Object.assign(button.style, {
            position: 'absolute',
            zIndex: '10000',
            width: '32px',
            height: '32px',
            padding: '6px',
            border: 'none',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
            color: 'white',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 8px rgba(99, 102, 241, 0.4)',
            transition: 'all 0.2s ease',
            opacity: '0.9'
        });

        // Hover effects
        button.addEventListener('mouseenter', () => {
            button.style.opacity = '1';
            button.style.transform = 'scale(1.05)';
            button.style.boxShadow = '0 4px 12px rgba(99, 102, 241, 0.5)';
        });

        button.addEventListener('mouseleave', () => {
            button.style.opacity = '0.9';
            button.style.transform = 'scale(1)';
            button.style.boxShadow = '0 2px 8px rgba(99, 102, 241, 0.4)';
        });

        // Click handler
        button.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.handleCapture();
        });

        return button;
    }

    /**
     * Position button relative to container
     * @param {HTMLElement} button 
     * @param {Element} container 
     */
    positionButton(button, container) {
        const position = this.parser?.getButtonPosition() || {
            style: { bottom: '12px', right: '50px' }
        };

        if (position.style) {
            Object.assign(button.style, position.style);
        } else {
            button.style.bottom = '12px';
            button.style.right = '50px';
        }
    }

    /**
     * Send a message to the background with retry for transient errors.
     * @param {Object} message
     * @param {number} retries
     */
    async sendMessageWithRetry(message, retries = 3) {
        for (let attempt = 1; attempt <= retries; attempt++) {
            try {
                return await chrome.runtime.sendMessage(message);
            } catch (error) {
                const msg = error?.message || '';
                // Context invalidated = extension was reloaded, no retry will help
                if (msg.includes('Extension context invalidated')) {
                    throw error;
                }
                const isTransient = msg.includes('Receiving end does not exist') ||
                    msg.includes('Could not establish connection');
                if (isTransient && attempt < retries) {
                    await new Promise(r => setTimeout(r, 300 * attempt));
                    continue;
                }
                throw error;
            }
        }
    }

    /**
     * Show a non-intrusive banner asking the user to refresh the page.
     */
    showRefreshBanner() {
        if (document.getElementById('cb-refresh-banner')) return;
        const banner = document.createElement('div');
        banner.id = 'cb-refresh-banner';
        Object.assign(banner.style, {
            position: 'fixed', top: '0', left: '0', right: '0', zIndex: '999999',
            background: '#fbbf24', color: '#1a1a1a', padding: '10px 16px',
            fontFamily: 'system-ui, sans-serif', fontSize: '14px', fontWeight: '600',
            textAlign: 'center', boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
        });
        banner.innerHTML = `
            ⚠️ Context Bridge was updated. Please <a href="#" id="cb-refresh-link"
                style="color:#4f46e5;text-decoration:underline;font-weight:700">refresh this page</a> to continue.
            <span id="cb-dismiss-banner" style="cursor:pointer;float:right;font-size:18px">&times;</span>
        `;
        document.body.appendChild(banner);
        document.getElementById('cb-refresh-link')?.addEventListener('click', (e) => {
            e.preventDefault(); location.reload();
        });
        document.getElementById('cb-dismiss-banner')?.addEventListener('click', () => banner.remove());
    }

    /**
     * Handle capture button click
     */
    async handleCapture() {
        const button = document.getElementById(this.buttonId);

        try {
            // Visual feedback - shrink
            if (button) {
                button.style.transform = 'scale(0.95)';
                button.style.opacity = '0.7';
                setTimeout(() => {
                    button.style.transform = 'scale(1)';
                    button.style.opacity = '0.9';
                }, 150);
            }

            // Send message to open side panel and capture (with retry for transient errors)
            await this.sendMessageWithRetry({
                type: 'CAPTURE_AND_OPEN',
                data: {
                    url: window.location.href,
                    title: document.title
                }
            });

        } catch (error) {
            console.error('Context Bridge: Capture failed', error);
            const msg = error?.message || '';

            if (msg.includes('Extension context invalidated')) {
                // Extension was reloaded — content script is orphaned
                this.showRefreshBanner();
                if (button) {
                    button.style.background = '#f59e0b';
                    button.title = 'Extension updated — please refresh this page';
                }
            } else {
                // Other error — show red feedback briefly
                if (button) {
                    const origBg = button.style.background;
                    button.style.background = '#ef4444';
                    button.title = 'Capture failed — try again';
                    setTimeout(() => {
                        button.style.background = origBg;
                        button.title = 'Capture Context with Context Bridge';
                    }, 2000);
                }
            }
        }
    }

    /**
     * Setup MutationObserver to re-inject button if needed
     */
    setupObserver() {
        this.observer = new MutationObserver((mutations) => {
            // Check if button was removed
            if (!document.getElementById(this.buttonId)) {
                this.retryAttempts = 0;
                this.injectButton();
            }
        });

        this.observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    /**
     * Remove button and cleanup
     */
    destroy() {
        const button = document.getElementById(this.buttonId);
        if (button) {
            button.remove();
        }

        if (this.observer) {
            this.observer.disconnect();
            this.observer = null;
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.ButtonInjector = ButtonInjector;
}
