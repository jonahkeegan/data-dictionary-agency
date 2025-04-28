/**
 * Mock Auth Service
 * 
 * Mock implementation of the authentication service for development and testing.
 * Uses mock data instead of making actual API calls.
 */

import mockData from './mockData';
const { users, withDelay, withRandomFailure, filterData, generateId, pastDate } = mockData;

// Default token storage keys (in-memory for mock service)
let mockToken = null;
let mockRefreshToken = null;
let mockUser = null;

/**
 * Mock authentication service implementation
 */
export class MockAuthService {
  /**
   * Create a new mock auth service
   * @param {Object} options - Configuration options
   */
  constructor(options = {}) {
    this.options = {
      failureRate: 0,
      minDelay: 50,
      maxDelay: 300,
      ...options
    };
    
    // Create a local copy of users to manipulate
    this.users = [...users];
    
    // Load mock tokens if available
    this.token = mockToken;
    this.refreshToken = mockRefreshToken;
    this.user = mockUser;
  }
  
  /**
   * Configure mock service behavior
   * @param {Object} options - Configuration options
   * @param {number} [options.failureRate] - Rate of random failures (0-1)
   * @param {number} [options.minDelay] - Minimum response delay in ms
   * @param {number} [options.maxDelay] - Maximum response delay in ms
   */
  configure(options = {}) {
    this.options = {
      ...this.options,
      ...options
    };
  }
  
  /**
   * Process the request with configured delay and failure rate
   * @param {*} data - Data to return
   * @returns {Promise} Promise resolving to the data or rejecting with error
   */
  async processRequest(data) {
    // Apply configured delay
    const delayedData = await withDelay(
      data, 
      this.options.minDelay, 
      this.options.maxDelay
    );
    
    // Apply configured failure rate
    return withRandomFailure(
      delayedData, 
      this.options.failureRate
    );
  }
  
  /**
   * Set authentication data in storage
   * @param {Object} authData - Authentication data
   * @param {string} authData.token - Authentication token
   * @param {string} authData.refresh_token - Refresh token
   * @param {Object} authData.user - User information
   */
  setAuth(authData) {
    this.token = authData.token;
    this.refreshToken = authData.refresh_token;
    this.user = authData.user;
    
    // Also update the mock static storage
    mockToken = authData.token;
    mockRefreshToken = authData.refresh_token;
    mockUser = authData.user;
  }
  
  /**
   * Clear authentication data from storage
   */
  clearAuth() {
    this.token = null;
    this.refreshToken = null;
    this.user = null;
    
    // Also clear the mock static storage
    mockToken = null;
    mockRefreshToken = null;
    mockUser = null;
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
    // Find user by username
    const user = this.users.find(user => user.username === credentials.username);
    
    if (!user || credentials.password !== 'password') { // Mock always accepts 'password'
      return Promise.reject({
        response: {
          status: 401,
          data: {
            error: {
              message: 'Invalid username or password',
              code: 'INVALID_CREDENTIALS'
            }
          }
        }
      });
    }
    
    // Generate auth tokens
    const authData = {
      token: `mock-token-${generateId()}`,
      refresh_token: `mock-refresh-${generateId()}`,
      user: {
        ...user,
        last_login: pastDate(0)
      },
      expires_in: 3600
    };
    
    // Store tokens
    this.setAuth(authData);
    
    return this.processRequest(authData);
  }
  
  /**
   * Logout current user
   * @param {Object} options - Request options
   * @returns {Promise<boolean>} Success indicator
   */
  async logout(options = {}) {
    // Clear auth data
    this.clearAuth();
    
    return this.processRequest({ success: true });
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
    // Check if username or email already exists
    const existingUser = this.users.find(
      user => user.username === userData.username || user.email === userData.email
    );
    
    if (existingUser) {
      return Promise.reject({
        response: {
          status: 400,
          data: {
            error: {
              message: 'Username or email already in use',
              code: 'DUPLICATE_USER'
            }
          }
        }
      });
    }
    
    // Create new user
    const newUser = {
      id: generateId('user'),
      username: userData.username,
      email: userData.email,
      first_name: userData.first_name || '',
      last_name: userData.last_name || '',
      roles: ['viewer'], // Default role
      permissions: ['read'], // Default permissions
      created_at: pastDate(0),
      last_login: pastDate(0)
    };
    
    // Add to users list
    this.users.push(newUser);
    
    // Generate auth tokens
    const authData = {
      token: `mock-token-${generateId()}`,
      refresh_token: `mock-refresh-${generateId()}`,
      user: newUser,
      expires_in: 3600
    };
    
    // Store tokens
    this.setAuth(authData);
    
    return this.processRequest(authData);
  }
  
