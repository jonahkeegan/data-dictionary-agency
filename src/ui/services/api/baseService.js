/**
 * Base service class for the Data Dictionary Agency frontend
 * Provides common functionality for API interaction with caching and error handling
 */
import { handleApiError, isRetryable, retryRequest } from './client';

/**
 * @typedef {Object} ServiceOptions
 * @property {import('axios').CancelToken} [cancelToken] - Axios cancel token
 * @property {boolean} [useCache=true] - Whether to use cache for this request
 * @property {number} [ttl] - Custom cache TTL in seconds (overrides default)
 * @property {string} [cacheKey] - Custom cache key
 */

/**
 * Cache entry structure
 * @typedef {Object} CacheEntry
 * @property {*} data - Cached data
 * @property {number} expiry - Expiration timestamp
 * @property {number} size - Approximate size in bytes
 */

/**
 * Cache manager for handling request caching
 */
class CacheManager {
  /**
   * Create a new cache manager
   * @param {Object} options - Cache options
   * @param {number} [options.maxSize=100000000] - Max cache size in bytes (100MB)
   * @param {number} [options.maxEntrySize=10000000] - Max entry size in bytes (10MB)
   */
  constructor(options = {}) {
    // Cache storage
    this.cache = new Map();
    this.inflightRequests = new Map();
    
    // Configuration
    this.options = {
      maxSize: 100 * 1024 * 1024, // 100MB default
      maxEntrySize: 10 * 1024 * 1024, // 10MB default
      ...options
    };
    
    // Size tracking
    this.currentSize = 0;
    
    // Metrics
    this.metrics = {
      hits: 0,
      misses: 0,
      evictions: 0,
      totalRequests: 0
    };
  }
  
  /**
   * Execute a request with caching
   * @template T
   * @param {string} key - Cache key
   * @param {Function} requestFn - Request function
   * @param {Object} options - Cache options
   * @param {number} [options.ttl] - Cache TTL in seconds
   * @param {boolean} [options.useCache=true] - Whether to use cache
   * @returns {Promise<T>} Response data
   */
  async withCache(key, requestFn, options = {}) {
    // Skip cache if disabled
    if (options.useCache === false) {
      this.metrics.totalRequests++;
      return requestFn();
    }
    
    // Check cache first
    const cached = this.cache.get(key);
    if (cached && Date.now() < cached.expiry) {
      this.recordHit();
      return cached.data;
    }
    
    this.recordMiss();
    
    // Check for in-flight request
    const inflightRequest = this.inflightRequests.get(key);
    if (inflightRequest) {
      return inflightRequest;
    }
    
    // Create new request
    const promise = (async () => {
      try {
        const data = await requestFn();
        
        // Store in cache with TTL
        const ttl = options.ttl || 300; // 5 minutes default
        this.storeInCache(key, data, ttl);
        
        return data;
      } finally {
        // Always remove from inflight requests
        this.inflightRequests.delete(key);
      }
    })();
    
    // Register inflight request
    this.inflightRequests.set(key, promise);
    return promise;
  }
  
  /**
   * Store data in cache with TTL
   * @param {string} key - Cache key
   * @param {*} data - Data to cache
   * @param {number} ttl - TTL in seconds
   */
  storeInCache(key, data, ttl) {
    // Skip if data is null or undefined
    if (data == null) return;
    
    // Calculate size
    const size = this.getApproximateSize(data);
    
    // Skip if too large
    if (size > this.options.maxEntrySize) {
      console.warn(`Cache entry too large (${size} bytes), not caching: ${key}`);
      return;
    }
    
    // Remove if already exists
    if (this.cache.has(key)) {
      this.currentSize -= this.cache.get(key).size;
      this.cache.delete(key);
    }
    
    // Store in cache
    this.cache.set(key, {
      data: structuredClone(data), // Deep copy to prevent mutation
      expiry: Date.now() + (ttl * 1000),
      size
    });
    
    this.currentSize += size;
    
    // Check if we need to evict entries
    this.evictIfNeeded();
  }
  
