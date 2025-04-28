/**
 * API Client
 * Centralized API client for the Data Dictionary Agency frontend
 */
import axios from 'axios';
import { getConfig } from '../../config';

/**
 * Creates an Axios API client with the provided configuration
 * @param {Object} customConfig - Custom configuration to override defaults
 * @returns {AxiosInstance} Configured Axios instance
 */
export const createApiClient = (customConfig = {}) => {
  const config = getConfig();
  
  // Create axios instance with default configuration
  const client = axios.create({
    baseURL: customConfig.baseURL || config.apiUrl,
    timeout: customConfig.timeout || config.timeout,
    headers: {
      'Content-Type': 'application/json',
      ...customConfig.headers
    },
    ...customConfig
  });
  
  // Request interceptor
  client.interceptors.request.use(
    (config) => {
      // Get token from localStorage if it exists
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      
      // Log requests in development mode
      if (process.env.NODE_ENV === 'development' && config.logLevel === 'debug') {
        console.log(`API Request: ${config.method.toUpperCase()} ${config.url}`, config);
      }
      
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );
  
  // Response interceptor
  client.interceptors.response.use(
    (response) => {
      // Log responses in development mode
      if (process.env.NODE_ENV === 'development' && config.logLevel === 'debug') {
        console.log(`API Response: ${response.config.method.toUpperCase()} ${response.config.url}`, response);
      }
      
      return response;
    },
    (error) => {
      return Promise.reject(handleApiError(error));
    }
  );
  
  return client;
};

// Create default client
export const apiClient = createApiClient();

/**
 * Transforms API errors into a standardized format
 * @param {Error} error - The error object from the API call
 * @returns {Object} Standardized error object
 */
export const handleApiError = (error) => {
  // Initialize flags for error type
  const enhancedError = {
    isNetworkError: false,
    isServerError: false,
    isClientError: false,
    isAuthError: false,
    original: error
  };
  
  // Handle axios cancellation errors
  if (axios.isCancel(error)) {
    enhancedError.isCancelled = true;
    enhancedError.message = 'Request was cancelled';
    return enhancedError;
  }
  
  // Handle network errors (no response from server)
  if (!error.response) {
    enhancedError.isNetworkError = true;
    enhancedError.message = 'Network error - unable to connect to the server';
    console.error('Network Error:', error);
    return enhancedError;
  }
  
  // Get the status code
  const status = error.response.status;
  enhancedError.status = status;
  
  // Client errors (4xx)
  if (status >= 400 && status < 500) {
    enhancedError.isClientError = true;
    
    // Special handling for authentication errors
    if (status === 401 || status === 403) {
      enhancedError.isAuthError = true;
    }
  }
  
  // Server errors (5xx)
  if (status >= 500) {
    enhancedError.isServerError = true;
  }
  
  // Extract error details from response
  const responseData = error.response.data;
  
  // Handle different error formats from the backend
  if (responseData) {
    // Try to get standardized error fields
    enhancedError.message = responseData.detail || responseData.message || responseData.error || 'An error occurred';
    enhancedError.code = responseData.code || responseData.error_code;
    enhancedError.errors = responseData.errors || [];
  } else {
    enhancedError.message = error.message || 'An error occurred';
  }
  
  // Log the error in development
  if (process.env.NODE_ENV === 'development') {
    console.error('API Error:', {
      status,
      url: error.config?.url,
      message: enhancedError.message,
      details: responseData
    });
  }
  
  return enhancedError;
};

/**
 * Determines if an error is retryable
 * @param {Object} error - Enhanced error object from handleApiError
 * @returns {boolean} Whether the error is retryable
 */
export const isRetryable = (error) => {
  // Network errors are retryable
  if (error.isNetworkError) {
    return true;
  }
  
  // Server errors are retryable
  if (error.isServerError) {
    return true;
  }
  
  // Client errors are not retryable (invalid request, not found, etc.)
  if (error.isClientError) {
    return false;
  }
  
  // By default, don't retry
  return false;
};

/**
 * Retries a failed API call with exponential backoff
 * @param {Function} apiCall - Function that returns a promise for the API call
 * @param {number} [maxRetries=null] - Maximum number of retries (null = use config)
 * @returns {Promise} Promise that resolves with the API response
 */
export const retryRequest = async (apiCall, maxRetries = null) => {
  const config = getConfig();
  const maxAttempts = maxRetries !== null ? maxRetries + 1 : config.retryCount + 1;
  let lastError = null;
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await apiCall();
    } catch (error) {
      lastError = error;
      
      // Don't retry if it's not a retryable error
      if (!isRetryable(error)) {
        throw error;
      }
      
      // Don't retry on the last attempt
      if (attempt === maxAttempts) {
        throw error;
      }
      
      // Calculate backoff delay with exponential backoff and jitter
      const baseDelay = 300; // Base delay in milliseconds
      const maxDelay = 3000; // Maximum delay in milliseconds
      const exponentialDelay = Math.min(maxDelay, baseDelay * Math.pow(2, attempt - 1));
      const jitter = Math.random() * 0.3 * exponentialDelay; // Add up to 30% jitter
      const delay = exponentialDelay + jitter;
      
      // Log retry attempt in development
      if (process.env.NODE_ENV === 'development') {
        console.log(`API retry attempt ${attempt}/${maxAttempts - 1} after ${Math.round(delay)}ms`);
      }
      
      // Wait before next retry
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  // This should never be reached due to the throw in the loop,
  // but is here for completeness
  throw lastError;
};
