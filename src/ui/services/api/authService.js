/**
 * Authentication Service
 * 
 * Service for interacting with authentication-related API endpoints.
 * Extends BaseService with auth-specific methods and manages auth tokens.
 */

import { BaseService } from './baseService';
import { apiClient } from './client';

// Default token storage keys
const TOKEN_STORAGE_KEY = 'authToken';
const REFRESH_TOKEN_STORAGE_KEY = 'refreshToken';
const USER_STORAGE_KEY = 'currentUser';

/**
 * Authentication service implementation
 */
export class AuthService extends BaseService {
  /**
   * Create a new auth service instance
   * @param {Object} options - Service options
   */
  constructor(options = {}) {
    super('auth', {
      enableCache: false, // Disable caching for auth requests
      ...options
    });
    
    // Storage keys
    this.tokenKey = options.tokenKey || TOKEN_STORAGE_KEY;
    this.refreshTokenKey = options.refreshTokenKey || REFRESH_TOKEN_STORAGE_KEY;
    this.userKey = options.userKey || USER_STORAGE_KEY;
    
    // Storage implementation (default to localStorage)
    this.storage = options.storage || 
      (typeof window !== 'undefined' ? window.localStorage : null);
    
    // Initialize from storage
    this.initFromStorage();
  }
  
  /**
   * Initialize auth state from storage
   */
  initFromStorage() {
    if (!this.storage) return;
    
    try {
      this.token = this.storage.getItem(this.tokenKey);
      this.refreshToken = this.storage.getItem(this.refreshTokenKey);
      
      const userJson = this.storage.getItem(this.userKey);
      this.user = userJson ? JSON.parse(userJson) : null;
    } catch (error) {
      console.error('Failed to initialize auth from storage:', error);
      this.clearAuth();
    }
  }
  
  /**
   * Set authentication data in storage
   * @param {Object} authData - Authentication data
   * @param {string} authData.token - Authentication token
   * @param {string} authData.refresh_token - Refresh token
   * @param {Object} authData.user - User information
   */
  setAuth(authData) {
    if (!this.storage) return;
    
    try {
      this.token = authData.token;
      this.refreshToken = authData.refresh_token;
      this.user = authData.user;
      
      this.storage.setItem(this.tokenKey, this.token);
      this.storage.setItem(this.refreshTokenKey, this.refreshToken);
      this.storage.setItem(this.userKey, JSON.stringify(this.user));
      
      // Update the authorization header for all future requests
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${this.token}`;
    } catch (error) {
      console.error('Failed to set auth data:', error);
    }
  }
  
  /**
   * Clear authentication data from storage
   */
  clearAuth() {
    if (!this.storage) return;
    
    try {
      this.token = null;
      this.refreshToken = null;
      this.user = null;
      
      this.storage.removeItem(this.tokenKey);
      this.storage.removeItem(this.refreshTokenKey);
      this.storage.removeItem(this.userKey);
      
      // Remove authorization header
      delete apiClient.defaults.headers.common['Authorization'];
    } catch (error) {
      console.error('Failed to clear auth data:', error);
    }
  }
  
  /**
   * Check if the user is authenticated
   * @returns {boolean} True if the user is authenticated
   */
  isAuthenticated() {
    return !!this.token;
  }
  
  /**
   * Get the current user
   * @returns {Object|null} Current user or null if not authenticated
   */
  getCurrentUser() {
    return this.user;
  }
  
  /**
   * Login with username and password
   * @param {Object} credentials - Login credentials
   * @param {string} credentials.username - Username
   * @param {string} credentials.password - Password
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Authentication result
   */
  async login(credentials, options = {}) {
    try {
      const authData = await this.executePost('/login', credentials, options);
      this.setAuth(authData);
      return authData;
    } catch (error) {
      this.clearAuth();
      throw error;
    }
  }
  
  /**
   * Logout current user
   * @param {Object} options - Request options
   * @returns {Promise<boolean>} Success indicator
   */
  async logout(options = {}) {
    try {
      // Try to call logout endpoint if authenticated
      if (this.isAuthenticated()) {
        await this.executePost('/logout', {}, options);
      }
    } catch (error) {
      console.warn('Error during logout:', error);
      // Continue with local logout even if server logout fails
    }
    
    // Clear local auth data
    this.clearAuth();
    return true;
  }
  
  /**
   * Register a new user
   * @param {Object} userData - User registration data
   * @param {string} userData.username - Username
   * @param {string} userData.email - Email address
   * @param {string} userData.password - Password
   * @param {string} [userData.first_name] - First name
   * @param {string} [userData.last_name] - Last name
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Registration result
   */
  async register(userData, options = {}) {
    try {
      const authData = await this.executePost('/register', userData, options);
      this.setAuth(authData);
      return authData;
    } catch (error) {
      this.clearAuth();
      throw error;
    }
  }
  
  /**
   * Refresh the authentication token
   * @param {Object} options - Request options
   * @returns {Promise<Object>} New authentication data
   */
  async refreshToken(options = {}) {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }
    
    try {
      const authData = await this.executePost('/refresh', {
        refresh_token: this.refreshToken
      }, options);
      
      this.setAuth(authData);
      return authData;
    } catch (error) {
      // If refresh fails, clear auth data
      this.clearAuth();
      throw error;
    }
  }
  
  /**
   * Update current user profile
   * @param {Object} userData - User data to update
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Updated user data
   */
  async updateProfile(userData, options = {}) {
    if (!this.isAuthenticated()) {
      throw new Error('User is not authenticated');
    }
    
    const updatedUser = await this.executePut('/me', userData, options);
    
    // Update stored user data
    this.user = updatedUser;
    if (this.storage) {
      this.storage.setItem(this.userKey, JSON.stringify(this.user));
    }
    
    return updatedUser;
  }
  
  /**
   * Change current user password
   * @param {Object} passwordData - Password data
   * @param {string} passwordData.current_password - Current password
   * @param {string} passwordData.new_password - New password
   * @param {Object} options - Request options
   * @returns {Promise<boolean>} Success indicator
   */
  async changePassword(passwordData, options = {}) {
    if (!this.isAuthenticated()) {
      throw new Error('User is not authenticated');
    }
    
    return this.executePost('/change-password', passwordData, options);
  }
  
  /**
   * Request password reset for a user
   * @param {Object} data - Reset request data
   * @param {string} data.email - User email address
   * @param {Object} options - Request options
   * @returns {Promise<boolean>} Success indicator
   */
  async requestPasswordReset(data, options = {}) {
    return this.executePost('/forgot-password', data, options);
  }
  
  /**
   * Reset password using reset token
   * @param {Object} data - Reset data
   * @param {string} data.token - Reset token
   * @param {string} data.password - New password
   * @param {Object} options - Request options
   * @returns {Promise<boolean>} Success indicator
   */
  async resetPassword(data, options = {}) {
    return this.executePost('/reset-password', data, options);
  }
  
  /**
   * Check permissions for the current user
   * @param {string} permission - Permission to check
   * @returns {boolean} True if the user has the permission
   */
  hasPermission(permission) {
    if (!this.user || !this.user.roles) {
      return false;
    }
    
    // Admin role has all permissions
    if (this.user.roles.includes('admin')) {
      return true;
    }
    
    // Check if the user has the specific permission
    return this.user.permissions && this.user.permissions.includes(permission);
  }
}

export default AuthService;
