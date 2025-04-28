/**
 * Cancel Token Utilities
 * Provides utilities for creating and managing request cancellation tokens
 */
import axios from 'axios';

// Store for active cancel tokens
const cancelTokens = {};

/**
 * Generates a unique request key for grouping related requests
 * @param {string} operationName - Name of the API operation
 * @param {Array} params - Parameters for the operation (used to differentiate concurrent calls)
 * @returns {string} Unique request key
 */
export const generateRequestKey = (operationName, params = []) => {
  // Create a simplified string version of the parameters
  const paramsString = params.map(param => {
    if (param === null || param === undefined) {
      return 'null';
    }
    if (typeof param === 'object') {
      // Use keys + first few chars of values to avoid large strings
      return Object.keys(param).map(key => {
        const val = param[key];
        const valStr = typeof val === 'object' 
          ? JSON.stringify(val).substring(0, 10)
          : String(val).substring(0, 10);
        return `${key}:${valStr}`;
      }).join(',');
    }
    return String(param).substring(0, 20); // Limit param length
  }).join('|');
  
  // Return operation name + params string
  return `${operationName}:${paramsString}`;
};

/**
 * Creates a cancellation token for a request
 * @param {string} key - Unique key for the request
 * @returns {CancelTokenSource} Axios cancel token source
 */
export const createCancelToken = (key) => {
  // Cancel any existing request with the same key
  cancelPendingRequest(key);
  
  // Create a new cancel token source
  const source = axios.CancelToken.source();
  
  // Store the token source with the key
  cancelTokens[key] = source;
  
  return source;
};

/**
 * Cancels a pending request with the given key
 * @param {string} key - Key for the request to cancel
 * @returns {boolean} Whether a request was cancelled
 */
export const cancelPendingRequest = (key) => {
  if (cancelTokens[key]) {
    cancelTokens[key].cancel('Request cancelled due to new request');
    delete cancelTokens[key];
    return true;
  }
  return false;
};

/**
 * Cancels all pending requests
 * @returns {number} Number of requests cancelled
 */
export const cancelAllPendingRequests = () => {
  let count = 0;
  Object.keys(cancelTokens).forEach(key => {
    cancelTokens[key].cancel('Operation cancelled');
    delete cancelTokens[key];
    count++;
  });
  return count;
};

/**
 * Checks if an error is a cancellation error
 * @param {Error} error - Error to check
 * @returns {boolean} Whether the error is a cancellation
 */
export const isCancel = (error) => {
  return axios.isCancel(error);
};