  /**
   * Refresh the authentication token
   * @param {Object} options - Request options
   * @returns {Promise<Object>} New authentication data
   */
  async refreshToken(options = {}) {
    // Check if we have a refresh token
    if (!this.refreshToken) {
      return Promise.reject({
        response: {
          status: 401,
          data: {
            error: {
              message: 'No refresh token available',
              code: 'INVALID_TOKEN'
            }
          }
        }
      });
    }
    
    // Make sure we have a user
    if (!this.user) {
      this.clearAuth();
      return Promise.reject({
        response: {
          status: 401,
          data: {
            error: {
              message: 'Invalid refresh token',
              code: 'INVALID_TOKEN'
            }
          }
        }
      });
    }
    
    // Generate new auth tokens
    const authData = {
      token: `mock-token-${generateId()}`,
      refresh_token: `mock-refresh-${generateId()}`,
      user: this.user,
      expires_in: 3600
    };
    
    // Store tokens
    this.setAuth(authData);
    
    return this.processRequest(authData);
  }
  
  /**
   * Update current user profile
   * @param {Object} userData - User data to update
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Updated user data
   */
  async updateProfile(userData, options = {}) {
    // Check if authenticated
    if (!this.isAuthenticated()) {
      return Promise.reject({
        response: {
          status: 401,
          data: {
            error: {
              message: 'User is not authenticated',
              code: 'UNAUTHORIZED'
            }
          }
        }
      });
    }
    
    // Find user in list
    const index = this.users.findIndex(user => user.id === this.user.id);
    
    if (index === -1) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `User with ID ${this.user.id} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    // Update user data
    const updatedUser = {
      ...this.users[index],
      ...userData,
      // Don't allow updating these fields
      id: this.users[index].id,
      roles: this.users[index].roles,
      permissions: this.users[index].permissions,
      created_at: this.users[index].created_at
    };
    
    // Update in users list
    this.users[index] = updatedUser;
    
    // Update current user
    this.user = updatedUser;
    mockUser = updatedUser;
    
    return this.processRequest(updatedUser);
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
    // Check if authenticated
    if (!this.isAuthenticated()) {
      return Promise.reject({
        response: {
          status: 401,
          data: {
            error: {
              message: 'User is not authenticated',
              code: 'UNAUTHORIZED'
            }
          }
        }
      });
    }
    
    // Verify current password (always 'password' in mock)
    if (passwordData.current_password !== 'password') {
      return Promise.reject({
        response: {
          status: 400,
          data: {
            error: {
              message: 'Current password is incorrect',
              code: 'INVALID_PASSWORD'
            }
          }
        }
      });
    }
    
    // In a mock, we don't actually store the password
    return this.processRequest({ success: true });
  }
  
  /**
   * Request password reset for a user
   * @param {Object} data - Reset request data
   * @param {string} data.email - User email address
   * @param {Object} options - Request options
   * @returns {Promise<boolean>} Success indicator
   */
  async requestPasswordReset(data, options = {}) {
    // Check if email exists
    const user = this.users.find(user => user.email === data.email);
    
    if (!user) {
      // For security reasons, we still return success even if email doesn't exist
      return this.processRequest({ success: true });
    }
    
    // In a real implementation, we would send an email with reset token
    return this.processRequest({ success: true });
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
    // In a mock, we don't validate the token
    // We just return success
    return this.processRequest({ success: true });
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

export default MockAuthService;
