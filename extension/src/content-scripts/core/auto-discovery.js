/**
 * Context Bridge - Auto-Discovering Parser
 * 
 * Auto-discovers conversation structure on unknown platforms
 * without requiring hard-coded selectors.
 */

class AutoDiscoveringParser {
    constructor() {
        this.minMessageLength = 20;
        this.maxCandidates = 100;
        this.confidenceThreshold = 0.7;
    }

    /**
     * Main discovery entry point
     * @returns {Object} Discovery result
     */
    async discover() {
        try {
            const candidates = await this.findTextCandidates();

            if (candidates.length < 2) {
                return {
                    success: false,
                    confidence: 0,
                    reason: 'Not enough text candidates found'
                };
            }

            const groups = this.groupByStructure(candidates);
            const pattern = this.identifyConversationPattern(groups);

            if (!pattern) {
                return {
                    success: false,
                    confidence: 0,
                    reason: 'No conversation pattern identified'
                };
            }

            const selectors = this.generateSelectors(pattern);
            const messages = this.extractMessages(pattern, selectors);
            const confidence = this.calculateConfidence(messages, pattern);

            return {
                success: confidence >= this.confidenceThreshold,
                confidence: confidence,
                selectors: selectors,
                messages: messages,
                method: 'auto-discovery',
                timestamp: Date.now()
            };
        } catch (error) {
            console.error('Auto-discovery failed:', error);
            return {
                success: false,
                confidence: 0,
                error: error.message
            };
        }
    }

    /**
     * Find potential message text candidates
     * @returns {Array<Element>}
     */
    async findTextCandidates() {
        const allElements = await this.querySelectorAllDeep('*');

        return allElements
            .filter(el => this.isMessageCandidate(el))
            .slice(0, this.maxCandidates);
    }

    /**
     * Query selector with Shadow DOM traversal
     * @param {string} selector 
     * @param {Element} root 
     * @returns {Array<Element>}
     */
    async querySelectorAllDeep(selector, root = document.body) {
        const results = [];
        const stack = [root];

        while (stack.length && results.length < this.maxCandidates) {
            const node = stack.pop();

            if (node.matches && node.matches(selector)) {
                results.push(node);
            }

            // Traverse shadow DOM
            if (node.shadowRoot) {
                stack.push(node.shadowRoot);
            }

            // Traverse children
            const children = node.children || [];
            for (const child of Array.from(children)) {
                stack.push(child);
                if (child.shadowRoot) {
                    stack.push(child.shadowRoot);
                }
            }
        }

        return results;
    }

    /**
     * Check if an element is a potential message candidate
     * @param {Element} element 
     * @returns {boolean}
     */
    isMessageCandidate(element) {
        // Skip interactive elements
        if (this.isInteractive(element)) return false;

        // Skip navigation/sidebar elements
        if (this.isNavigation(element)) return false;

        // Skip hidden elements
        if (this.isHidden(element)) return false;

        const text = element.textContent?.trim() || '';

        // Check minimum length
        if (text.length < this.minMessageLength) return false;

        // Skip if mostly code content
        const codeRatio = this.getCodeRatio(element);
        if (codeRatio > 0.8) return false;

        // Skip if it's just whitespace or repeated characters
        if (/^[\s\n\r]+$/.test(text)) return false;

        return true;
    }

    /**
     * Check if element is interactive
     * @param {Element} element 
     * @returns {boolean}
     */
    isInteractive(element) {
        const interactiveTags = ['BUTTON', 'INPUT', 'SELECT', 'TEXTAREA', 'A'];
        if (interactiveTags.includes(element.tagName)) return true;

        if (element.onclick || element.getAttribute('role') === 'button') return true;
        if (element.getAttribute('contenteditable') === 'true') return true;

        return false;
    }

