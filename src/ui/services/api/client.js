/**
 * API Client
 * 
 * Provides a configured Axios instance with enhanced features:
 * - Environment-specific configuration
 * - Request/response interceptors
 * - Error handling and standardization
 * - Request cancellation
 * - Authentication header management
 * - Automatic retries for transient failures
 */

import axios from 'axios';
import { getConfig, getApiUrl } from './config';
import { createErrorHandler, isRetriableError } from './errorHandler';
import * as cache from './cache';
import * as circuitBreaker from './circuitBreaker';

/**
 * Create a configured Axios instance
 * @param {Object} [options] - Custom options to override defaults
 * @returns {Object} Configured Axios instance
 */
export const createApiClient = (options = {}) => {
  const config = getConfig();
  
  // Create base client with defaults
  const client = axios.create({
    baseURL: options.baseURL || config.apiUrl,
    timeout: options.timeout || config.timeout,
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...options.headers
    }
  });
  
  // Add request interceptor for auth token, logging, etc.
  client.interceptors.request.use(
    (config) => {
      // Configure request for debugging
      if (process.env.NODE_ENV === 'development') {
        console.debug(`[API] ${config.method.toUpperCase()} ${config.url}`);
      }
      
      // Add auth token if available (from localStorage or other auth service)
      const token = localStorage.getItem('authToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      
      return config;
    },
    (error) => Promise.reject(error)
  );
  
  // Add response interceptor for error handling
  client.interceptors.response.use(
    (response) => {
      // Process successful responses
      // Some APIs wrap responses in a data field, normalize here if needed
      if (response.data && response.data.data !== undefined) {
        response.data = response.data.data;
      }
      
      return response;
    },
    createErrorHandler()
  );
  
  return client;
};

// Create default API client
export const apiClient = createApiClient();

/**
 * Execute a GET request with caching and circuit breaker
 * @param {string} url - The URL to request
 * @param {Object} [params] - URL parameters
 * @param {Object} [options] - Request options
 * @returns {Promise} Promise resolving to the response data
 */
export const get = async (url, params = {}, options = {}) => {
  const {
    useCache = true,
    cacheTTL,
    cacheKey,
    circuitName = url,
    cancelToken,
    withCredentials,
    headers,
    ...axiosOptions
  } = options;
  
  // Construct final URL with params
  const requestKey = cacheKey || `${url}:${JSON.stringify(params)}`;
  
  // Check if response is in cache
  if (useCache) {
    const cachedData = cache.get(requestKey);
    if (cachedData) {
      return cachedData;
    }
    
    // Check for in-flight requests to deduplicate
    const inflightRequest = cache.getInflightRequest(requestKey);
    if (inflightRequest) {
      return inflightRequest;
    }
  }

  // Create request function
  const sendRequest = async () => {
    const response = await apiClient.get(url, {
      params,
      cancelToken,
      withCredentials,
      headers,
      ...axiosOptions
    });
    
    const responseData = response.data;
    
    // Cache the response if caching is enabled
    if (useCache) {
      cache.set(requestKey, responseData, cacheTTL);
    }
    
    return responseData;
  };
  
  // Wrap request in circuit breaker
  const executeRequest = async () => {
    return circuitBreaker.execute(
      circuitName,
      sendRequest,
      options.fallback || null
    );
  };
  
  // Register and execute request
  const requestPromise = executeRequest();
  
  // Register as in-flight if using cache
  if (useCache) {
    cache.registerInflightRequest(requestKey, requestPromise);
  }
  
  return requestPromise;
};

/**
 * Execute a POST request with cache invalidation
 * @param {string} url - The URL to request
 * @param {Object} data - The data to send
 * @param {Object} [options] - Request options
 * @returns {Promise} Promise resolving to the response data
 */