  /**
   * Invalidate cache entries by pattern
   * @param {string|RegExp} pattern - Invalidation pattern
   */
  invalidate(pattern) {
    // Convert string to RegExp if needed
    const regex = typeof pattern === 'string' 
      ? new RegExp(pattern)
      : pattern;
    
    let freedMemory = 0;
    let evictionCount = 0;
    
    // Check each key
    for (const [key, entry] of this.cache.entries()) {
      if (regex.test(key)) {
        freedMemory += entry.size;
        evictionCount++;
        this.cache.delete(key);
      }
    }
    
    if (evictionCount > 0) {
      this.currentSize -= freedMemory;
      this.metrics.evictions += evictionCount;
      
      if (evictionCount > 1) {
        console.debug(`Cache: Invalidated ${evictionCount} entries matching ${pattern}`);
      }
    }
  }
  
  /**
   * Evict entries if cache size exceeds maximum
   */
  evictIfNeeded() {
    if (this.currentSize <= this.options.maxSize) {
      return; // No need to evict
    }
    
    // Sort entries by expiry (oldest first)
    const entries = Array.from(this.cache.entries())
      .sort((a, b) => a[1].expiry - b[1].expiry);
    
    let evictionCount = 0;
    
    // Evict until under size limit (with buffer)
    for (const [key, entry] of entries) {
      this.cache.delete(key);
      this.currentSize -= entry.size;
      evictionCount++;
      
      // Stop at 80% of max to provide buffer
      if (this.currentSize <= this.options.maxSize * 0.8) {
        break;
      }
    }
    
    this.metrics.evictions += evictionCount;
    console.debug(`Cache: Evicted ${evictionCount} entries due to size limit`);
  }
  
  /**
   * Get approximate size of data in bytes
   * @param {*} data - Data to measure
   * @returns {number} Size in bytes
   */
  getApproximateSize(data) {
    if (data === null || data === undefined) return 0;
    
    // Handle primitives
    if (typeof data === 'boolean') return 4;
    if (typeof data === 'number') return 8;
    if (typeof data === 'string') return data.length * 2; // UTF-16
    
    // Handle arrays
    if (Array.isArray(data)) {
      return data.reduce((size, item) => 
        size + this.getApproximateSize(item), 0) + 24; // Array overhead
    }
    
    // Handle dates
    if (data instanceof Date) return 8;
    
    // Handle objects
    if (typeof data === 'object') {
      let size = 32; // Object overhead
      
      for (const [key, value] of Object.entries(data)) {
        // Key size (approximate string size)
        size += key.length * 2;
        // Value size (recursive)
        size += this.getApproximateSize(value);
      }
      
      return size;
    }
    
    return 8; // Default for unknown types
  }
  
  /**
   * Record cache hit
   */
  recordHit() {
    this.metrics.hits++;
    this.metrics.totalRequests++;
  }
  
  /**
   * Record cache miss
   */
  recordMiss() {
    this.metrics.misses++;
    this.metrics.totalRequests++;
  }
  
  /**
   * Get cache metrics
   * @returns {Object} Cache metrics
   */
  getMetrics() {
    return {
      ...this.metrics,
      hitRate: this.metrics.totalRequests > 0 
        ? this.metrics.hits / this.metrics.totalRequests
        : 0,
      currentSize: this.currentSize,
      maxSize: this.options.maxSize,
      entryCount: this.cache.size,
      inflightCount: this.inflightRequests.size
    };
  }
}

/**
 * Circuit breaker state for tracking failing endpoints
 * @typedef {Object} CircuitBreakerState
 * @property {number} failures - Number of consecutive failures
 * @property {number} openUntil - Timestamp until circuit is open
 */

/**
 * Base service class with shared functionality
 */
class BaseService {
  /**
   * Create a new service
   * @param {import('axios').AxiosInstance} apiClient - API client
   * @param {Object} [options={}] - Service options
   * @param {number} [options.defaultTTL=300] - Default cache TTL in seconds
   * @param {boolean} [options.enableCache=true] - Whether to enable caching
   * @param {number} [options.maxCacheSize] - Maximum cache size in bytes
   * @param {number} [options.maxCacheEntrySize] - Maximum cache entry size in bytes
   */
  constructor(apiClient, options = {}) {
    this.apiClient = apiClient;
    this.options = {
      defaultTTL: 300, // 5 minutes
      enableCache: true,
      ...options
    };
    
    // Create cache manager if caching is enabled
    if (this.options.enableCache) {
      this.cacheManager = new CacheManager({
        maxSize: this.options.maxCacheSize,
        maxEntrySize: this.options.maxCacheEntrySize
      });
    }
    
    // Circuit breaker state
    this.circuitBreakers = new Map();
  }
  
