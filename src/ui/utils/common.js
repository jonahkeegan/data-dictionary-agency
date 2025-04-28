/**
 * Common utilities for the Data Dictionary Agency frontend
 */

/**
 * Add artificial delay to simulate network latency
 * @param {number} ms - Milliseconds to delay
 * @returns {Promise<void>} Promise that resolves after the specified delay
 */
export function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Parse query parameters from URL
 * @param {string} [queryString=window.location.search] - Query string to parse (defaults to current URL)
 * @returns {Object} Parsed query parameters as key-value pairs
 */
export function parseQueryParams(queryString = window.location.search) {
  const params = {};
  const urlParams = new URLSearchParams(queryString);
  
  for (const [key, value] of urlParams.entries()) {
    // Try to parse JSON values
    try {
      params[key] = JSON.parse(value);
    } catch (e) {
      // If not valid JSON, use the string value
      params[key] = value;
    }
  }
  
  return params;
}

/**
 * Format a date object or string to a human-readable format
 * @param {Date|string} date - Date to format
 * @param {Object} [options] - Intl.DateTimeFormat options
 * @returns {string} Formatted date string
 */
export function formatDate(date, options = {}) {
  const defaultOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: 'numeric'
  };
  
  const mergedOptions = { ...defaultOptions, ...options };
  const dateObj = date instanceof Date ? date : new Date(date);
  
  return new Intl.DateTimeFormat('en-US', mergedOptions).format(dateObj);
}

/**
 * Truncate a string to a maximum length and add ellipsis if truncated
 * @param {string} str - String to truncate
 * @param {number} [maxLength=100] - Maximum length before truncation
 * @returns {string} Truncated string with ellipsis if needed
 */
export function truncate(str, maxLength = 100) {
  if (!str) return '';
  if (str.length <= maxLength) return str;
  return `${str.substring(0, maxLength - 3)}...`;
}

/**
 * Deep clone an object
 * @param {*} obj - Object to clone
 * @returns {*} Cloned object
 */
export function cloneDeep(obj) {
  return JSON.parse(JSON.stringify(obj));
}

/**
 * Get the base API URL from environment variables
 * @returns {string} Base API URL
 */
export function getApiBaseUrl() {
  // Check for environment variable
  if (process.env.REACT_APP_API_BASE_URL) {
    return process.env.REACT_APP_API_BASE_URL;
  }
  
  // Check for window variable (useful for runtime configuration)
  if (window.ENV && window.ENV.API_BASE_URL) {
    return window.ENV.API_BASE_URL;
  }
  
  // Default to relative path for same-origin API
  return '/api';
}

/**
 * Determine if the application should use mock services
 * @returns {boolean} Whether to use mock services
 */
export function shouldUseMockServices() {
  // Check query parameter first (useful for manual testing)
  const params = parseQueryParams();
  if (params.mock !== undefined) {
    return params.mock === 'true' || params.mock === true;
  }
  
  // Check environment variable
  if (process.env.REACT_APP_USE_MOCK_SERVICES) {
    return process.env.REACT_APP_USE_MOCK_SERVICES === 'true';
  }
  
  // Check for development mode
  if (process.env.NODE_ENV === 'development') {
    // Default to true for development
    return true;
  }
  
  // Default to false for production
  return false;
}

/**
 * Get environment configuration
 * @returns {Object} Environment configuration
 */
export function getEnvironmentConfig() {
  return {
    apiBaseUrl: getApiBaseUrl(),
    useMockServices: shouldUseMockServices(),
    environment: process.env.NODE_ENV || 'development',
    version: process.env.REACT_APP_VERSION || '0.1.0',
    debug: process.env.NODE_ENV !== 'production'
  };
}

/**
 * Generate a random ID (useful for temporary IDs)
 * @param {number} [length=8] - Length of the ID
 * @returns {string} Random ID
 */
export function generateId(length = 8) {
  return Math.random()
    .toString(36)
    .substring(2, 2 + length);
}

/**
 * Convert a file size in bytes to a human-readable format
 * @param {number} bytes - File size in bytes
 * @param {number} [decimals=2] - Number of decimal places
 * @returns {string} Human-readable file size
 */
export function formatFileSize(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${sizes[i]}`;
}

/**
 * Extract filename from a path
 * @param {string} path - File path
 * @returns {string} Filename without path
 */
export function getFilename(path) {
  if (!path) return '';
  
  // Handle both forward and backward slashes
  const parts = path.split(/[\\/]/);
  return parts[parts.length - 1];
}

/**
 * Extract file extension from a filename
 * @param {string} filename - Filename
 * @returns {string} File extension (without dot)
 */
export function getFileExtension(filename) {
  if (!filename) return '';
  
  const parts = filename.split('.');
  return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : '';
}

/**
 * Check if two objects are deeply equal
 * @param {Object} obj1 - First object
 * @param {Object} obj2 - Second object
 * @returns {boolean} Whether the objects are equal
 */
export function deepEqual(obj1, obj2) {
  return JSON.stringify(obj1) === JSON.stringify(obj2);
}

/**
 * Debounce a function
 * @param {Function} func - Function to debounce
 * @param {number} [wait=300] - Debounce delay in milliseconds
 * @returns {Function} Debounced function
 */
export function debounce(func, wait = 300) {
  let timeout;
  
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}