export const post = async (url, data = {}, options = {}) => {
  const {
    invalidateCache,
    circuitName = url,
    cancelToken,
    withCredentials,
    headers,
    ...axiosOptions
  } = options;
  
  // Create request function
  const sendRequest = async () => {
    const response = await apiClient.post(url, data, {
      cancelToken,
      withCredentials,
      headers,
      ...axiosOptions
    });
    
    // Invalidate cache if specified
    if (invalidateCache) {
      const pattern = typeof invalidateCache === 'string' 
        ? invalidateCache 
        : url;
      
      cache.clearPattern(pattern);
    }
    
    return response.data;
  };
  
  // Wrap request in circuit breaker
  return circuitBreaker.execute(
    circuitName,
    sendRequest,
    options.fallback || null
  );
};

/**
 * Execute a PUT request with cache invalidation
 * @param {string} url - The URL to request
 * @param {Object} data - The data to send
 * @param {Object} [options] - Request options
 * @returns {Promise} Promise resolving to the response data
 */
export const put = async (url, data = {}, options = {}) => {
  const {
    invalidateCache,
    circuitName = url,
    cancelToken,
    withCredentials,
    headers,
    ...axiosOptions
  } = options;
  
  // Create request function
  const sendRequest = async () => {
    const response = await apiClient.put(url, data, {
      cancelToken,
      withCredentials,
      headers,
      ...axiosOptions
    });
    
    // Invalidate cache if specified
    if (invalidateCache) {
      const pattern = typeof invalidateCache === 'string' 
        ? invalidateCache 
        : url;
      
      cache.clearPattern(pattern);
    }
    
    return response.data;
  };
  
  // Wrap request in circuit breaker
  return circuitBreaker.execute(
    circuitName,
    sendRequest,
    options.fallback || null
  );
};

/**
 * Execute a DELETE request with cache invalidation
 * @param {string} url - The URL to request
 * @param {Object} [options] - Request options
 * @returns {Promise} Promise resolving to the response data
 */
export const del = async (url, options = {}) => {
  const {
    invalidateCache,
    circuitName = url,
    cancelToken,
    withCredentials,
    headers,
    ...axiosOptions
  } = options;
  
  // Create request function
  const sendRequest = async () => {
    const response = await apiClient.delete(url, {
      cancelToken,
      withCredentials,
      headers,
      ...axiosOptions
    });
    
    // Invalidate cache if specified
    if (invalidateCache) {
      const pattern = typeof invalidateCache === 'string' 
        ? invalidateCache 
        : url;
      
      cache.clearPattern(pattern);
    }
    
    return response.data;
  };
  
  // Wrap request in circuit breaker
  return circuitBreaker.execute(
    circuitName,
    sendRequest,
    options.fallback || null
  );
};

/**
 * Execute a request with automatic retries for transient failures
 * @param {Function} requestFn - Function that returns a promise
 * @param {Object} [options] - Retry options
 * @returns {Promise} Promise resolving to the response data
 */
export const retryRequest = async (requestFn, options = {}) => {
  const {
    maxRetries = getConfig().retryCount,
    retryDelay = 1000,
    retryMultiplier = 2,
    maxRetryDelay = 30000,
    shouldRetry = isRetriableError
  } = options;
  
  let retries = 0;
  let lastError = null;
  
  const executeWithRetry = async () => {
    try {
      return await requestFn();
    } catch (error) {
      // Check if we should retry
      if (retries < maxRetries && shouldRetry(error)) {
        retries++;
        lastError = error;
        
        // Calculate backoff delay
        const delay = Math.min(
          retryDelay * Math.pow(retryMultiplier, retries - 1),
          maxRetryDelay
        );
        
        // Log retry attempt
        console.info(`[API] Retry ${retries}/${maxRetries} after ${delay}ms: ${error.message}`);
        
        // Wait for the backoff delay
        await new Promise(resolve => setTimeout(resolve, delay));
        
        // Try again
        return executeWithRetry();
      }
      
      // If we shouldn't retry or have maxed out retries, throw the last error
      throw error;
    }
  };
  
  return executeWithRetry();
};

export default {
  createApiClient,
  apiClient,
  get,
  post,
  put,
  del,
  retryRequest
};
