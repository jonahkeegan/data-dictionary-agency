/**
 * Service Factory
 * 
 * Central factory for creating and managing service instances.
 * Provides singleton instances of each domain service with
 * configuration options and environment-aware behavior.
 */

import { isMockEnabled } from './config';

// Service instance cache
const serviceInstances = new Map();

// Import actual service implementations
// These will be imported and initialized lazily
let repositoryServiceImpl;
let schemaServiceImpl;
let formatServiceImpl;
let authServiceImpl;

// Import mock service implementations
// These will be imported and initialized lazily
let mockRepositoryServiceImpl;
let mockSchemaServiceImpl;
let mockFormatServiceImpl;
let mockAuthServiceImpl;

/**
 * Lazy load a module to improve initial loading performance
 * @param {Function} importFn - Function that returns an import promise
 * @returns {Promise} Promise resolving to the imported module
 */
const lazyLoad = async (importFn) => {
  try {
    const module = await importFn();
    return module.default || module;
  } catch (error) {
    console.error('Failed to lazy load service:', error);
    throw error;
  }
};

/**
 * Get a service instance, creating it if it doesn't exist
 * @param {string} serviceType - Type of service to get
 * @param {Function} createFn - Function to create the service if needed
 * @param {boolean} [useMock=false] - Whether to use the mock implementation
 * @returns {Object} Service instance
 */
const getServiceInstance = (serviceType, createFn, useMock = false) => {
  const key = `${serviceType}${useMock ? ':mock' : ''}`;
  
  if (!serviceInstances.has(key)) {
    serviceInstances.set(key, createFn());
  }
  
  return serviceInstances.get(key);
};

/**
 * Service Factory - provides access to all API services
 */
export const serviceFactory = {
  /**
   * Get an instance of the repository service
   * @param {boolean} [options.forceMock] - Force using mock service
   * @param {boolean} [options.forceReal] - Force using real service
   * @returns {Object} Repository service instance
   */
  getRepositoryService: (options = {}) => {
    const useMock = options.forceMock || (isMockEnabled() && !options.forceReal);

    return getServiceInstance('repository', async () => {
      if (useMock) {
        if (!mockRepositoryServiceImpl) {
          mockRepositoryServiceImpl = await lazyLoad(() => 
            import('../mock/mockRepositoryService')
          );
        }
        return new mockRepositoryServiceImpl();
      } 
      
      if (!repositoryServiceImpl) {
        repositoryServiceImpl = await lazyLoad(() => 
          import('./repositoryService')
        );
      }
      return new repositoryServiceImpl();
    }, useMock);
  },
  
  /**
   * Get an instance of the schema service
   * @param {boolean} [options.forceMock] - Force using mock service
   * @param {boolean} [options.forceReal] - Force using real service
   * @returns {Object} Schema service instance
   */
  getSchemaService: (options = {}) => {
    const useMock = options.forceMock || (isMockEnabled() && !options.forceReal);

    return getServiceInstance('schema', async () => {
      if (useMock) {
        if (!mockSchemaServiceImpl) {
          mockSchemaServiceImpl = await lazyLoad(() => 
            import('../mock/mockSchemaService')
          );
        }
        return new mockSchemaServiceImpl();
      } 
      
      if (!schemaServiceImpl) {
        schemaServiceImpl = await lazyLoad(() => 
          import('./schemaService')
        );
      }
      return new schemaServiceImpl();
    }, useMock);
  },
  
  /**
   * Get an instance of the format service
   * @param {boolean} [options.forceMock] - Force using mock service
   * @param {boolean} [options.forceReal] - Force using real service
   * @returns {Object} Format service instance
   */
  getFormatService: (options = {}) => {
    const useMock = options.forceMock || (isMockEnabled() && !options.forceReal);

    return getServiceInstance('format', async () => {
      if (useMock) {
        if (!mockFormatServiceImpl) {
          mockFormatServiceImpl = await lazyLoad(() => 
            import('../mock/mockFormatService')
          );
        }
        return new mockFormatServiceImpl();
      } 
      
      if (!formatServiceImpl) {
        formatServiceImpl = await lazyLoad(() => 
          import('./formatService')
        );
      }
      return new formatServiceImpl();
    }, useMock);
  },
  
  /**
   * Get an instance of the authentication service
   * @param {boolean} [options.forceMock] - Force using mock service
   * @param {boolean} [options.forceReal] - Force using real service
   * @returns {Object} Authentication service instance
   */
  getAuthService: (options = {}) => {
    const useMock = options.forceMock || (isMockEnabled() && !options.forceReal);

    return getServiceInstance('auth', async () => {
      if (useMock) {
        if (!mockAuthServiceImpl) {
          mockAuthServiceImpl = await lazyLoad(() => 
            import('../mock/mockAuthService')
          );
        }
        return new mockAuthServiceImpl();
      } 
      
      if (!authServiceImpl) {
        authServiceImpl = await lazyLoad(() => 
          import('./authService')
        );
      }
      return new authServiceImpl();
    }, useMock);
  },
  
  /**
   * Reset all service instances (useful for testing)
   */
  resetAll: () => {
    serviceInstances.clear();
  }
};

export default serviceFactory;
