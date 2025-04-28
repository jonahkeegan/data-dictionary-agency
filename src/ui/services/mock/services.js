/**
 * Mock service implementations for testing and offline development
 * Provides in-memory implementations of all API services
 */

import BaseService from '../api/baseService';
import { delay } from '../../utils/common';

// Mock data
const mockRepositories = [
  {
    id: '1',
    name: 'E-Commerce Database',
    description: 'Product catalog and order management database',
    url: 'https://github.com/example/ecommerce-db',
    status: 'active',
    progress: 100,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-10T00:00:00Z'
  },
  {
    id: '2',
    name: 'Customer Analytics',
    description: 'Customer behavior analytics database',
    url: 'https://github.com/example/analytics-db',
    status: 'pending',
    progress: 60,
    created_at: '2025-02-01T00:00:00Z',
    updated_at: '2025-02-15T00:00:00Z'
  },
  {
    id: '3',
    name: 'Inventory Management',
    description: 'Warehouse inventory tracking system',
    url: 'https://github.com/example/inventory',
    status: 'active',
    progress: 100,
    created_at: '2025-03-01T00:00:00Z',
    updated_at: '2025-03-10T00:00:00Z'
  }
];

const mockSchemas = [
  {
    id: '1',
    name: 'Products',
    description: 'Product catalog schema',
    repository_id: '1',
    format_id: '1',
    format_name: 'JSON Schema',
    file_path: '/schemas/products.json',
    created_at: '2025-01-05T00:00:00Z',
    updated_at: '2025-01-10T00:00:00Z',
    content: {
      type: 'object',
      properties: {
        id: { type: 'string' },
        name: { type: 'string' },
        price: { type: 'number' },
        category: { type: 'string' }
      },
      required: ['id', 'name', 'price']
    }
  },
  {
    id: '2',
    name: 'Orders',
    description: 'Customer orders schema',
    repository_id: '1',
    format_id: '2',
    format_name: 'SQL',
    file_path: '/schemas/orders.sql',
    created_at: '2025-01-06T00:00:00Z',
    updated_at: '2025-01-12T00:00:00Z',
    content: {
      tables: [
        {
          name: 'orders',
          columns: [
            { name: 'id', type: 'varchar', primary: true },
            { name: 'customer_id', type: 'varchar', references: 'customers.id' },
            { name: 'order_date', type: 'timestamp' },
            { name: 'status', type: 'varchar' }
          ]
        }
      ]
    }
  },
  {
    id: '3',
    name: 'CustomerEvents',
    description: 'Customer behavior events',
    repository_id: '2',
    format_id: '3',
    format_name: 'Avro',
    file_path: '/schemas/events.avsc',
    created_at: '2025-02-10T00:00:00Z',
    updated_at: '2025-02-15T00:00:00Z',
    content: {
      type: 'record',
      name: 'Event',
      fields: [
        { name: 'id', type: 'string' },
        { name: 'customer_id', type: 'string' },
        { name: 'event_type', type: 'string' },
        { name: 'timestamp', type: 'long' }
      ]
    }
  }
];

const mockFormats = [
  {
    id: '1',
    name: 'JSON Schema',
    description: 'JSON Schema specification',
    mime_type: 'application/schema+json',
    file_extensions: ['.json', '.schema.json'],
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    schema_count: 10,
    detection_patterns: ['"\\$schema"\\s*:\\s*"https?://json-schema.org'],
    example: '{\n  "$schema": "http://json-schema.org/draft-07/schema#",\n  "type": "object"\n}'
  },
  {
    id: '2',
    name: 'SQL',
    description: 'SQL Schema definition',
    mime_type: 'text/plain',
    file_extensions: ['.sql', '.ddl'],
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    schema_count: 8,
    detection_patterns: ['CREATE\\s+TABLE', 'ALTER\\s+TABLE'],
    example: 'CREATE TABLE users (\n  id INT PRIMARY KEY,\n  name VARCHAR(255)\n);'
  },
  {
    id: '3',
    name: 'Avro',
    description: 'Apache Avro schema',
    mime_type: 'application/avro',
    file_extensions: ['.avsc', '.avro'],
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    schema_count: 6,
    detection_patterns: ['"type"\\s*:\\s*"record"', '"namespace"\\s*:'],
    example: '{\n  "type": "record",\n  "name": "User",\n  "fields": [\n    {"name": "id", "type": "string"},\n    {"name": "name", "type": "string"}\n  ]\n}'
  }
];

