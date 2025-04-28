/**
 * API client for the Data Dictionary Agency frontend
 * Provides centralized axios instance with interceptors for authentication and error handling
 */
import axios from 'axios';
import { getConfig } from '../../config';

/**
 * Create a configured axios instance
 * @param {Object} customConfig - Optional custom configuration
 * @returns {Object} Configured axios instance
 */
export const createApiClient = (customConfig = {}) => {
  const config = getConfig();
  
  const client = axios.create({
    baseURL: customConfig.baseURL || config.apiUrl,
    timeout: customConfig.timeout || config.timeout,
    headers: {
      'Content-Type': 'application/json',
      ...customConfig.headers,
    }
  });

  // Add request interceptors
  client.interceptors.request.use(
    (requestConfig) => {
      // Add authentication header if token exists
      const token = localStorage.getItem('auth_token');
      if (token) {
        requestConfig.headers.Authorization = `Bearer ${token}`;
      }
      
      // Log requests in development
      if (config.logLevel === 'debug' && process.env.NODE_ENV !== 'production') {
        console.log(`API Request: ${requestConfig.method.toUpperCase()} ${requestConfig.baseURL}${requestConfig.url}`, {
          data: requestConfig.data,
          params: requestConfig.params
        });
      }
      
      return requestConfig;
    },
    (error) => {
      // Handle request configuration errors
      console.error('API Request Error:', error);
      return Promise.reject(error);
    }
  );

  // Add response interceptors
  client.interceptors.response.use(
    (response) => {
      // Log successful responses in development
      if (config.logLevel === 'debug' && process.env.NODE_ENV !== 'production') {
        console.log(`API Response: ${response.config.method.toUpperCase()} ${response.config.url} ${response.status}`, {
          data: response.data
        });
      }
      
      return response;
    },
    (error) => {
      // Transform error response
      return handleApiError(error);
    }
  );

  return client;
};

/**
 * Global default client instance
 */
export const apiClient = createApiClient();

/**
 * Transform API errors into a standardized format
 * @param {Object} error - Axios error object
 * @returns {Promise} Rejected promise with standardized error
 */
export const handleApiError = (error) => {
  const config = getConfig();
  
  // Extract response data
  const response = error.response || {};
  const status = response.status || 0;
  const data = response.data || {};
  
  // Standard error response
  const standardError = {
    status,
    message: data.detail || data.message || error.message || 'Unknown error occurred',
    code: data.code || status,
    errors: data.errors || [],
    originalError: error,
  };

  // Log error for debugging
  if (config.logLevel === 'debug' || process.env.NODE_ENV !== 'production') {
    console.error('API Error:', standardError);
  }
  
  // Add metadata for handling special cases
  standardError.isNetworkError = !error.response;
  standardError.isServerError = status >= 500 && status < 600;
  standardError.isClientError = status >= 400 && status < 500;
  standardError.isAuthError = status === 401 || status === 403;
  
  return Promise.reject(standardError);
};

/**
 * Determine if an error should trigger a retry
 * @param {Object} error - Standardized error object
 * @returns {boolean} Whether the request should be retried
 */
export const isRetryable = (error) => {
  // Network errors are retryable
  if (error.isNetworkError) {
    return true;
  }
  
  // Server errors (5xx) are retryable
  return error.isServerError;
};

/**
 * Retry a failed request with exponential backoff
 * @param {Function} apiCall - Function that returns a promise for the API call
 * @param {number} maxRetries - Maximum number of retries (defaults to config value)
 * @returns {Promise} Result of API call or last error
 */
export const retryRequest = async (apiCall, maxRetries = null) => {
  const config = getConfig();
  const retries = maxRetries !== null ? maxRetries : config.retryCount;
  let retryCount = 0;
  
  while (retryCount <= retries) {
    try {
      return await apiCall();
    } catch (error) {
      retryCount++;
      
      // If reached max retries or error is not retryable, throw
      if (retryCount > retries || !isRetryable(error)) {
        throw error;
      }
      
      // Exponential backoff: wait longer for each retry
      const delay = Math.pow(2, retryCount) * 300;
      await new Promise(resolve => setTimeout(resolve, delay));
      
      // Log retry attempt
      if (config.logLevel === 'debug') {
        console.log(`Retrying request (${retryCount}/${retries})...`);
      }
    }
  }
};
