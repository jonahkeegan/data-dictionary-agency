/**
 * Request Cancellation Utility
 * 
 * Provides utilities for creating and managing cancellation tokens
 * for Axios requests, allowing safe cancellation of in-flight requests.
 */

import axios from 'axios';

// Store active cancellation tokens
const activeTokens = new Map();

/**
 * Create a cancellation token that can be used to abort requests
 * @param {string} id - Unique identifier for the cancellation token
 * @returns {Object} Object with token and cancel function
 */
export const createCancelToken = (id) => {
  // Cancel any existing token with the same ID
  cancelPendingRequest(id);
  
  // Create a new cancelation token
  const source = axios.CancelToken.source();
  
  // Store the token source
  activeTokens.set(id, source);
  
  return {
    token: source.token,
    cancel: () => source.cancel(`Request ${id} was cancelled`)
  };
};

/**
 * Cancel a pending request by ID
 * @param {string} id - ID of the request to cancel
 * @returns {boolean} True if a request was cancelled, false otherwise
 */
export const cancelPendingRequest = (id) => {
  if (activeTokens.has(id)) {
    const source = activeTokens.get(id);
    source.cancel(`Request ${id} was cancelled`);
    activeTokens.delete(id);
    return true;
  }
  return false;
};

/**
 * Cancel all pending requests
 * @param {string} [prefix] - Optional prefix to only cancel requests with IDs starting with this prefix
 * @returns {number} Number of requests cancelled
 */
export const cancelAllPendingRequests = (prefix) => {
  let count = 0;
  
  for (const [id, source] of activeTokens.entries()) {
    if (!prefix || id.startsWith(prefix)) {
      source.cancel(`Request ${id} was cancelled`);
      activeTokens.delete(id);
      count++;
    }
  }
  
  return count;
};

/**
 * Check if a request cancellation was triggered by the cancellation token
 * @param {Error} error - The error to check
 * @returns {boolean} True if the error is a cancellation error
 */
export const isRequestCancelledError = (error) => {
  return axios.isCancel(error);
};

/**
 * Get the count of active cancellation tokens
 * @param {string} [prefix] - Optional prefix to filter tokens
 * @returns {number} Count of active tokens
 */
export const getActiveTokensCount = (prefix) => {
  if (prefix) {
    let count = 0;
    for (const id of activeTokens.keys()) {
      if (id.startsWith(prefix)) {
        count++;
      }
    }
    return count;
  }
  return activeTokens.size;
};

/**
 * Create a cancellation token for use in a component
 * The token will automatically be cancelled when the component unmounts
 * @param {string} id - Unique identifier for the cancellation token
 * @param {Function} useEffectHook - React useEffect hook for cleanup
 * @returns {Object} Object with token and cancel function
 * 
 * @example
 * // In a React component:
 * const { token } = useCancelToken('myDataFetch', useEffect);
 * 
 * useEffect(() => {
 *   apiClient.get('/data', { cancelToken: token });
 * }, [token]);
 */
export const useCancelToken = (id, useEffectHook) => {
  const source = createCancelToken(id);
  
  // Set up automatic cleanup when component unmounts
  useEffectHook(() => {
    return () => {
      cancelPendingRequest(id);
    };
  }, []); // Empty dependency array ensures this only runs on mount/unmount
  
  return source;
};

export default {
  createCancelToken,
  cancelPendingRequest,
  cancelAllPendingRequests,
  isRequestCancelledError,
  getActiveTokensCount,
  useCancelToken
};
