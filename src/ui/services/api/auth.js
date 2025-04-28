/**
 * Authentication service for the Data Dictionary Agency frontend
 * Provides methods for user authentication and management
 */
import BaseService from './baseService';
import { createCancelToken, generateRequestKey } from './cancelToken';

/**
 * @typedef {import('./baseService').ServiceOptions} ServiceOptions
 */

/**
 * @typedef {Object} User
 * @property {string} id - User ID
 * @property {string} username - Username
 * @property {string} email - Email address
 * @property {string} first_name - First name
 * @property {string} last_name - Last name
 * @property {string} created_at - ISO 8601 creation timestamp
 * @property {string} last_login - ISO 8601 last login timestamp
 */

/**
 * @typedef {Object} LoginCredentials
 * @property {string} username - Username or email
 * @property {string} password - Password
 */

/**
 * @typedef {Object} RegisterUserData
 * @property {string} username - Username
 * @property {string} email - Email address
 * @property {string} password - Password
 * @property {string} [first_name] - First name
 * @property {string} [last_name] - Last name
 */

/**
 * @typedef {Object} AuthResult
 * @property {string} token - JWT token
 * @property {string} refresh_token - Refresh token
 * @property {User} user - User details
 */

/**
 * Authentication service implementation
 * @extends BaseService
 */
export class AuthService extends BaseService {
  /**
   * Login with credentials
   * 
   * @async
   * @param {LoginCredentials} credentials - User credentials
   * @param {ServiceOptions} [options={}] - Request options
   * @returns {Promise<AuthResult>} Authentication result
   * @throws {Error} If the request fails
   */
  async login(credentials, options = {}) {
    // Create cancel token if not provided
    this.setupCancelToken(options, 'login', [credentials]);
    
    try {
      const response = await this.apiClient.post('/auth/login', credentials, options);
      
      // Store token in localStorage on successful login
      if (response.data && response.data.token) {
        localStorage.setItem('auth_token', response.data.token);
        if (response.data.refresh_token) {
          localStorage.setItem('refresh_token', response.data.refresh_token);
        }
      }
      
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
  }
  
  /**
   * Logout current user
   * 
   * @async
   * @param {ServiceOptions} [options={}] - Request options
   * @returns {Promise<void>} Success indicator
   * @throws {Error} If the request fails
   */
  async logout(options = {}) {
    // Create cancel token if not provided
    this.setupCancelToken(options, 'logout', []);
    
    try {
      await this.apiClient.post('/auth/logout', null, options);
      
      // Clear tokens from localStorage
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
      
      // Clear all cache when logging out
      if (this.cacheManager) {
        this.cacheManager.invalidate('.*');
      }
      
      return true;
    } catch (error) {
      // Still remove tokens even if API call fails
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
      
      return this.handleError(error);
    }
  }
  
  /**
   * Register a new user
   * 
   * @async
   * @param {RegisterUserData} userData - User registration data
   * @param {ServiceOptions} [options={}] - Request options
   * @returns {Promise<AuthResult>} Authentication result
   * @throws {Error} If the request fails
   */
  async register(userData, options = {}) {
    // Create cancel token if not provided
    this.setupCancelToken(options, 'register', [userData]);
    
    try {
      const response = await this.apiClient.post('/auth/register', userData, options);
      
      // Store token in localStorage on successful registration
      if (response.data && response.data.token) {
        localStorage.setItem('auth_token', response.data.token);
        if (response.data.refresh_token) {
          localStorage.setItem('refresh_token', response.data.refresh_token);
        }
      }
      
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
  }
  
  /**
   * Get current user information
   * 
   * @async
   * @param {ServiceOptions} [options={}] - Request options
   * @returns {Promise<User>} User information
   * @throws {Error} If the request fails
   */
  async getCurrentUser(options = {}) {
    // Create cancel token if not provided
    this.setupCancelToken(options, 'getCurrentUser', []);
    
    try {
      // Use cached request with short TTL for user data
      return await this.cachedGet('/auth/me', {}, {
        ...options,
        ttl: 120 // 2 minutes TTL for user data
      });
    } catch (error) {
      // If unauthorized, clear tokens
      if (error.status === 401 || error.status === 403) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('refresh_token');
      }
      return this.handleError(error);
    }
  }
  
  /**
   * Refresh authentication token
   * 
   * @async
   * @param {ServiceOptions} [options={}] - Request options
   * @returns {Promise<AuthResult>} New authentication tokens
   * @throws {Error} If the request fails
   */
  async refreshToken(options = {}) {
    // Create cancel token if not provided
    this.setupCancelToken(options, 'refreshToken', []);
    
    // Get refresh token from storage
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      const error = new Error('No refresh token available');
      error.status = 401;
      return this.handleError(error);
    }
    
    try {
      const response = await this.apiClient.post('/auth/refresh', { 
        refresh_token: refreshToken 
      }, options);
      
      // Update tokens in localStorage
      if (response.data && response.data.token) {
        localStorage.setItem('auth_token', response.data.token);
        if (response.data.refresh_token) {
          localStorage.setItem('refresh_token', response.data.refresh_token);
        }
      }
      
      return response.data;
    } catch (error) {
      // If refresh failed, clear tokens
      if (error.response && (error.response.status === 401 || error.response.status === 403)) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('refresh_token');
      }
      return this.handleError(error);
    }
  }
  
  /**
   * Check if user is authenticated
   * 
   * @returns {boolean} Whether user is authenticated
   */
  isAuthenticated() {
    return !!localStorage.getItem('auth_token');
  }
  
  /**
   * Setup cancel token if not provided
   * @private
   * @param {ServiceOptions} options - Request options
   * @param {string} requestType - Request type for key generation
   * @param {Array} params - Request parameters
   */
  setupCancelToken(options, requestType, params) {
    if (!options.cancelToken) {
      const requestKey = generateRequestKey(requestType, params);
      const source = createCancelToken(requestKey);
      options.cancelToken = source.token;
    }
  }
}
