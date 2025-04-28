/**
 * Mock Service Factory
 * 
 * Central factory for creating mock service instances.
 * Provides consistent access to mock services with realistic behavior.
 */

import MockRepositoryService from './mockRepositoryService';
import MockSchemaService from './mockSchemaService';
import MockFormatService from './mockFormatService';
import MockAuthService from './mockAuthService';

// Service instance cache
const serviceInstances = new Map();

/**
 * Get a service instance, creating it if it doesn't exist
 * @param {string} serviceType - Type of service to get
 * @param {Function} createFn - Function to create the service if needed
 * @returns {Object} Service instance
 */
const getServiceInstance = (serviceType, createFn) => {
  if (!serviceInstances.has(serviceType)) {
    serviceInstances.set(serviceType, createFn());
  }
  
  return serviceInstances.get(serviceType);
};

/**
 * Mock Service Factory - provides access to all mock API services
 */
export const mockServiceFactory = {
  /**
   * Get a mock repository service instance
   * @param {Object} [options] - Service options
   * @returns {MockRepositoryService} Mock repository service
   */
  getRepositoryService: (options = {}) => {
    return getServiceInstance('repository', () => new MockRepositoryService(options));
  },
  
  /**
   * Get a mock schema service instance
   * @param {Object} [options] - Service options
   * @returns {MockSchemaService} Mock schema service
   */
  getSchemaService: (options = {}) => {
    return getServiceInstance('schema', () => new MockSchemaService(options));
  },
  
  /**
   * Get a mock format service instance
   * @param {Object} [options] - Service options
   * @returns {MockFormatService} Mock format service
   */
  getFormatService: (options = {}) => {
    return getServiceInstance('format', () => new MockFormatService(options));
  },
  
  /**
   * Get a mock auth service instance
   * @param {Object} [options] - Service options
   * @returns {MockAuthService} Mock auth service
   */
  getAuthService: (options = {}) => {
    return getServiceInstance('auth', () => new MockAuthService(options));
  },
  
  /**
   * Reset all service instances
   */
  resetAll: () => {
    serviceInstances.clear();
  },
  
  /**
   * Configure failure rates for mock services
   * @param {Object} options - Configuration options
   * @param {number} [options.failureRate=0] - Rate of random failures (0-1)
   * @param {number} [options.minDelay=50] - Minimum response delay in ms
   * @param {number} [options.maxDelay=300] - Maximum response delay in ms
   */
  configure: (options = {}) => {
    const services = [
      'repository', 'schema', 'format', 'auth'
    ];
    
    services.forEach(serviceType => {
      const service = serviceInstances.get(serviceType);
      if (service && typeof service.configure === 'function') {
        service.configure(options);
      }
    });
  }
};

export default mockServiceFactory;
