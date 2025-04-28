/**
 * Base Service
 * 
 * Abstract base class for all API services providing common functionality:
 * - Standardized CRUD operations
 * - Caching with TTL support
 * - Circuit breaker integration
 * - Error handling and transformation
 */

import * as apiClient from './client';
import * as cache from './cache';
import * as circuitBreaker from './circuitBreaker';

/**
 * Base service class with common functionality for all services
 * @abstract
 */
export class BaseService {
  /**
   * Create a new service instance
   * @param {string} resourceName - API resource name (e.g., 'repositories')
   * @param {Object} [options] - Service options
   */
  constructor(resourceName, options = {}) {
    this.resourceName = resourceName;
    this.baseUrl = `/${resourceName}`;
    this.options = {
      enableCache: true,
      cacheTTL: null, // Use default TTL from cache config
      enableCircuitBreaker: true,
      ...options
    };
  }
  
  /**
   * Generate a circuit breaker name for this resource and operation
   * @param {string} operation - Operation name
   * @returns {string} Circuit breaker name
   */
  getCircuitName(operation) {
    return `${this.resourceName}:${operation}`;
  }
  
  /**
   * Generate a cache key for this resource and parameters
   * @param {string} operation - Operation name
   * @param {any} params - Parameters to include in the cache key
   * @returns {string} Cache key
   */
  getCacheKey(operation, params = null) {
    let key = `${this.resourceName}:${operation}`;
    
    if (params) {
      // For IDs or simple values, add directly
      if (typeof params === 'string' || typeof params === 'number') {
        key += `:${params}`;
      } 
      // For objects, add a hash of the serialized object
      else if (typeof params === 'object') {
        key += `:${JSON.stringify(params)}`;
      }
    }
    
    return key;
  }
  
  /**
   * Executes a GET request with caching and circuit breaking
   * @param {string} endpoint - API endpoint (will be appended to baseUrl)
   * @param {Object} [params] - Request parameters
   * @param {Object} [options] - Request options
   * @returns {Promise<any>} - Response data
   */
  async cachedGet(endpoint, params = {}, options = {}) {
    const url = this.baseUrl + (endpoint.startsWith('/') ? endpoint : `/${endpoint}`);
    const operation = endpoint.replace(/^\//, '').replace(/\//g, '_');
    const circuitName = this.getCircuitName(operation);
    const useCache = options.useCache ?? this.options.enableCache;
    const cacheTTL = options.cacheTTL ?? this.options.cacheTTL;
    
    // Set up options for the request
    const requestOptions = {
      ...options,
      useCache,
      cacheTTL,
      circuitName,
      cacheKey: options.cacheKey || this.getCacheKey(operation, params)
    };
    
    return apiClient.get(url, params, requestOptions);
  }
  
  /**
   * Executes a POST request with cache invalidation
   * @param {string} endpoint - API endpoint (will be appended to baseUrl)
   * @param {Object} data - Request payload
   * @param {Object} [options] - Request options
   * @param {string|boolean} [invalidatePattern] - Cache invalidation pattern
   * @returns {Promise<any>} - Response data
   */
  async executePost(endpoint, data = {}, options = {}, invalidatePattern = true) {
    const url = this.baseUrl + (endpoint.startsWith('/') ? endpoint : `/${endpoint}`);
    const operation = endpoint.replace(/^\//, '').replace(/\//g, '_');
    const circuitName = this.getCircuitName(operation);
    
    // Set up cache invalidation
    const invalidateCache = invalidatePattern === true 
      ? this.resourceName 
      : invalidatePattern;
    
    // Set up options for the request
    const requestOptions = {
      ...options,
      invalidateCache,
      circuitName
    };
    
    return apiClient.post(url, data, requestOptions);
  }
  
  /**
   * Executes a PUT request with cache invalidation
   * @param {string} endpoint - API endpoint (will be appended to baseUrl)
   * @param {Object} data - Request payload
   * @param {Object} [options] - Request options
   * @param {string|boolean} [invalidatePattern] - Cache invalidation pattern
   * @returns {Promise<any>} - Response data
   */
  async executePut(endpoint, data = {}, options = {}, invalidatePattern = true) {
    const url = this.baseUrl + (endpoint.startsWith('/') ? endpoint : `/${endpoint}`);
    const operation = endpoint.replace(/^\//, '').replace(/\//g, '_');
    const circuitName = this.getCircuitName(operation);
    
    // Set up cache invalidation
    const invalidateCache = invalidatePattern === true 
      ? this.resourceName 
      : invalidatePattern;
    
    // Set up options for the request
    const requestOptions = {
      ...options,
      invalidateCache,
      circuitName
    };
    
    return apiClient.put(url, data, requestOptions);
  }
  
  /**
   * Executes a DELETE request with cache invalidation
   * @param {string} endpoint - API endpoint (will be appended to baseUrl)
   * @param {Object} [options] - Request options
   * @param {string|boolean} [invalidatePattern] - Cache invalidation pattern
   * @returns {Promise<any>} - Response data
   */
  async executeDelete(endpoint, options = {}, invalidatePattern = true) {
    const url = this.baseUrl + (endpoint.startsWith('/') ? endpoint : `/${endpoint}`);
    const operation = endpoint.replace(/^\//, '').replace(/\//g, '_');
    const circuitName = this.getCircuitName(operation);
    
    // Set up cache invalidation
    const invalidateCache = invalidatePattern === true 
      ? this.resourceName 
      : invalidatePattern;
    
    // Set up options for the request
    const requestOptions = {
      ...options,
      invalidateCache,
      circuitName
    };
    
    return apiClient.del(url, requestOptions);
  }
  
  /**
   * Clear all cache entries for this resource
   * @param {string} [pattern] - Specific pattern to clear, defaults to all entries for this resource
   * @returns {number} Number of entries cleared
   */
  clearCache(pattern = null) {
    const cachePattern = pattern || `^${this.resourceName}:`;
    return cache.clearPattern(cachePattern);
  }
  
  /**
   * Execute a function with circuit breaker protection
   * @param {string} operation - Operation name
   * @param {Function} fn - Function to execute
   * @param {Function} [fallback] - Fallback function if circuit is open
   * @param {Object} [options] - Circuit breaker options
   * @returns {Promise<any>} - Function result or fallback result
   */
  async withCircuitBreaker(operation, fn, fallback = null, options = {}) {
    if (!this.options.enableCircuitBreaker) {
      return fn();
    }
    
    const circuitName = this.getCircuitName(operation);
    return circuitBreaker.execute(circuitName, fn, fallback, options);
  }
  
  /**
   * Retry a request with exponential backoff
   * @param {Function} requestFn - Function that returns a promise
   * @param {number} [maxRetries] - Maximum number of retries
   * @param {Object} [options] - Retry options
   * @returns {Promise<any>} - Request result
   */
  async retryRequest(requestFn, maxRetries = 3, options = {}) {
    return apiClient.retryRequest(requestFn, { 
      maxRetries, 
      ...options 
    });
  }
}

export default BaseService;
