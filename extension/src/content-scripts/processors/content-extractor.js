/**
 * Context Bridge - Fallback Content Extractor
 * 
 * Final fallback when platform adapters and auto-discovery fail.
 * Extracts raw text from main content area.
 */

class FallbackContentExtractor {
    constructor() {
        this.unwantedSelectors = [
            'nav', 'header', 'footer', 'aside',
            '.nav', '.sidebar', '.menu', '.toolbar',
            '[role="navigation"]', '[role="banner"]', '[role="contentinfo"]',
            'script', 'style', 'noscript', 'iframe',
            '.ad', '.advertisement', '[class*="ad-"]', '[class*="ads-"]',
            '.cookie', '.popup', '.modal', '.overlay',
            '[aria-hidden="true"]',
            'button', 'input', 'select', 'textarea'
        ];
    }

    /**
     * Extract main content as fallback
     * @returns {Object}
     */
    extract() {
        const mainContent = this.findMainContent();
        const rawText = this.extractText(mainContent);

        return {
            success: !!rawText,
            platform: 'unknown',
            raw: rawText,
            messages: this.attemptMessageParsing(rawText),
            confidence: 0.3,
            method: 'fallback',
            warning: 'Used fallback extraction - structure may not be optimal',
            timestamp: Date.now()
        };
    }

    /**
     * Find the main content area
     * @returns {Element}
     */
    findMainContent() {
        // Try semantic elements first
        const main = document.querySelector('main');
        if (main) return main;

        const roleMain = document.querySelector('[role="main"]');
        if (roleMain) return roleMain;

        // Try common content patterns
        const contentSelectors = [
            '#main-content',
            '#content',
            '.main-content',
            '.content',
            '[class*="conversation"]',
            '[class*="chat-container"]',
            '[class*="messages"]'
        ];

        for (const selector of contentSelectors) {
            const el = document.querySelector(selector);
            if (el && el.textContent.length > 100) return el;
        }

        // Fallback to body
        return document.body;
    }

    /**
     * Extract clean text from element
     * @param {Element} container 
     * @returns {string}
     */
    extractText(container) {
        // Clone to avoid modifying original DOM
        const clone = container.cloneNode(true);
        this.removeUnwantedElements(clone);

        return this.cleanText(clone.innerText || clone.textContent || '');
    }

    /**
     * Remove unwanted elements from container
     * @param {Element} container 
     */
    removeUnwantedElements(container) {
        for (const selector of this.unwantedSelectors) {
            try {
                const elements = container.querySelectorAll(selector);
                elements.forEach(el => el.remove());
            } catch (e) {
                // Invalid selector, skip
            }
        }
    }

    /**
     * Clean extracted text
     * @param {string} text 
     * @returns {string}
     */
    cleanText(text) {
        return text
            // Normalize whitespace
            .replace(/\s+/g, ' ')
            // Remove excessive newlines
            .replace(/\n{3,}/g, '\n\n')
            // Trim
            .trim();
    }

    /**
     * Attempt to parse messages from raw text
     * @param {string} rawText 
     * @returns {Array}
     */
    attemptMessageParsing(rawText) {
        if (!rawText || rawText.length < 50) {
            return [];
        }

        // Try to identify message boundaries
        const patterns = [
            // Common prompt patterns
            /(?:You|Human|User):\s*([\s\S]+?)(?=(?:Assistant|AI|Claude|ChatGPT|Gemini):|\n{2}You:|\n{2}Human:|$)/gi,
            /(?:Assistant|AI|Claude|ChatGPT|Gemini):\s*([\s\S]+?)(?=(?:You|Human|User):|\n{2}|$)/gi
        ];

        const messages = [];
        let isUserNext = true;

        // Split by double newlines as rough message boundaries
        const paragraphs = rawText.split(/\n{2,}/).filter(p => p.trim().length > 20);

        paragraphs.forEach((para, index) => {
            const content = para.trim();
            if (content) {
                messages.push({
                    role: index % 2 === 0 ? 'user' : 'assistant',
                    content: content,
                    platform: 'unknown'
                });
            }
        });

        return messages;
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.FallbackContentExtractor = FallbackContentExtractor;
}
