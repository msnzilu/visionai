/**
 * CVision Cache Utility
 * 
 * Provides a centralized, reusable caching mechanism using localStorage.
 * Supports TTL (Time To Live), key namespacing, and stale-while-revalidate patterns.
 */

const Cache = {
    PREFIX: 'cvision_cache_',
    DEFAULT_TTL: 3600000, // 1 hour in ms

    /**
     * Set a value in cache
     * @param {string} key - Cache key
     * @param {any} value - Value to store
     * @param {number} ttl - TTL in ms (optional)
     */
    set(key, value, ttl = this.DEFAULT_TTL) {
        const data = {
            value,
            timestamp: Date.now(),
            ttl
        };
        try {
            localStorage.setItem(this.PREFIX + key, JSON.stringify(data));
        } catch (e) {
            console.warn('Cache write failed:', e);
        }
    },

    /**
     * Get a value from cache
     * @param {string} key - Cache key
     * @returns {any|null} Cached value or null if not found/expired
     */
    get(key) {
        try {
            const data = localStorage.getItem(this.PREFIX + key);
            if (!data) return null;

            const { value, timestamp, ttl } = JSON.parse(data);
            const isExpired = ttl !== null && ttl > 0 && (Date.now() - timestamp) > ttl;

            if (isExpired) {
                this.remove(key);
                return null;
            }

            return value;
        } catch (e) {
            console.warn('Cache read failed:', e);
            return null;
        }
    },

    /**
     * Get meta info about a cache entry (including timestamp)
     * @param {string} key 
     */
    getMeta(key) {
        try {
            const data = localStorage.getItem(this.PREFIX + key);
            if (!data) return null;
            return JSON.parse(data);
        } catch (e) {
            return null;
        }
    },

    /**
     * Remove a value from cache
     * @param {string} key - Cache key
     */
    remove(key) {
        localStorage.removeItem(this.PREFIX + key);
    },

    /**
     * Clear all CVision cache
     */
    clear() {
        Object.keys(localStorage).forEach(key => {
            if (key.startsWith(this.PREFIX)) {
                localStorage.removeItem(key);
            }
        });
    },

    /**
     * Stale-while-revalidate wrapper
     * @param {string} key - Cache key
     * @param {function} fetchFn - Function that returns a promise for fresh data
     * @param {function} onUpdate - Callback called when data is available (cached and/or fresh)
     * @param {number} ttl - TTL in ms
     */
    async swr(key, fetchFn, onUpdate, ttl = this.DEFAULT_TTL) {
        // 1. Try to get from cache first
        const cached = this.get(key);
        if (cached) {
            onUpdate(cached, true); // true indicates it's from cache

            // Perform background revalidation without blocking
            this._revalidate(key, fetchFn, onUpdate, ttl).catch(e => {
                console.error('Background SWR revalidation failed:', e);
            });
            return;
        }

        // 2. Perform background revalidation (No cache, must await)
        try {
            await this._revalidate(key, fetchFn, onUpdate, ttl);
        } catch (e) {
            console.error('SWR revalidation failed:', e);
            throw e;
        }
    },

    /**
     * Internal revalidation helper
     * @private
     */
    async _revalidate(key, fetchFn, onUpdate, ttl) {
        const freshData = await fetchFn();
        if (freshData) {
            this.set(key, freshData, ttl);
            onUpdate(freshData, false);
        }
        return freshData;
    }
};

// Expose to CVision global
window.CVision = window.CVision || {};
window.CVision.Cache = Cache;
