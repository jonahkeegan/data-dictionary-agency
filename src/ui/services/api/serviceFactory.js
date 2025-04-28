/**
 * Service factory for creating and managing service instances
 * Provides a centralized point for accessing API services
 */
import { createApiClient } from './client';
import BaseService from './baseService';
import { RepositoryService } from './repositories';
import { SchemaService } from './schemas';

// Import utils and mock services
import { shouldUseMockServices } from '../../utils/common';
import mockServiceFactory from '../mock/mockServiceFactory'; 

/**
 * Service factory for creating and managing service instances
 */
class ServiceFactory {
  /**
   * Singleton instance
   * @type {ServiceFactory}
   * @private
   */
  static instance = null;
  
  /**
   * Create a new service factory
   * @private
   */
  constructor() {
    this.apiClient = createApiClient();
    this.services = new Map();
    this.mockMode = shouldUseMockServices();
  }
  
  /**
   * Get singleton instance of service factory
   * @returns {ServiceFactory} Service factory instance
   */
  static getInstance() {
    if (!ServiceFactory.instance) {
      ServiceFactory.instance = new ServiceFactory();
    }
    return ServiceFactory.instance;
  }
  
  /**
   * Get repository service
   * @returns {import('./repositories').RepositoryService} Repository service
   */
  getRepositoryService() {
    if (!this.services.has('repository')) {
      const service = this.mockMode
        ? mockServiceFactory.getRepositoryService()
        : new RepositoryService(this.apiClient, {
            defaultTTL: 600 // 10 minutes for repositories
          });
      this.services.set('repository', service);
    }
    return this.services.get('repository');
  }
  
  /**
   * Get schema service
   * @returns {import('./schemas').SchemaService} Schema service
   */
  getSchemaService() {
    if (!this.services.has('schema')) {
      const service = this.mockMode
        ? mockServiceFactory.getSchemaService()
        : new SchemaService(this.apiClient, {
            defaultTTL: 300 // 5 minutes for schemas
          });
      this.services.set('schema', service);
    }
    return this.services.get('schema');
  }
  
  /**
   * Get format service
   * @returns {import('./formats').FormatService} Format service
   */
  getFormatService() {
    if (!this.services.has('format')) {
      // Lazy import to prevent circular dependencies
      const { FormatService } = require('./formats');
      
      const service = this.mockMode
        ? mockServiceFactory.getFormatService()
        : new FormatService(this.apiClient, {
            defaultTTL: 1800 // 30 minutes for formats
          });
      this.services.set('format', service);
    }
    return this.services.get('format');
  }
  
  /**
   * Get authentication service
   * @returns {import('./auth').AuthService} Authentication service
   */
  getAuthService() {
    if (!this.services.has('auth')) {
      // Lazy import to prevent circular dependencies
      const { AuthService } = require('./auth');
      
      const service = this.mockMode
        ? mockServiceFactory.getAuthService()
        : new AuthService(this.apiClient, {
            defaultTTL: 120 // 2 minutes for auth
          });
      this.services.set('auth', service);
    }
    return this.services.get('auth');
  }
  
  /**
   * Clear all service caches
   */
  clearCache() {
    this.services.forEach(service => {
      if (service.clearCache) {
        service.clearCache();
      }
    });
  }
  
  /**
   * Set the factory to mock mode
   * @param {boolean} [enabled=true] - Whether to enable mock mode
   */
  setMockMode(enabled = true) {
    // Only clear services if mode changes
    if (this.mockMode !== enabled) {
      this.mockMode = enabled;
      this.services.clear();
    }
  }
  
  /**
   * Create a factory with mock services
   * @returns {Object} Mock service factory providing the same interface
   */
  static createMockFactory() {
    // For testing, return our dedicated mockServiceFactory directly
    return mockServiceFactory;
  }
  
  /**
   * Reset the singleton instance
   * Used for testing
   */
  static resetInstance() {
    ServiceFactory.instance = null;
  }
}

// Default instance export for convenience
export const serviceFactory = ServiceFactory.getInstance();

// Export class for testing or custom instantiation
export default ServiceFactory;
