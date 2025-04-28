/**
 * API Cache Manager
 * 
 * Provides an intelligent caching system for API responses with:
 * - TTL (Time-To-Live) based expiration
 * - Pattern-based cache invalidation
 * - Size-based cache eviction (LRU)
 * - In-flight request deduplication
 */

// Store cache entries with their metadata
const cacheStore = new Map();

// Store in-flight requests to prevent duplicate requests
const inflightRequests = new Map();

// Default cache settings
const DEFAULT_SETTINGS = {
  ttl: 300000, // 5 minutes in milliseconds
  maxSize: 50 * 1024 * 1024, // 50MB max cache size
  enabled: true
};

// Current settings (can be updated at runtime)
let settings = { ...DEFAULT_SETTINGS };

// Utility to estimate size of an object in bytes
const estimateSize = (obj) => {
  // Convert object to JSON string and get length in bytes
  // This is an estimation and not 100% accurate for all types
  if (!obj) return 0;
  try {
    const json = JSON.stringify(obj);
    // In JavaScript, each character is 2 bytes
    return json.length * 2;
  } catch (e) {
    console.warn('Failed to estimate object size for cache', e);
    return 0;
  }
};

/**
 * Create a cache entry with metadata
 * @param {string} key - Cache key
 * @param {any} data - Data to cache
 * @param {number} [ttl] - Time to live in milliseconds (optional)
 * @returns {Object} Cache entry object
 */
const createCacheEntry = (key, data, ttl = settings.ttl) => {
  const now = Date.now();
  const size = estimateSize(data);
  
  return {
    key,
    data,
    createdAt: now,
    expiresAt: ttl ? now + ttl : Infinity,
    lastAccessed: now,
    size,
    accessCount: 0
  };
};

/**
 * Check if a cache entry is expired
 * @param {Object} entry - Cache entry to check
 * @returns {boolean} True if the entry is expired
 */
const isExpired = (entry) => {
  return entry.expiresAt <= Date.now();
};

/**
 * Clear expired entries from the cache
 * @returns {number} Number of entries cleared
 */
const clearExpired = () => {
  let count = 0;
  
  for (const [key, entry] of cacheStore.entries()) {
    if (isExpired(entry)) {
      cacheStore.delete(key);
      count++;
    }
  }
  
  return count;
};

/**
 * Get the current cache size in bytes
 * @returns {number} Current cache size in bytes
 */
const getCacheSize = () => {
  let size = 0;
  
  for (const entry of cacheStore.values()) {
    size += entry.size;
  }
  
  return size;
};

/**
 * Make room in the cache by removing least recently used entries
 * @param {number} sizeNeeded - Size in bytes that needs to be freed
 * @returns {number} Size freed in bytes
 */
const makeRoom = (sizeNeeded) => {
  if (getCacheSize() + sizeNeeded <= settings.maxSize) {
    return 0; // No need to make room
  }
  
  // Sort entries by lastAccessed (oldest first)
  const entries = Array.from(cacheStore.entries())
    .map(([key, entry]) => entry)
    .sort((a, b) => a.lastAccessed - b.lastAccessed);
  
  let freedSize = 0;
  
  // Remove entries until we have enough room
  for (const entry of entries) {
    if (getCacheSize() - freedSize + sizeNeeded <= settings.maxSize) {
      break;
    }
    
    cacheStore.delete(entry.key);
    freedSize += entry.size;
  }
  
  return freedSize;
};

/**
 * Set cache configuration
 * @param {Object} config - Cache configuration
 * @param {number} [config.ttl] - Default time to live in milliseconds
 * @param {number} [config.maxSize] - Maximum cache size in bytes
 * @param {boolean} [config.enabled] - Whether caching is enabled
 */
export const configure = (config = {}) => {
  settings = {
    ...settings,
    ...config
  };
  
  // If the new max size is smaller than current cache size, make room
  if (settings.maxSize < getCacheSize()) {
    makeRoom(0);
  }
  
  return settings;
};