    /**
     * Check if element is navigation
     * @param {Element} element 
     * @returns {boolean}
     */
    isNavigation(element) {
        const navRoles = ['navigation', 'banner', 'complementary', 'contentinfo'];
        if (navRoles.includes(element.getAttribute('role'))) return true;

        const navClasses = ['nav', 'sidebar', 'menu', 'header', 'footer', 'toolbar'];
        const className = element.className?.toLowerCase() || '';
        if (navClasses.some(c => className.includes(c))) return true;

        const navTags = ['NAV', 'HEADER', 'FOOTER', 'ASIDE'];
        if (navTags.includes(element.tagName)) return true;

        return false;
    }

    /**
     * Check if element is hidden
     * @param {Element} element 
     * @returns {boolean}
     */
    isHidden(element) {
        if (element.hidden) return true;

        const style = window.getComputedStyle(element);
        if (style.display === 'none' || style.visibility === 'hidden') return true;
        if (style.opacity === '0') return true;

        return false;
    }

    /**
     * Get ratio of code content in element
     * @param {Element} element 
     * @returns {number}
     */
    getCodeRatio(element) {
        const codeElements = element.querySelectorAll('pre, code');
        const totalText = element.textContent?.length || 1;
        const codeText = Array.from(codeElements)
            .reduce((sum, el) => sum + (el.textContent?.length || 0), 0);
        return codeText / totalText;
    }

    /**
     * Group elements by DOM structure similarity
     * @param {Array<Element>} elements 
     * @returns {Map}
     */
    groupByStructure(elements) {
        const groups = new Map();

        for (const el of elements) {
            const signature = this.getParentSignature(el);

            if (!groups.has(signature)) {
                groups.set(signature, []);
            }
            groups.get(signature).push(el);
        }

        // Sort by group size (largest first)
        return new Map([...groups.entries()].sort((a, b) => b[1].length - a[1].length));
    }

    /**
     * Get a signature for element's parent structure
     * @param {Element} element 
     * @returns {string}
     */
    getParentSignature(element) {
        const parent = element.parentElement;
        if (!parent) return 'root';

        const attrs = ['id', 'data-testid', 'data-test', 'role', 'aria-label'];
        const parts = [];

        for (const attr of attrs) {
            const value = parent.getAttribute(attr);
            if (value) {
                parts.push(`${attr}=${value}`);
            }
        }

        // Include class hash for non-specific elements
        if (parts.length === 0) {
            const classes = parent.className?.split(' ').slice(0, 3).join('.') || '';
            parts.push(`class=${classes}`);
        }

        return parts.join(';') || 'default';
    }

    /**
     * Identify conversation patterns in groups
     * @param {Map} groups 
     * @returns {Object|null}
     */
    identifyConversationPattern(groups) {
        for (const [signature, elements] of groups) {
            if (elements.length < 2) continue;

            const texts = elements.map(el => ({
                element: el,
                text: el.textContent?.trim() || '',
                length: el.textContent?.trim()?.length || 0
            }));

            if (this.isConversationPattern(texts)) {
                return {
                    containerSignature: signature,
                    elements: texts,
                    messageCount: elements.length
                };
            }
        }

        return null;
    }

    /**
     * Check if texts represent a conversation pattern
     * @param {Array} texts 
     * @returns {boolean}
     */
    isConversationPattern(texts) {
        if (texts.length < 2) return false;

        // Calculate variance in message lengths
        const avgLength = texts.reduce((sum, t) => sum + t.length, 0) / texts.length;
        const variance = texts.reduce((sum, t) =>
            sum + Math.pow(t.length - avgLength, 2), 0) / texts.length;

        // High variance suggests conversation (short user + long assistant)
        // But also accept lower variance if there are enough messages
        return (variance > 500 && texts.length >= 2) ||
            (texts.length >= 4 && avgLength > 50);
    }

    /**
     * Generate selectors from pattern
     * @param {Object} pattern 
     * @returns {Object}
     */
    generateSelectors(pattern) {
        if (!pattern.elements.length) {
            return { container: null, message: null, fallbackSelectors: [] };
        }

        const representative = pattern.elements[0].element;

        return {
            container: this.generateContainerSelector(representative),
            message: this.generateMessageSelector(representative),
            fallbackSelectors: this.generateFallbackSelectors(representative)
        };
    }