const mockRelationships = [
  {
    id: '1',
    source_schema_id: '1',
    target_schema_id: '2',
    relationship_type: 'one-to-many',
    confidence: 0.95,
    properties: {
      source_field: 'id',
      target_field: 'product_id'
    }
  },
  {
    id: '2',
    source_schema_id: '2',
    target_schema_id: '3',
    relationship_type: 'reference',
    confidence: 0.82,
    properties: {
      source_field: 'customer_id',
      target_field: 'customer_id'
    }
  }
];

const mockUser = {
  id: 'user-1',
  username: 'testuser',
  email: 'user@example.com',
  first_name: 'Test',
  last_name: 'User',
  created_at: '2025-01-01T00:00:00Z',
  last_login: '2025-04-01T00:00:00Z'
};

/**
 * Helper function to clone objects to avoid reference issues
 * @param {*} obj - Object to clone
 * @returns {*} Cloned object
 */
function cloneDeep(obj) {
  return JSON.parse(JSON.stringify(obj));
}

/**
 * Helper function to find an item by ID in an array
 * @param {Array} array - Array to search
 * @param {string} id - ID to find
 * @returns {Object|undefined} Found item or undefined
 */
function findById(array, id) {
  return array.find(item => item.id === id);
}

/**
 * Mock Repository Service
 * @extends BaseService
 */
export class MockRepositoryService extends BaseService {
  constructor() {
    super(null); // No API client for mock service
    this.repositories = cloneDeep(mockRepositories);
  }
  
  /**
   * Get all repositories
   * @param {Object} [params={}] - Query parameters
   * @returns {Promise<Array>} Array of repository objects
   */
  async getAll(params = {}) {
    await delay(300); // Simulate network latency
    
    let result = this.repositories;
    
    // Handle skip and limit
    if (params.skip || params.limit) {
      const skip = params.skip || 0;
      const limit = params.limit || this.repositories.length;
      result = result.slice(skip, skip + limit);
    }
    
    return cloneDeep(result);
  }
  
  /**
   * Get a repository by ID
   * @param {string} id - Repository ID
   * @returns {Promise<Object>} Repository object
   */
  async getById(id) {
    await delay(200); // Simulate network latency
    
    const repository = findById(this.repositories, id);
    
    if (!repository) {
      const error = new Error('Repository not found');
      error.status = 404;
      throw error;
    }
    
    return cloneDeep(repository);
  }
  
  /**
   * Create a new repository
   * @param {Object} data - Repository data
   * @returns {Promise<Object>} Created repository object
   */
  async create(data) {
    await delay(400); // Simulate network latency
    
    const newId = String(this.repositories.length + 1);
    const now = new Date().toISOString();
    
    const newRepository = {
      id: newId,
      name: data.name,
      description: data.description || '',
      url: data.url,
      status: 'pending',
      progress: 0,
      created_at: now,
      updated_at: now
    };
    
    this.repositories.push(newRepository);
    
    return cloneDeep(newRepository);
  }
  
  /**
   * Delete a repository by ID
   * @param {string} id - Repository ID
   * @returns {Promise<boolean>} True if deletion was successful
   */
  async delete(id) {
    await delay(300); // Simulate network latency
    
    const index = this.repositories.findIndex(repo => repo.id === id);
    
    if (index === -1) {
      const error = new Error('Repository not found');
      error.status = 404;
      throw error;
    }
    
    this.repositories.splice(index, 1);
    
    return true;
  }
  
  /**
   * Trigger analysis for a repository
   * @param {string} id - Repository ID
   * @returns {Promise<Object>} Analysis result
   */
  async triggerAnalysis(id) {
    await delay(300); // Simulate network latency
    
    const repository = findById(this.repositories, id);
    
    if (!repository) {
      const error = new Error('Repository not found');
      error.status = 404;
      throw error;
    }
    
    // Update repository progress
    const repoIndex = this.repositories.findIndex(r => r.id === id);
    if (repoIndex !== -1) {
      this.repositories[repoIndex].status = 'processing';
      this.repositories[repoIndex].progress = 25;
    }
    
    return {
      id: `analysis-${id}`,
      status: 'in_progress',
      progress: 25
    };
  }
}

/**
 * Mock Schema Service
 * @extends BaseService
 */
export class MockSchemaService extends BaseService {
  constructor() {
    super(null); // No API client for mock service
    this.schemas = cloneDeep(mockSchemas);
    this.relationships = cloneDeep(mockRelationships);
  }
  
  /**
   * Get all schemas
   * @param {Object} [params={}] - Query parameters
   * @returns {Promise<Array>} Array of schema objects
   */
  async getAll(params = {}) {
    await delay(300); // Simulate network latency
    
    let result = this.schemas;
    
    // Filter by repository_id if provided
    if (params.repository_id) {
      result = result.filter(schema => schema.repository_id === params.repository_id);
    }
    
    // Filter by format_id if provided
    if (params.format_id) {
      result = result.filter(schema => schema.format_id === params.format_id);
    }
    
    // Handle skip and limit
    if (params.skip || params.limit) {
      const skip = params.skip || 0;
      const limit = params.limit || result.length;
      result = result.slice(skip, skip + limit);
    }
    
    return cloneDeep(result);
  }
  