/**
 * Get a value from the cache
 * @param {string} key - Cache key
 * @returns {any|null} Cached value or null if not found/expired
 */
export const get = (key) => {
  if (!settings.enabled) return null;
  
  const entry = cacheStore.get(key);
  
  if (!entry) return null;
  
  // Check if the entry is expired
  if (isExpired(entry)) {
    cacheStore.delete(key);
    return null;
  }
  
  // Update access metadata
  entry.lastAccessed = Date.now();
  entry.accessCount++;
  
  return entry.data;
};

/**
 * Set a value in the cache
 * @param {string} key - Cache key
 * @param {any} data - Data to cache
 * @param {number} [ttl] - Time to live in milliseconds (optional)
 * @returns {boolean} True if the value was cached successfully
 */
export const set = (key, data, ttl) => {
  if (!settings.enabled) return false;
  
  // Don't cache null or undefined values
  if (data === null || data === undefined) return false;
  
  // Create a new cache entry
  const entry = createCacheEntry(key, data, ttl);
  
  // Check if the entry is too large for the cache
  if (entry.size > settings.maxSize) {
    console.warn(`Cache entry ${key} is larger than max cache size and cannot be cached`);
    return false;
  }
  
  // Periodically clear expired entries
  if (Math.random() < 0.1) {
    clearExpired();
  }
  
  // Make room for the new entry if needed
  makeRoom(entry.size);
  
  // Store the entry
  cacheStore.set(key, entry);
  
  return true;
};

/**
 * Remove a value from the cache
 * @param {string} key - Cache key
 * @returns {boolean} True if an entry was removed
 */
export const remove = (key) => {
  return cacheStore.delete(key);
};

/**
 * Clear all entries from the cache
 * @returns {number} Number of entries cleared
 */
export const clear = () => {
  const count = cacheStore.size;
  cacheStore.clear();
  return count;
};

/**
 * Check if a key exists in the cache and is not expired
 * @param {string} key - Cache key
 * @returns {boolean} True if the key exists and is not expired
 */
export const has = (key) => {
  if (!settings.enabled) return false;
  
  const entry = cacheStore.get(key);
  
  if (!entry) return false;
  
  if (isExpired(entry)) {
    cacheStore.delete(key);
    return false;
  }
  
  return true;
};

/**
 * Clear cache entries by pattern
 * @param {string|RegExp} pattern - Pattern to match against cache keys
 * @returns {number} Number of entries cleared
 */
export const clearPattern = (pattern) => {
  let count = 0;
  const regex = pattern instanceof RegExp ? pattern : new RegExp(pattern);
  
  for (const [key] of cacheStore.entries()) {
    if (regex.test(key)) {
      cacheStore.delete(key);
      count++;
    }
  }
  
  return count;
};

/**
 * Get cache statistics
 * @returns {Object} Cache statistics
 */
export const getStats = () => {
  return {
    entries: cacheStore.size,
    sizeBytes: getCacheSize(),
    maxSizeBytes: settings.maxSize,
    enabled: settings.enabled,
    inflightRequests: inflightRequests.size
  };
};

/**
 * Register an in-flight request
 * @param {string} key - Cache key
 * @param {Promise} promise - Request promise
 * @returns {Promise} The registered promise
 */
export const registerInflightRequest = (key, promise) => {
  inflightRequests.set(key, promise);
  
  // Remove from in-flight requests when done
  promise.finally(() => {
    if (inflightRequests.get(key) === promise) {
      inflightRequests.delete(key);
    }
  });
  
  return promise;
};

/**
 * Get an in-flight request if one exists
 * @param {string} key - Cache key
 * @returns {Promise|null} The in-flight request promise or null
 */
export const getInflightRequest = (key) => {
  return inflightRequests.get(key) || null;
};

export default {
  configure,
  get,
  set,
  remove,
  clear,
  has,
  clearPattern,
  getStats,
  registerInflightRequest,
  getInflightRequest
};