  /**
   * Get the API client instance
   * @returns {import('axios').AxiosInstance} API client
   */
  getApiClient() {
    return this.apiClient;
  }
  
  /**
   * Handle and normalize API errors
   * @param {Error} error - Original error
   * @throws {Error} Normalized error
   */
  handleError(error) {
    // Use the handleApiError function from client.js
    throw handleApiError(error);
  }
  
  /**
   * Execute a cached API request
   * @template T
   * @param {string} endpoint - API endpoint
   * @param {Object} [params={}] - Query parameters
   * @param {ServiceOptions} [options={}] - Request options
   * @returns {Promise<T>} Response data
   */
  async cachedGet(endpoint, params = {}, options = {}) {
    // Skip cache if disabled
    if (!this.cacheManager || options.useCache === false) {
      const response = await this.apiClient.get(endpoint, { 
        params,
        ...options 
      });
      return response.data;
    }
    
    // Generate cache key
    const cacheKey = options.cacheKey || 
      this.generateCacheKey(endpoint, params);
    
    // Execute with cache
    return this.cacheManager.withCache(
      cacheKey,
      async () => {
        const response = await this.apiClient.get(endpoint, { 
          params,
          ...options 
        });
        return response.data;
      },
      {
        ttl: options.ttl || this.options.defaultTTL,
        ...options
      }
    );
  }
  
