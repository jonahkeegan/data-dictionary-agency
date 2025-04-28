/**
 * Configuration management for the Data Dictionary Agency frontend
 * Provides environment-specific settings and runtime configuration updates
 */

/**
 * Environment-specific configuration settings
 */
const environments = {
  development: {
    apiUrl: 'http://localhost:8000/api',
    timeout: 10000,
    retryCount: 3,
    mockEnabled: true,
    logLevel: 'debug'
  },
  production: {
    apiUrl: '/api',
    timeout: 30000,
    retryCount: 1,
    mockEnabled: false,
    logLevel: 'error'
  },
  test: {
    apiUrl: 'http://localhost:8000/api',
    timeout: 5000,
    retryCount: 0,
    mockEnabled: true,
    logLevel: 'debug'
  }
};

/**
 * Detect current environment
 * @returns {string} Environment name (development, production, or test)
 */
export const getEnvironment = () => {
  // In browser environments, use process.env.NODE_ENV
  if (typeof process !== 'undefined' && process.env && process.env.NODE_ENV) {
    return process.env.NODE_ENV;
  }
  
  // Default to development
  return 'development';
};

/**
 * Get configuration for current environment
 * @returns {Object} Configuration object for current environment
 */
export const getConfig = () => {
  const env = getEnvironment();
  return environments[env] || environments.development;
};

/**
 * Update configuration at runtime (useful for testing)
 * @param {Object} updates - Configuration properties to update
 * @returns {Object} Updated configuration object
 */
export const updateConfig = (updates) => {
  const env = getEnvironment();
  environments[env] = { ...environments[env], ...updates };
  return environments[env];
};