  /**
   * Get a schema by ID
   * @param {string} id - Schema ID
   * @returns {Promise<Object>} Schema object
   */
  async getById(id) {
    await delay(200); // Simulate network latency
    
    const schema = findById(this.schemas, id);
    
    if (!schema) {
      const error = new Error('Schema not found');
      error.status = 404;
      throw error;
    }
    
    return cloneDeep(schema);
  }
  
  /**
   * Create a new schema
   * @param {Object} data - Schema data
   * @returns {Promise<Object>} Created schema object
   */
  async create(data) {
    await delay(400); // Simulate network latency
    
    const newId = String(this.schemas.length + 1);
    const now = new Date().toISOString();
    
    const newSchema = {
      id: newId,
      name: data.name,
      description: data.description || '',
      repository_id: data.repository_id,
      format_id: data.format_id || '1',
      format_name: data.format_id === '1' ? 'JSON Schema' : 
                  data.format_id === '2' ? 'SQL' : 'Avro',
      file_path: data.file_path || `/schemas/${data.name.toLowerCase().replace(/\s/g, '_')}.json`,
      content: data.content || {},
      created_at: now,
      updated_at: now
    };
    
    this.schemas.push(newSchema);
    
    return cloneDeep(newSchema);
  }
  
  /**
   * Update a schema
   * @param {string} id - Schema ID
   * @param {Object} data - Updated Schema data
   * @returns {Promise<Object>} Updated Schema object
   */
  async update(id, data) {
    await delay(400); // Simulate network latency
    
    const index = this.schemas.findIndex(schema => schema.id === id);
    
    if (index === -1) {
      const error = new Error('Schema not found');
      error.status = 404;
      throw error;
    }
    
    // Update schema with new data
    const updatedSchema = {
      ...this.schemas[index],
      ...data,
      updated_at: new Date().toISOString()
    };
    
    this.schemas[index] = updatedSchema;
    
    return cloneDeep(updatedSchema);
  }
  
  /**
   * Delete a schema
   * @param {string} id - Schema ID
   * @returns {Promise<boolean>} True if deletion was successful
   */
  async delete(id) {
    await delay(300); // Simulate network latency
    
    const index = this.schemas.findIndex(schema => schema.id === id);
    
    if (index === -1) {
      const error = new Error('Schema not found');
      error.status = 404;
      throw error;
    }
    
    this.schemas.splice(index, 1);
    
    // Also remove any relationships involving this schema
    this.relationships = this.relationships.filter(
      rel => rel.source_schema_id !== id && rel.target_schema_id !== id
    );
    
    return true;
  }
  
  /**
   * Get relationships for a schema
   * @param {string} id - Schema ID
   * @returns {Promise<Array>} Array of relationship objects
   */
  async getRelationships(id) {
    await delay(300); // Simulate network latency
    
    // Check if schema exists
    const schema = findById(this.schemas, id);
    
    if (!schema) {
      const error = new Error('Schema not found');
      error.status = 404;
      throw error;
    }
    
    // Find relationships where this schema is either source or target
    const relationships = this.relationships.filter(
      rel => rel.source_schema_id === id || rel.target_schema_id === id
    );
    
    return cloneDeep(relationships);
  }
  
  /**
   * Export a schema to a specific format
   * @param {string} id - Schema ID
   * @param {string} [format='json'] - Export format
   * @returns {Promise<Object>} Exported schema data
   */
  async export(id, format = 'json') {
    await delay(500); // Simulate network latency
    
    const schema = findById(this.schemas, id);
    
    if (!schema) {
      const error = new Error('Schema not found');
      error.status = 404;
      throw error;
    }
    
    // Format the content based on requested format
    let content = '';
    if (format === 'json') {
      content = JSON.stringify(schema.content, null, 2);
    } else if (format === 'yaml') {
      // Simple YAML conversion
      content = JSON.stringify(schema.content, null, 2)
        .replace(/^\{|\}$/g, '')
        .replace(/"([^"]+)":/g, '$1:');
    } else {
      content = `# Export format ${format} not fully implemented\n` + 
                JSON.stringify(schema.content, null, 2);
    }
    
    return {
      format,
      content,
      schema_id: id,
      schema_name: schema.name
    };
  }
}

/**
 * Mock Format Service
 * @extends BaseService
 */
export class MockFormatService extends BaseService {
  constructor() {
    super(null); // No API client for mock service
    this.formats = cloneDeep(mockFormats);
  }
  
