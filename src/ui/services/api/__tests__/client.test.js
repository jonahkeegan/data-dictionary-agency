/**
 * Unit tests for API client
 */
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import { 
  createApiClient, 
  apiClient, 
  handleApiError, 
  isRetryable, 
  retryRequest 
} from '../client';
import { getConfig } from '../../../config';

// Mock the config module
jest.mock('../../../config', () => ({
  getConfig: jest.fn().mockReturnValue({
    apiUrl: 'http://test-api.com',
    timeout: 5000,
    retryCount: 2,
    logLevel: 'debug'
  }),
  getEnvironment: jest.fn().mockReturnValue('test')
}));

// Mock console methods to prevent test noise
const originalConsoleError = console.error;
const originalConsoleLog = console.log;

describe('API Client', () => {
  let mock;
  
  beforeEach(() => {
    // Create a new mock adapter for axios
    mock = new MockAdapter(axios);
    
    // Clear localStorage
    localStorage.clear();
    
    // Reset all mocks
    jest.clearAllMocks();
    
    // Silence console during tests
    console.error = jest.fn();
    console.log = jest.fn();
  });
  
  afterEach(() => {
    // Restore console methods
    console.error = originalConsoleError;
    console.log = originalConsoleLog;
    
    // Reset mock adapter
    mock.reset();
  });
  
  afterAll(() => {
    // Restore all mocks
    jest.restoreAllMocks();
    
    // Reset mock adapter
    mock.restore();
  });
  
  describe('createApiClient', () => {
    test('creates client with correct base configuration', () => {
      const client = createApiClient();
      
      expect(client.defaults.baseURL).toBe('http://test-api.com');
      expect(client.defaults.timeout).toBe(5000);
      expect(client.defaults.headers['Content-Type']).toBe('application/json');
    });
    
    test('uses custom configuration when provided', () => {
      const client = createApiClient({
        baseURL: 'http://custom-api.com',
        timeout: 10000,
        headers: {
          'X-Custom-Header': 'custom-value'
        }
      });
      
      expect(client.defaults.baseURL).toBe('http://custom-api.com');
      expect(client.defaults.timeout).toBe(10000);
      expect(client.defaults.headers['Content-Type']).toBe('application/json');
      expect(client.defaults.headers['X-Custom-Header']).toBe('custom-value');
    });
    
    test('adds auth token to requests when present', async () => {
      // Set token in localStorage
      localStorage.setItem('auth_token', 'test-token');
      
      // Create client and set up mock
      const client = createApiClient();
      mock.onGet('/test-auth').reply(config => {
        // Assert that the token was added to headers
        expect(config.headers.Authorization).toBe('Bearer test-token');
        return [200, { success: true }];
      });
      
      // Make request
      await client.get('/test-auth');
      
      // Verify the request was made
      expect(mock.history.get.length).toBe(1);
    });
    
    test('does not add auth token when not present', async () => {
      // Create client and set up mock
      const client = createApiClient();
      mock.onGet('/test-no-auth').reply(config => {
        // Assert that no Authorization header is present
        expect(config.headers.Authorization).toBeUndefined();
        return [200, { success: true }];
      });
      
      // Make request
      await client.get('/test-no-auth');
      
      // Verify the request was made
      expect(mock.history.get.length).toBe(1);
    });
  });
  
  describe('handleApiError', () => {
    test('transforms API errors into standardized format', async () => {
      // Set up error response
      mock.onGet('/error-test').reply(400, {
        detail: 'Bad request error',
        code: 'VALIDATION_ERROR',
        errors: [{ field: 'name', message: 'Required field' }]
      });
      
      // Create client
      const client = createApiClient();
      
      try {
        await client.get('/error-test');
        // Should not reach here
        expect(true).toBe(false);
      } catch (error) {
        // Verify error structure
        expect(error.status).toBe(400);
        expect(error.message).toBe('Bad request error');
        expect(error.code).toBe('VALIDATION_ERROR');
        expect(error.errors).toHaveLength(1);
        expect(error.errors[0].field).toBe('name');
        
        // Verify error flags
        expect(error.isNetworkError).toBe(false);
        expect(error.isClientError).toBe(true);
        expect(error.isServerError).toBe(false);
        expect(error.isAuthError).toBe(false);
      }
      
      // Verify error was logged
      expect(console.error).toHaveBeenCalled();
    });
    
    test('handles network errors correctly', async () => {
      // Set up network error
      mock.onGet('/network-error').networkError();
      
      // Create client
      const client = createApiClient();
      
      try {
        await client.get('/network-error');
        // Should not reach here
        expect(true).toBe(false);
      } catch (error) {
        // Verify error flags
        expect(error.isNetworkError).toBe(true);
        expect(error.isClientError).toBe(false);
        expect(error.isServerError).toBe(false);
      }
    });
    
    test('handles server errors correctly', async () => {
      // Set up server error
      mock.onGet('/server-error').reply(500, {
        detail: 'Internal server error'
      });
      
      // Create client
      const client = createApiClient();
      
      try {
        await client.get('/server-error');
        // Should not reach here
        expect(true).toBe(false);
      } catch (error) {
        // Verify error flags
        expect(error.isNetworkError).toBe(false);
        expect(error.isClientError).toBe(false);
        expect(error.isServerError).toBe(true);
      }
    });
    
    test('handles auth errors correctly', async () => {
      // Set up auth error
      mock.onGet('/auth-error').reply(401, {
        detail: 'Unauthorized access'
      });
      
      // Create client
      const client = createApiClient();
      
      try {
        await client.get('/auth-error');
        // Should not reach here
        expect(true).toBe(false);
      } catch (error) {
        // Verify error flags
        expect(error.isNetworkError).toBe(false);
        expect(error.isClientError).toBe(true);
        expect(error.isServerError).toBe(false);
        expect(error.isAuthError).toBe(true);
      }
    });
  });
  
  describe('isRetryable', () => {
    test('identifies network errors as retryable', () => {
      const networkError = { isNetworkError: true };
      expect(isRetryable(networkError)).toBe(true);
    });
    
    test('identifies server errors as retryable', () => {
      const serverError = { isServerError: true };
      expect(isRetryable(serverError)).toBe(true);
    });
    
    test('identifies client errors as non-retryable', () => {
      const clientError = { isClientError: true };
      expect(isRetryable(clientError)).toBe(false);
    });
  });
  
  describe('retryRequest', () => {
    test('does not retry successful requests', async () => {
      // Create mock function for API call
      const apiCall = jest.fn().mockResolvedValue({ success: true });
      
      // Execute with retry
      const result = await retryRequest(apiCall);
      
      // Verify that it was called exactly once
      expect(apiCall).toHaveBeenCalledTimes(1);
      expect(result).toEqual({ success: true });
    });
    
    test('retries retryable errors up to the configured limit', async () => {
      // Mock API call that fails with a retryable error, then succeeds
      const apiCall = jest.fn()
        .mockRejectedValueOnce({ isNetworkError: true })
        .mockRejectedValueOnce({ isServerError: true })
        .mockResolvedValue({ success: true });
      
      // Execute with retry (config sets retryCount to 2)
      const result = await retryRequest(apiCall);
      
      // Verify it was called 3 times (initial + 2 retries)
      expect(apiCall).toHaveBeenCalledTimes(3);
      expect(result).toEqual({ success: true });
    });
    
    test('does not retry non-retryable errors', async () => {
      // Mock API call that fails with a non-retryable error
      const apiCall = jest.fn().mockRejectedValue({ isClientError: true });
      
      // Execute with retry
      try {
        await retryRequest(apiCall);
        // Should not reach here
        expect(true).toBe(false);
      } catch (error) {
        // Verify it was called only once
        expect(apiCall).toHaveBeenCalledTimes(1);
        expect(error.isClientError).toBe(true);
      }
    });
    
    test('respects custom retry limit', async () => {
      // Mock API call that always fails with a retryable error
      const apiCall = jest.fn().mockRejectedValue({ isNetworkError: true });
      
      // Execute with custom retry limit of 3
      try {
        await retryRequest(apiCall, 3);
        // Should not reach here
        expect(true).toBe(false);
      } catch (error) {
        // Verify it was called exactly 4 times (initial + 3 retries)
        expect(apiCall).toHaveBeenCalledTimes(4);
        expect(error.isNetworkError).toBe(true);
      }
    });
  });
});
