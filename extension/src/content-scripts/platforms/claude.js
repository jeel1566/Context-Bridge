/**
 * Context Bridge - Claude Platform Adapter
 * 
 * Parses conversations from claude.ai
 */

class ClaudeAdapter extends PlatformAdapter {
    constructor() {
        super();
        this.platformName = 'claude';
        this.urlPattern = /claude\.ai/;

        this.versions = {
            'latest': {
                selectors: {
                    container: '[data-testid="conversation-turn"]',
                    message: '[data-test-render-count]',
                    humanMessage: '[class*="human"]',
                    assistantMessage: '[class*="assistant"]',
                    content: '[class*="content"]',
                    input: '[contenteditable="true"]'
                }
            },
            'legacy': {
                selectors: {
                    container: '[data-test-render-count]',
                    message: '[data-test-render-count]',
                    content: null,
                    input: '[contenteditable="true"]'
                }
            }
        };
    }

    detectVersion() {
        const turn = document.querySelector('[data-testid="conversation-turn"]');
        return turn ? 'latest' : 'legacy';
    }

    getConfidence() {
        if (!this.detect()) return 0;

        const turn = document.querySelector('[data-testid="conversation-turn"]');
        if (turn) return 0.95;

        const renderCount = document.querySelector('[data-test-render-count]');
        return renderCount ? 0.85 : 0.7;
    }

    parse(selectors = null) {
        const config = selectors || this.getSelectors(this.detectVersion());

        // Try latest selectors first
        let containers = document.querySelectorAll(config.selectors.container);

        if (!containers.length) {
            return this.legacyParse();
        }

        const messages = [];

        containers.forEach(container => {
            const role = this.detectRole(container);
            const content = container.textContent?.trim() || '';

            if (content && content.length > 0) {
                messages.push({
                    role: role,
                    content: content,
                    platform: 'claude',
                    timestamp: this.extractTimestamp(container)
                });
            }
        });

        return messages.length > 0 ? messages : null;
    }

    detectRole(element) {
        const className = element.className?.toLowerCase() || '';

        // Check class patterns
        if (className.includes('human') || className.includes('user')) {
            return 'user';
        }
        if (className.includes('assistant') || className.includes('claude')) {
            return 'assistant';
        }

        // Check parent classes
        const parent = element.parentElement;
        if (parent) {
            const parentClass = parent.className?.toLowerCase() || '';
            if (parentClass.includes('human') || parentClass.includes('user')) {
                return 'user';
            }
            if (parentClass.includes('assistant') || parentClass.includes('claude')) {
                return 'assistant';
            }
        }

        // Check for data attributes
        const dataRole = element.getAttribute('data-role');
        if (dataRole) return dataRole;

        return 'unknown';
    }

    legacyParse() {
        // Fallback for older Claude versions - use position-based detection
        const messages = document.querySelectorAll('[data-test-render-count]');

        if (!messages.length) return null;

        return Array.from(messages).map((msg, index) => ({
            role: index % 2 === 0 ? 'user' : 'assistant',
            content: msg.textContent?.trim() || '',
            platform: 'claude',
            timestamp: null
        })).filter(m => m.content.length > 0);
    }

    getInputSelector() {
        return '[contenteditable="true"]';
    }

    getButtonPosition() {
        return {
            position: 'right',
            offset: 8,
            anchor: 'input-container',
            style: {
                bottom: '12px',
                right: '60px'
            }
        };
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.ClaudeAdapter = ClaudeAdapter;
}
