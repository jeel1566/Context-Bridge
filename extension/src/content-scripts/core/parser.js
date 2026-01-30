/**
 * Context Bridge - DOM Parser Orchestrator
 * 
 * Coordinates between platform adapters and auto-discovery.
 * Entry point for all context capture operations.
 */

class ContextBridgeParser {
    constructor() {
        this.adapters = new Map();
        this.autoDiscoverer = null;
        this.fallbackExtractor = null;
        this.cache = new Map();
        this.cacheTTL = 60000; // 1 minute cache
    }

    /**
     * Initialize the parser with all adapters
     */
    init() {
        // Register platform adapters
        if (typeof ChatGPTAdapter !== 'undefined') {
            this.registerAdapter(new ChatGPTAdapter());
        }
        if (typeof ClaudeAdapter !== 'undefined') {
            this.registerAdapter(new ClaudeAdapter());
        }
        if (typeof GeminiAdapter !== 'undefined') {
            this.registerAdapter(new GeminiAdapter());
        }

        // Initialize auto-discoverer
        if (typeof AutoDiscoveringParser !== 'undefined') {
            this.autoDiscoverer = new AutoDiscoveringParser();
        }

        // Initialize fallback extractor
        if (typeof FallbackContentExtractor !== 'undefined') {
            this.fallbackExtractor = new FallbackContentExtractor();
        }
    }

    /**
     * Register a platform adapter
     * @param {PlatformAdapter} adapter 
     */
    registerAdapter(adapter) {
        this.adapters.set(adapter.platformName, adapter);
    }

    /**
     * Main parse entry point
     * @returns {Object} Parse result with messages and metadata
     */
    async parse() {
        // Check cache first
        const cacheKey = this.getCacheKey();
        const cached = this.cache.get(cacheKey);
        if (cached && Date.now() - cached.timestamp < this.cacheTTL) {
            return { ...cached.data, fromCache: true };
        }

        let result = null;

        // Try platform adapters first
        const adapter = this.findBestAdapter();

        if (adapter) {
            result = this.parseWithAdapter(adapter);
        }

        // Fallback to auto-discovery
        if (!result && this.autoDiscoverer) {
            result = await this.autoDiscoverer.discover();
        }

        // Final fallback to raw text extraction
        if ((!result || result.confidence < 0.7) && this.fallbackExtractor) {
            result = this.fallbackExtractor.extract();
        }

        // Validate and normalize result
        result = this.normalizeResult(result);

        // Cache the result
        if (result) {
            this.cache.set(cacheKey, {
                data: result,
                timestamp: Date.now()
            });
        }

        return result;
    }

    /**
     * Find the best matching adapter for current page
     * @returns {PlatformAdapter|null}
     */
    findBestAdapter() {
        let bestAdapter = null;
        let bestConfidence = 0;

        for (const adapter of this.adapters.values()) {
            if (adapter.detect()) {
                const confidence = adapter.getConfidence();
                if (confidence > bestConfidence) {
                    bestConfidence = confidence;
                    bestAdapter = adapter;
                }
            }
        }

        return bestAdapter;
    }

    /**
     * Get the currently detected platform name
     * @returns {string|null}
     */
    getDetectedPlatform() {
        const adapter = this.findBestAdapter();
        return adapter ? adapter.platformName : null;
    }

    /**
     * Get the current adapter's input selector
     * @returns {string|null}
     */
    getInputSelector() {
        const adapter = this.findBestAdapter();
        return adapter ? adapter.getInputSelector() : null;
    }

    /**
     * Get button positioning for current platform
     * @returns {Object|null}
     */
    getButtonPosition() {
        const adapter = this.findBestAdapter();
        return adapter ? adapter.getButtonPosition() : null;
    }

    /**
     * Parse using a specific adapter
     * @param {PlatformAdapter} adapter 
     * @returns {Object}
     */
    parseWithAdapter(adapter) {
        const version = adapter.detectVersion();
        const selectors = adapter.getSelectors(version);
        const messages = adapter.parse(selectors);

        if (!messages || messages.length === 0) {
            return null;
        }

        return {
            success: true,
            platform: adapter.platformName,
            version: version,
            messages: messages,
            confidence: adapter.getConfidence(),
            method: 'adapter',
            timestamp: Date.now()
        };
    }

    /**
     * Normalize parse result to standard format
     * @param {Object} result 
     * @returns {Object}
     */
    normalizeResult(result) {
        if (!result) {
            return {
                success: false,
                platform: 'unknown',
                messages: [],
                confidence: 0,
                error: 'No content could be extracted'
            };
        }

        // Ensure messages array exists
        if (!result.messages) {
            result.messages = [];
        }

        // Normalize message roles
        result.messages = result.messages.map(msg => ({
            role: this.normalizeRole(msg.role),
            content: msg.content || '',
            platform: msg.platform || result.platform || 'unknown',
            timestamp: msg.timestamp || null
        }));

        return result;
    }

    /**
     * Normalize role names to standard format
     * @param {string} role 
     * @returns {string}
     */
    normalizeRole(role) {
        const normalized = (role || '').toLowerCase();

        if (['user', 'human'].includes(normalized)) {
            return 'user';
        }
        if (['assistant', 'ai', 'bot', 'claude', 'chatgpt', 'gemini', 'model'].includes(normalized)) {
            return 'assistant';
        }
        if (['system'].includes(normalized)) {
            return 'system';
        }

        return 'unknown';
    }

    /**
     * Generate cache key for current page
     * @returns {string}
     */
    getCacheKey() {
        return `${window.location.hostname}-${window.location.pathname}`;
    }

    /**
     * Clear the content cache
     */
    clearCache() {
        this.cache.clear();
    }
}

// Create global instance
if (typeof window !== 'undefined') {
    window.ContextBridgeParser = ContextBridgeParser;
    window.contextBridgeParser = new ContextBridgeParser();
}