    /**
     * Generate container selector
     * @param {Element} element 
     * @returns {string|null}
     */
    generateContainerSelector(element) {
        const parent = element.parentElement;
        if (!parent) return null;

        // Try data attributes first (most stable)
        for (const attr of ['data-testid', 'data-test', 'data-id']) {
            if (parent.hasAttribute(attr)) {
                return `[${attr}="${parent.getAttribute(attr)}"]`;
            }
        }

        // Try id
        if (parent.id) {
            return `#${parent.id}`;
        }

        // Try class-based selector
        const classes = parent.className?.split(' ').filter(c => c.length > 2 && !c.includes('_'));
        if (classes?.length) {
            return `.${classes.slice(0, 2).join('.')}`;
        }

        return null;
    }

    /**
     * Generate message selector
     * @param {Element} element 
     * @returns {string|null}
     */
    generateMessageSelector(element) {
        // Try data attributes
        for (const attr of ['data-message-author-role', 'data-testid', 'data-role', 'data-message-id']) {
            if (element.hasAttribute(attr)) {
                return `[${attr}]`;
            }
        }

        // Try specific class patterns
        const className = element.className || '';
        if (className.includes('message')) {
            return '[class*="message"]';
        }

        return null;
    }

    /**
     * Generate fallback selectors
     * @param {Element} element 
     * @returns {Array<string>}
     */
    generateFallbackSelectors(element) {
        return [
            '[class*="message"]',
            '[class*="turn"]',
            '[class*="conversation"]',
            '[class*="chat"]',
            'article',
            '[role="article"]',
            '[role="log"]',
            '[data-test-render-count]'
        ];
    }

    /**
     * Extract messages from pattern
     * @param {Object} pattern 
     * @param {Object} selectors 
     * @returns {Array}
     */
    extractMessages(pattern, selectors) {
        return pattern.elements.map((e, index) => ({
            role: this.detectRole(e.element, index),
            content: e.text,
            timestamp: this.extractTimestamp(e.element)
        }));
    }

    /**
     * Detect message role
     * @param {Element} element 
     * @param {number} index 
     * @returns {string}
     */
    detectRole(element, index) {
        // Check data attributes
        const roleAttr = element.getAttribute('data-message-author-role') ||
            element.getAttribute('data-role');
        if (roleAttr) return roleAttr;

        // Check class patterns
        const className = element.className?.toLowerCase() || '';
        if (className.includes('user') || className.includes('human')) return 'user';
        if (className.includes('assistant') || className.includes('bot') || className.includes('ai')) return 'assistant';

        // Check parent for role
        const parent = element.closest('[data-message-author-role]');
        if (parent) return parent.getAttribute('data-message-author-role');

        // Fallback to position-based (alternating)
        return index % 2 === 0 ? 'user' : 'assistant';
    }

    /**
     * Extract timestamp from element
     * @param {Element} element 
     * @returns {string|null}
     */
    extractTimestamp(element) {
        const timeElement = element.querySelector('time');
        if (timeElement) {
            return timeElement.getAttribute('datetime') || timeElement.textContent;
        }

        const timestamp = element.getAttribute('data-timestamp');
        return timestamp || null;
    }

    /**
     * Calculate confidence score
     * @param {Array} messages 
     * @param {Object} pattern 
     * @returns {number}
     */
    calculateConfidence(messages, pattern) {
        let score = 0;

        // Has minimum messages
        if (messages.length >= 2) score += 0.2;
        if (messages.length >= 5) score += 0.1;

        // Role detection accuracy
        const knownRoles = messages.filter(m => m.role !== 'unknown').length;
        if (knownRoles / messages.length > 0.8) score += 0.3;

        // Content quality
        const avgLength = messages.reduce((sum, m) => sum + m.content.length, 0) / messages.length;
        if (avgLength > 50) score += 0.2;
        if (avgLength > 200) score += 0.1;

        // Pattern consistency
        if (pattern.messageCount === messages.length) score += 0.1;

        return Math.min(score, 1);
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.AutoDiscoveringParser = AutoDiscoveringParser;
}
