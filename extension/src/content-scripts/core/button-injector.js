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
     * Handle capture button click
     */
    async handleCapture() {
        try {
            // Visual feedback
            const button = document.getElementById(this.buttonId);
            if (button) {
                button.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    button.style.transform = 'scale(1)';
                }, 150);
            }

            // Send message to open side panel and capture
            await chrome.runtime.sendMessage({
                type: 'CAPTURE_AND_OPEN',
                data: {
                    url: window.location.href,
                    title: document.title
                }
            });

        } catch (error) {
            console.error('Context Bridge: Capture failed', error);
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
