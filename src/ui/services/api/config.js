/**
 * API configuration manager for environment-specific settings
 */

// Default configuration for all environments
const defaultConfig = {
  apiUrl: 'http://localhost:8000/api',
  timeout: 10000,
  retryCount: 3,
  mockEnabled: false,
  logLevel: 'info',
  cacheTTL: 300000, // 5 minutes in milliseconds
  maxCacheSize: 50 * 1024 * 1024, // 50MB
  circuitBreakerThreshold: 5,
  circuitBreakerTimeout: 30000 // 30 seconds
};

// Environment-specific overrides
const environmentConfigs = {
  development: {
    apiUrl: 'http://localhost:8000/api',
    timeout: 10000,
    retryCount: 3,
    mockEnabled: true,
    logLevel: 'debug',
    cacheTTL: 60000 // 1 minute in development
  },
  test: {
    apiUrl: 'http://localhost:8000/api',
    timeout: 1000,
    retryCount: 0,
    mockEnabled: true,
    logLevel: 'debug',
    cacheTTL: 0 // No caching in test
  },
  staging: {
    apiUrl: 'https://staging-api.data-dictionary-agency.example.com/api',
    timeout: 10000,
    retryCount: 2,
    mockEnabled: false,
    logLevel: 'info'
  },
  production: {
    apiUrl: 'https://api.data-dictionary-agency.example.com/api',
    timeout: 15000,
    retryCount: 1,
    mockEnabled: false,
    logLevel: 'error',
    cacheTTL: 600000 // 10 minutes in production
  }
};

/**
 * Get the current environment
 * @returns {string} The current environment name
 */
const getCurrentEnvironment = () => {
  // This would typically come from environment variables
  // e.g., process.env.NODE_ENV in Node.js
  // For browser environments, this could be set in webpack config
  return process.env.NODE_ENV || 'development';
};

/**
 * Get configuration for the current environment
 * @returns {Object} Configuration object with environment-specific settings
 */
export const getConfig = () => {
  const env = getCurrentEnvironment();
  const envConfig = environmentConfigs[env] || {};
  
  // Merge default config with environment-specific config
  return {
    ...defaultConfig,
    ...envConfig,
    env
  };
};

/**
 * Get the base API URL for the current environment
 * @returns {string} The base API URL
 */
export const getApiUrl = () => {
  return getConfig().apiUrl;
};

/**
 * Check if mock services should be enabled
 * @returns {boolean} True if mock services should be used
 */
export const isMockEnabled = () => {
  return getConfig().mockEnabled;
};

export default {
  getConfig,
  getApiUrl,
  isMockEnabled
};
