/**
 * Context Bridge - Platform Adapter Base Class
 * 
 * Base class for platform-specific conversation parsers.
 * Each platform (ChatGPT, Claude, Gemini) extends this class.
 */

class PlatformAdapter {
    constructor() {
        this.platformName = 'unknown';
        this.urlPattern = null;
        this.versions = {};
    }

    /**
     * Detect if this adapter applies to current platform
     * @returns {boolean}
     */
    detect() {
        if (!this.urlPattern) return false;
        return this.urlPattern.test(window.location.href);
    }

    /**
     * Detect which version of the platform UI is present
     * @returns {string} Version identifier
     */
    detectVersion() {
        return 'latest';
    }

    /**
     * Get versioned selector configuration
     * @param {string} version 
     * @returns {Object} Selector configuration
     */
    getSelectors(version = 'latest') {
        return this.versions[version] || this.versions[Object.keys(this.versions)[0]];
    }

    /**
     * Parse conversation from current platform
     * @param {Object} selectors - Optional selector overrides
     * @returns {Array|null} Array of message objects or null
     */
    parse(selectors = null) {
        throw new Error('parse() must be implemented by subclass');
    }

    /**
     * Get confidence score for this adapter (0-1)
     * Higher confidence means selectors are more reliable
     * @returns {number}
     */
    getConfidence() {
        return this.detect() ? 0.5 : 0;
    }

    /**
     * Extract timestamp from a message element
     * @param {Element} element 
     * @returns {string|null}
     */
    extractTimestamp(element) {
        const timeEl = element.querySelector('time');
        if (timeEl) {
            return timeEl.getAttribute('datetime') || timeEl.textContent;
        }
        const timestamp = element.getAttribute('data-timestamp');
        return timestamp || null;
    }

    /**
     * Get the input area selector for button positioning
     * @returns {string}
     */
    getInputSelector() {
        return null;
    }

    /**
     * Get button positioning config relative to input area
     * @returns {Object}
     */
    getButtonPosition() {
        return { position: 'right', offset: 8 };
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.PlatformAdapter = PlatformAdapter;
}