  /**
   * Get all formats
   * @param {Object} [params={}] - Query parameters
   * @returns {Promise<Array>} Array of format objects
   */
  async getAll(params = {}) {
    await delay(300); // Simulate network latency
    
    let result = this.formats;
    
    // Handle skip and limit
    if (params.skip || params.limit) {
      const skip = params.skip || 0;
      const limit = params.limit || result.length;
      result = result.slice(skip, skip + limit);
    }
    
    return cloneDeep(result);
  }
  
  /**
   * Get a format by ID
   * @param {string} id - Format ID
   * @returns {Promise<Object>} Format object
   */
  async getById(id) {
    await delay(200); // Simulate network latency
    
    const format = findById(this.formats, id);
    
    if (!format) {
      const error = new Error('Format not found');
      error.status = 404;
      throw error;
    }
    
    return cloneDeep(format);
  }
  
  /**
   * Get list of supported formats
   * @returns {Promise<Array>} Array of format strings
   */
  async getSupportedFormats() {
    await delay(100); // Simulate network latency
    
    // Return just the names of formats
    return this.formats.map(format => format.name);
  }
  
  /**
   * Validate a schema against a format
   * @param {string} formatId - Format ID
   * @param {Object} schema - Schema to validate
   * @returns {Promise<Object>} Validation result
   */
  async validateSchema(formatId, schema) {
    await delay(500); // Simulate network latency
    
    const format = findById(this.formats, formatId);
    
    if (!format) {
      const error = new Error('Format not found');
      error.status = 404;
      throw error;
    }
    
    // Simulate schema validation (always succeeds)
    return {
      valid: true,
      errors: [],
      format: format.name
    };
  }
}

/**
 * Mock Authentication Service
 * @extends BaseService
 */
export class MockAuthService extends BaseService {
  constructor() {
    super(null); // No API client for mock service
    this.user = cloneDeep(mockUser);
    this.isLoggedIn = false;
  }
  
  /**
   * Login with credentials
   * @param {Object} credentials - User credentials
   * @returns {Promise<Object>} Authentication result
   */
  async login(credentials) {
    await delay(500); // Simulate network latency
    
    // Check credentials
    if (credentials.username === 'testuser' && credentials.password === 'password') {
      this.isLoggedIn = true;
      
      return {
        token: 'mock-jwt-token',
        refresh_token: 'mock-refresh-token',
        user: cloneDeep(this.user)
      };
    } else {
      const error = new Error('Invalid credentials');
      error.status = 401;
      throw error;
    }
  }
  
  /**
   * Logout current user
   * @returns {Promise<boolean>} Success indicator
   */
  async logout() {
    await delay(200); // Simulate network latency
    
    this.isLoggedIn = false;
    return true;
  }
  
  /**
   * Register a new user
   * @param {Object} userData - User registration data
   * @returns {Promise<Object>} Authentication result
   */
  async register(userData) {
    await delay(700); // Simulate network latency
    
    // Simple validation
    if (!userData.username || !userData.email || !userData.password) {
      const error = new Error('Missing required fields');
      error.status = 400;
      throw error;
    }
    
    // Set the new user data
    this.user = {
      id: 'user-new',
      username: userData.username,
      email: userData.email,
      first_name: userData.first_name || '',
      last_name: userData.last_name || '',
      created_at: new Date().toISOString(),
      last_login: new Date().toISOString()
    };
    
    this.isLoggedIn = true;
    
    return {
      token: 'mock-jwt-token',
      refresh_token: 'mock-refresh-token',
      user: cloneDeep(this.user)
    };
  }
  
  /**
   * Get current user
   * @returns {Promise<Object>} User data
   */
  async getCurrentUser() {
    await delay(200); // Simulate network latency
    
    if (!this.isLoggedIn) {
      const error = new Error('Not authenticated');
      error.status = 401;
      throw error;
    }
    
    return cloneDeep(this.user);
  }
  
  /**
   * Refresh token
   * @returns {Promise<Object>} New tokens
   */
  async refreshToken() {
    await delay(300); // Simulate network latency
    
    if (!this.isLoggedIn) {
      const error = new Error('Invalid refresh token');
      error.status = 401;
      throw error;
    }
    
    return {
      token: 'new-mock-jwt-token',
      refresh_token: 'new-mock-refresh-token',
      user: cloneDeep(this.user)
    };
  }
  
  /**
   * Check if user is authenticated
   * @returns {boolean} Authentication status
   */
  isAuthenticated() {
    return this.isLoggedIn;
  }
}

/**
 * Helper utility to add artificial delay
 * @param {number} ms - Milliseconds to delay
 * @returns {Promise} Promise that resolves after delay
 */
export function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
