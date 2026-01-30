/**
 * Context Bridge - ChatGPT Platform Adapter
 * 
 * Parses conversations from chat.openai.com
 */

class ChatGPTAdapter extends PlatformAdapter {
    constructor() {
        super();
        this.platformName = 'chatgpt';
        this.urlPattern = /(chat\.openai\.com|chatgpt\.com)/;

        this.versions = {
            'latest': {
                selectors: {
                    container: '[data-testid="conversation-turn"]',
                    message: '[data-message-author-role]',
                    role: 'data-message-author-role',
                    content: '.markdown',
                    input: '#prompt-textarea'
                }
            },
            '2024-01': {
                selectors: {
                    container: '[data-message-author-role]',
                    message: '[data-message-author-role]',
                    role: 'data-message-author-role',
                    content: '.markdown',
                    input: '#prompt-textarea'
                }
            }
        };
    }

    detectVersion() {
        const container = document.querySelector('[data-testid="conversation-turn"]');
        return container ? 'latest' : '2024-01';
    }

    getConfidence() {
        if (!this.detect()) return 0;

        const container = document.querySelector('[data-testid="conversation-turn"]');
        if (container) return 0.95;

        const message = document.querySelector('[data-message-author-role]');
        return message ? 0.85 : 0.7;
    }

    parse(selectors = null) {
        const config = selectors || this.getSelectors(this.detectVersion());
        const containers = document.querySelectorAll(config.selectors.container);

        if (!containers.length) {
            return null;
        }

        const messages = [];

        containers.forEach(container => {
            const roleEl = container.querySelector(`[${config.selectors.role}]`);
            const role = roleEl?.dataset?.messageAuthorRole ||
                container.getAttribute(config.selectors.role);

            const contentEl = container.querySelector(config.selectors.content);
            const content = contentEl?.textContent?.trim() || container.textContent?.trim() || '';

            if (content && content.length > 0) {
                messages.push({
                    role: role || 'unknown',
                    content: content,
                    platform: 'chatgpt',
                    timestamp: this.extractTimestamp(container)
                });
            }
        });

        return messages.length > 0 ? messages : null;
    }

    getInputSelector() {
        const version = this.detectVersion();
        return this.versions[version].selectors.input;
    }

    getButtonPosition() {
        return {
            position: 'right',
            offset: 8,
            // ChatGPT has the input at the bottom with send button on right
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
    window.ChatGPTAdapter = ChatGPTAdapter;
}
