/**
 * Context Bridge - Gemini Platform Adapter
 * 
 * Parses conversations from gemini.google.com
 */

class GeminiAdapter extends PlatformAdapter {
    constructor() {
        super();
        this.platformName = 'gemini';
        this.urlPattern = /gemini\.google\.com/;

        this.versions = {
            'latest': {
                selectors: {
                    container: 'message-content',
                    conversationContainer: '.conversation-container',
                    userMessage: 'user-query',
                    assistantMessage: 'model-response',
                    input: 'rich-textarea'
                }
            }
        };
    }

    detectVersion() {
        return 'latest';
    }

    getConfidence() {
        if (!this.detect()) return 0;

        const messageContent = document.querySelector('message-content');
        if (messageContent) return 0.9;

        const userQuery = document.querySelector('user-query');
        return userQuery ? 0.85 : 0.7;
    }

    parse(selectors = null) {
        const config = selectors || this.getSelectors();

        // Try to find message-content elements first
        let messages = this.parseMessageContent(config);
        if (messages && messages.length > 0) {
            return messages;
        }

        // Fallback to user-query and model-response elements
        return this.parseUserModelPairs(config);
    }

    parseMessageContent(config) {
        const elements = document.querySelectorAll(config.selectors.container);

        if (!elements.length) return null;

        const messages = [];

        elements.forEach((el, index) => {
            const content = el.textContent?.trim() || '';

            if (content && content.length > 0) {
                // Gemini alternates: user (even index), assistant (odd index)
                messages.push({
                    role: index % 2 === 0 ? 'user' : 'assistant',
                    content: content,
                    platform: 'gemini',
                    timestamp: null
                });
            }
        });

        return messages.length > 0 ? messages : null;
    }

    parseUserModelPairs(config) {
        const messages = [];

        // Get user queries
        const userQueries = document.querySelectorAll('user-query');
        userQueries.forEach(query => {
            const content = query.textContent?.trim() || '';
            if (content) {
                messages.push({
                    role: 'user',
                    content: content,
                    platform: 'gemini',
                    timestamp: null
                });
            }
        });

        // Get model responses
        const modelResponses = document.querySelectorAll('model-response');
        modelResponses.forEach(response => {
            const content = response.textContent?.trim() || '';
            if (content) {
                messages.push({
                    role: 'assistant',
                    content: content,
                    platform: 'gemini',
                    timestamp: null
                });
            }
        });

        // Interleave if we have both - assume alternating pattern
        if (userQueries.length > 0 && modelResponses.length > 0) {
            const interleaved = [];
            const maxLen = Math.max(userQueries.length, modelResponses.length);

            for (let i = 0; i < maxLen; i++) {
                if (i < userQueries.length) {
                    const content = userQueries[i].textContent?.trim();
                    if (content) {
                        interleaved.push({
                            role: 'user',
                            content: content,
                            platform: 'gemini',
                            timestamp: null
                        });
                    }
                }
                if (i < modelResponses.length) {
                    const content = modelResponses[i].textContent?.trim();
                    if (content) {
                        interleaved.push({
                            role: 'assistant',
                            content: content,
                            platform: 'gemini',
                            timestamp: null
                        });
                    }
                }
            }
            return interleaved.length > 0 ? interleaved : null;
        }

        return messages.length > 0 ? messages : null;
    }

    getInputSelector() {
        return 'rich-textarea';
    }

    getButtonPosition() {
        return {
            position: 'right',
            offset: 8,
            anchor: 'input-container',
            style: {
                bottom: '12px',
                right: '80px'
            }
        };
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.GeminiAdapter = GeminiAdapter;
}