  /**
   * Execute a POST request with cache invalidation
   * @template T
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request data
   * @param {ServiceOptions} [options={}] - Request options
   * @param {string|RegExp} [invalidatePattern] - Cache invalidation pattern
   * @returns {Promise<T>} Response data
   */
  async executePost(endpoint, data, options = {}, invalidatePattern) {
    try {
      const response = await this.apiClient.post(endpoint, data, options);
      
      // Invalidate cache if pattern provided
      if (this.cacheManager && invalidatePattern) {
        this.cacheManager.invalidate(invalidatePattern);
      }
      
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
  }
  
  /**
   * Execute a PUT request with cache invalidation
   * @template T
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request data
   * @param {ServiceOptions} [options={}] - Request options
   * @param {string|RegExp} [invalidatePattern] - Cache invalidation pattern
   * @returns {Promise<T>} Response data
   */
  async executePut(endpoint, data, options = {}, invalidatePattern) {
    try {
      const response = await this.apiClient.put(endpoint, data, options);
      
      // Invalidate cache if pattern provided
      if (this.cacheManager && invalidatePattern) {
        this.cacheManager.invalidate(invalidatePattern);
      }
      
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
  }
  
  /**
   * Execute a DELETE request with cache invalidation
   * @template T
   * @param {string} endpoint - API endpoint
   * @param {ServiceOptions} [options={}] - Request options
   * @param {string|RegExp} [invalidatePattern] - Cache invalidation pattern
   * @returns {Promise<T>} Response data
   */
  async executeDelete(endpoint, options = {}, invalidatePattern) {
    try {
      const response = await this.apiClient.delete(endpoint, options);
      
      // Invalidate cache if pattern provided
      if (this.cacheManager && invalidatePattern) {
        this.cacheManager.invalidate(invalidatePattern);
      }
      
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
  }
  
  /**
   * Generate cache key from endpoint and params
   * @param {string} endpoint - API endpoint
   * @param {Object} [params={}] - Query parameters
   * @returns {string} Cache key
   */
  generateCacheKey(endpoint, params = {}) {
    // Create normalized copy of params
    const normalizedParams = { ...params };
    
    // Sort keys for consistent ordering
    const sortedParams = Object.keys(normalizedParams)
      .sort()
      .reduce((obj, key) => {
        obj[key] = normalizedParams[key];
        return obj;
      }, {});
    
    return `${endpoint}:${JSON.stringify(sortedParams)}`;
  }
  
  /**
   * Clear service cache
   * @param {string|RegExp} [pattern] - Invalidation pattern
   */
  clearCache(pattern) {
    if (this.cacheManager) {
      this.cacheManager.invalidate(pattern || '.*');
    }
  }
  
  /**
   * Implement circuit breaker pattern for API calls
   * @template T
   * @param {Function} requestFn - Request function
   * @param {Function} [fallbackFn] - Optional fallback function
   * @param {Object} [options={}] - Circuit breaker options
   * @param {string} [options.endpoint='unknown'] - Endpoint identifier
   * @param {number} [options.maxFailures=3] - Maximum consecutive failures before opening circuit
   * @param {number} [options.resetTimeout=30000] - Time to wait before resetting circuit (ms)
   * @returns {Promise<T>} Response data or fallback
   */
  async withCircuitBreaker(requestFn, fallbackFn, options = {}) {
    const { endpoint = 'unknown', maxFailures = 3, resetTimeout = 30000 } = options;
    
    // Check if circuit is open
    if (this.isCircuitOpen(endpoint)) {
      // Circuit is open, use fallback
      if (fallbackFn) {
        return fallbackFn();
      }
      throw new Error(`Circuit open for ${endpoint}`);
    }
    
    try {
      // Attempt the request
      const result = await requestFn();
      // Success, reset failure count
      this.resetCircuitFailures(endpoint);
      return result;
    } catch (error) {
      // Increment failure count
      this.recordCircuitFailure(endpoint);
      
      // Check if we need to open the circuit
      if (this.getCircuitFailures(endpoint) >= maxFailures) {
        this.openCircuit(endpoint, resetTimeout);
      }
      
      // Re-throw or use fallback
      if (fallbackFn) {
        return fallbackFn(error);
      }
      throw error;
    }
  }
  
  /**
   * Retry a request using the retryRequest function
   * @template T
   * @param {Function} requestFn - Request function
   * @param {number} [maxRetries] - Maximum number of retries
   * @returns {Promise<T>} Response data
   */
  retryRequest(requestFn, maxRetries) {
    return retryRequest(requestFn, maxRetries);
  }
  
  /**
   * Check if a circuit is open
   * @param {string} endpoint - Endpoint identifier
   * @returns {boolean} Whether circuit is open
   */
  isCircuitOpen(endpoint) {
    const state = this.circuitBreakers.get(endpoint);
    if (!state) return false;
    
    if (Date.now() < state.openUntil) {
      return true;
    }
    
    // Reset if timeout has elapsed
    if (state.openUntil > 0) {
      this.resetCircuitFailures(endpoint);
    }
    
    return false;
  }
  
  /**
   * Get the number of consecutive failures for an endpoint
   * @param {string} endpoint - Endpoint identifier
   * @returns {number} Number of failures
   */
  getCircuitFailures(endpoint) {
    const state = this.circuitBreakers.get(endpoint);
    return state ? state.failures : 0;
  }
  
  /**
   * Record a circuit failure
   * @param {string} endpoint - Endpoint identifier
   */
  recordCircuitFailure(endpoint) {
    const state = this.circuitBreakers.get(endpoint) || { failures: 0, openUntil: 0 };
    state.failures++;
    this.circuitBreakers.set(endpoint, state);
  }
  
  /**
   * Reset circuit failures
   * @param {string} endpoint - Endpoint identifier
   */
  resetCircuitFailures(endpoint) {
    this.circuitBreakers.set(endpoint, { failures: 0, openUntil: 0 });
  }
  
  /**
   * Open a circuit
   * @param {string} endpoint - Endpoint identifier
   * @param {number} resetTimeout - Time to wait before resetting circuit (ms)
   */
  openCircuit(endpoint, resetTimeout) {
    const state = this.circuitBreakers.get(endpoint) || { failures: 0, openUntil: 0 };
    state.openUntil = Date.now() + resetTimeout;
    this.circuitBreakers.set(endpoint, state);
    
    console.warn(`Circuit opened for ${endpoint} until ${new Date(state.openUntil).toISOString()}`);
  }
}

export default BaseService;
