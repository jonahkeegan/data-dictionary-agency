/**
 * Request cancellation utilities for the Data Dictionary Agency frontend
 * Manages cancellation tokens for in-flight API requests
 */
import axios from 'axios';

/**
 * Map of pending requests by key
 * @type {Map}
 */
const pendingRequests = new Map();

/**
 * Create a cancellation token for a request
 * @param {string} requestKey - Unique key for the request
 * @returns {Object} CancelToken source object
 */
export const createCancelToken = (requestKey) => {
  // Cancel any existing request with this key
  cancelPendingRequest(requestKey);
  
  // Create a new cancel token
  const source = axios.CancelToken.source();
  pendingRequests.set(requestKey, source);  
  return source;
};

/**
 * Cancel a pending request
 * @param {string} requestKey - Unique key for the request
 */
export const cancelPendingRequest = (requestKey) => {
  const source = pendingRequests.get(requestKey);
  if (source) {
    source.cancel(`Request ${requestKey} cancelled`);
    pendingRequests.delete(requestKey);
  }
};

/**
 * Cancel all pending requests
 * Useful when navigating away from a page or on app shutdown
 */
export const cancelAllPendingRequests = () => {
  pendingRequests.forEach((source, key) => {
    source.cancel(`Request ${key} cancelled during cleanup`);
  });
  pendingRequests.clear();
};

/**
 * Generate a request key from function name and parameters
 * @param {string} functionName - Name of the function making the request
 * @param {Array} args - Arguments passed to the function
 * @returns {string} Unique request key
 */
export const generateRequestKey = (functionName, args = []) => {
  return `${functionName}_${JSON.stringify(args)}`;
};

/**
 * Check if an error was caused by request cancellation
 * @param {Object} error - Error object from axios
 * @returns {boolean} Whether the error was due to cancellation
 */
export const isCancel = (error) => {
  return axios.isCancel(error);
};
