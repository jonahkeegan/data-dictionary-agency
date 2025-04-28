/**
 * API Error Handler
 * 
 * Standardizes error handling across the application by transforming
 * various error types into a consistent format with helpful properties.
 */

/**
 * Custom API Error class with standardized properties
 */
export class ApiError extends Error {
  /**
   * Create a new API Error
   * @param {string} message - Human readable error message
   * @param {number} status - HTTP status code
   * @param {string} code - Error code
   * @param {Array} errors - Array of detailed errors
   * @param {boolean} isNetworkError - Whether this is a network error
   * @param {boolean} isServerError - Whether this is a server error (5xx)
   * @param {boolean} isClientError - Whether this is a client error (4xx)
   * @param {boolean} isAuthError - Whether this is an authentication error
   * @param {any} original - Original error for debugging
   */
  constructor({
    message = 'An unknown error occurred',
    status = 500,
    code = 'UNKNOWN_ERROR',
    errors = [],
    isNetworkError = false,
    isServerError = false,
    isClientError = false,
    isAuthError = false,
    original = null
  }) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.errors = errors;
    this.isNetworkError = isNetworkError;
    this.isServerError = isServerError;
    this.isClientError = isClientError;
    this.isAuthError = isAuthError;
    this.original = original;
  }

  /**
   * Convert to a plain object suitable for logging
   * @returns {Object} Plain object representation of the error
   */
  toJSON() {
    return {
      name: this.name,
      message: this.message,
      status: this.status,
      code: this.code,
      errors: this.errors,
      isNetworkError: this.isNetworkError,
      isServerError: this.isServerError,
      isClientError: this.isClientError,
      isAuthError: this.isAuthError
    };
  }
}

/**
 * Check if an error is retriable (can be automatically retried)
 * @param {ApiError} error - The API error to check
 * @returns {boolean} Whether the error is retriable
 */
export const isRetriableError = (error) => {
  // Network errors are usually transient and can be retried
  if (error.isNetworkError) {
    return true;
  }

  // Server errors (except 501 Not Implemented, 505 HTTP Version Not Supported)
  if (error.isServerError) {
    return ![501, 505].includes(error.status);
  }

  // Rate limiting (429) can be retried after a delay
  if (error.status === 429) {
    return true;
  }

  // All other errors are not automatically retriable
  return false;
};

/**
 * Transform Axios error into standardized API error
 * @param {Error} error - The error to transform
 * @returns {ApiError} Standardized API error
 */
export const transformAxiosError = (error) => {
  // No response indicates a network error
  if (!error.response) {
    return new ApiError({
      message: 'Network error: Unable to connect to the server',
      code: 'NETWORK_ERROR',
      isNetworkError: true,
      original: error
    });
  }

  const { response } = error;
  const { status, data } = response;

  // Extract error details from response data
  let errorMessage = 'An unknown error occurred';
  let errorCode = 'UNKNOWN_ERROR';
  let errorDetails = [];

  if (data && data.error) {
    errorMessage = data.error.message || errorMessage;
    errorCode = data.error.code || errorCode;
    errorDetails = data.error.details || [];
  }

  // Classify error by status code
  const isServerError = status >= 500 && status < 600;
  const isClientError = status >= 400 && status < 500;
  const isAuthError = status === 401 || status === 403;

  // Special handling for common status codes
  switch (status) {
    case 400:
      errorMessage = data.error?.message || 'Bad request: The server could not understand the request';
      errorCode = data.error?.code || 'BAD_REQUEST';
      break;
    case 401:
      errorMessage = 'Authentication required: Please log in to continue';
      errorCode = 'AUTHENTICATION_REQUIRED';
      break;
    case 403:
      errorMessage = 'Access denied: You do not have permission to access this resource';
      errorCode = 'ACCESS_DENIED';
      break;
    case 404:
      errorMessage = 'Resource not found: The requested resource does not exist';
      errorCode = 'RESOURCE_NOT_FOUND';
      break;
    case 409:
      errorMessage = 'Conflict: The request conflicts with the current state of the resource';
      errorCode = 'RESOURCE_CONFLICT';
      break;
    case 429:
      errorMessage = 'Too many requests: Please try again later';
      errorCode = 'RATE_LIMIT_EXCEEDED';
      break;
    case 500:
      errorMessage = 'Server error: Something went wrong on the server';
      errorCode = 'SERVER_ERROR';
      break;
    default:
      if (isServerError) {
        errorMessage = 'Server error: The server encountered an error processing your request';
        errorCode = 'SERVER_ERROR';
      } else if (isClientError) {
        errorMessage = 'Client error: There was a problem with the request';
        errorCode = 'CLIENT_ERROR';
      }
  }

  return new ApiError({
    message: errorMessage,
    status,
    code: errorCode,
    errors: errorDetails,
    isNetworkError: false,
    isServerError,
    isClientError,
    isAuthError,
    original: error
  });
};

/**
 * Create an error handler middleware for Axios
 * @returns {Function} Error handler function
 */
export const createErrorHandler = () => {
  return (error) => {
    // Transform the error to our standard format
    const apiError = transformAxiosError(error);
    
    // Log errors in development or for server errors
    if (process.env.NODE_ENV !== 'production' || apiError.isServerError) {
      console.error('[API Error]', apiError.toJSON());
      
      // In development, log the original error for debugging
      if (process.env.NODE_ENV === 'development' && apiError.original) {
        console.error('[Original Error]', apiError.original);
      }
    }
    
    // Rethrow as ApiError for consistent error handling
    return Promise.reject(apiError);
  };
};

export default {
  ApiError,
  transformAxiosError,
  createErrorHandler,
  isRetriableError
};
