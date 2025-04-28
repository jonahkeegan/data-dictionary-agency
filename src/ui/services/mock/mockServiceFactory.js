/**
 * Factory for creating mock service instances
 * Used for development and testing without a backend
 */
import { MockRepositoryService, MockSchemaService, MockFormatService, MockAuthService, delay } from './services';
import mockRepositories from './data/repositories';
import mockSchemas, { relationships as mockRelationships } from './data/schemas';
import mockFormats, { supportedFormats } from './data/formats';

/**
 * Mock Service Factory for testing and offline development
 * Provides in-memory service implementations
 */
class MockServiceFactory {
  constructor() {
    // Create service instances only when first requested
    this.repositoryService = null;
    this.schemaService = null;
    this.formatService = null;
    this.authService = null;
  }
  
  /**
   * Get repository service instance
   * @returns {MockRepositoryService} Repository service
   */
  getRepositoryService() {
    if (!this.repositoryService) {
      this.repositoryService = new MockRepositoryService();
      // Initialize with mock data
      this.repositoryService.repositories = [...mockRepositories];
    }
    return this.repositoryService;
  }
  
  /**
   * Get schema service instance
   * @returns {MockSchemaService} Schema service
   */
  getSchemaService() {
    if (!this.schemaService) {
      this.schemaService = new MockSchemaService();
      // Initialize with mock data
      this.schemaService.schemas = [...mockSchemas];
      this.schemaService.relationships = [...mockRelationships];
    }
    return this.schemaService;
  }
  
  /**
   * Get format service instance
   * @returns {MockFormatService} Format service
   */
  getFormatService() {
    if (!this.formatService) {
      this.formatService = new MockFormatService();
      // Initialize with mock data
      this.formatService.formats = [...mockFormats];
    }
    return this.formatService;
  }
  
  /**
   * Get authentication service instance
   * @returns {MockAuthService} Authentication service
   */
  getAuthService() {
    if (!this.authService) {
      this.authService = new MockAuthService();
    }
    return this.authService;
  }
  
  /**
   * Reset all service instances
   * Useful for testing to recreate a clean state
   */
  resetAll() {
    this.repositoryService = null;
    this.schemaService = null;
    this.formatService = null;
    this.authService = null;
  }
  
  /**
   * Reset a specific service by name
   * @param {string} serviceName - Name of the service to reset (e.g. 'repository')
   */
  resetService(serviceName) {
    switch (serviceName) {
      case 'repository':
        this.repositoryService = null;
        break;
      case 'schema':
        this.schemaService = null;
        break;
      case 'format':
        this.formatService = null;
        break;
      case 'auth':
        this.authService = null;
        break;
      default:
        console.warn(`Unknown service: ${serviceName}`);
    }
  }
  
  /**
   * Simulate network latency for all service methods
   * @param {number} minMs - Minimum latency in milliseconds
   * @param {number} maxMs - Maximum latency in milliseconds
   */
  simulateNetworkLatency(minMs = 200, maxMs = 800) {
    // Apply to all services
    const services = [
      this.getRepositoryService(),
      this.getSchemaService(),
      this.getFormatService(),
      this.getAuthService()
    ];
    
    services.forEach(service => {
      // Get all methods from the service prototype
      const methodNames = Object.getOwnPropertyNames(Object.getPrototypeOf(service))
        .filter(name => 
          typeof service[name] === 'function' && 
          name !== 'constructor' && 
          !name.startsWith('_')
        );
      
      // Wrap each method with artificial delay
      methodNames.forEach(methodName => {
        const originalMethod = service[methodName];
        service[methodName] = async function(...args) {
          // Random delay between minMs and maxMs
          const latency = Math.floor(Math.random() * (maxMs - minMs + 1)) + minMs;
          await delay(latency);
          return originalMethod.apply(this, args);
        };
      });
    });
  }
}

// Create singleton instance
const mockServiceFactory = new MockServiceFactory();

export default mockServiceFactory;
