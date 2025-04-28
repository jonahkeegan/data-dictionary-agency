/**
 * Schema service for the Data Dictionary Agency frontend
 * Provides methods for interacting with schema-related API endpoints
 */
import BaseService from './baseService';
import { createCancelToken, generateRequestKey } from './cancelToken';

/**
 * @typedef {import('./baseService').ServiceOptions} ServiceOptions
 */

/**
 * @typedef {Object} Schema
 * @property {string} id - Schema ID
 * @property {string} name - Schema name
 * @property {string} description - Schema description
 * @property {string} repository_id - Repository ID
 * @property {string} format_id - Format ID
 * @property {string} format_name - Format name
 * @property {string} file_path - File path in repository
 * @property {string} created_at - ISO 8601 creation timestamp
 * @property {string} updated_at - ISO 8601 update timestamp
 * @property {Object} content - Schema-specific content
 */

/**
 * @typedef {Object} SchemaParams
 * @property {string} [repository_id] - Filter by repository ID
 * @property {string} [format_id] - Filter by format ID
 * @property {number} [skip=0] - Number of items to skip
 * @property {number} [limit=100] - Max number of items to return
 * @property {string} [sort] - Field to sort by
 * @property {string} [order] - Sort order ('asc' or 'desc')
 */

/**
 * @typedef {Object} SchemaData
 * @property {string} name - Schema name
 * @property {string} description - Schema description
 * @property {string} repository_id - Repository ID
 * @property {string} [format_id] - Format ID
 * @property {string} [file_path] - File path in repository
 * @property {Object} [content] - Schema-specific content
 */

/**
 * @typedef {Object} Relationship
 * @property {string} id - Relationship ID
 * @property {string} source_schema_id - Source schema ID
 * @property {string} target_schema_id - Target schema ID
 * @property {string} relationship_type - Relationship type
 * @property {number} confidence - Confidence score (0-1)
 * @property {Object} properties - Additional properties
 */

/**
 * @typedef {Object} ExportResult
 * @property {string} format - Export format
 * @property {string} content - Exported content
 */

/**
 * Schema service implementation
 * @extends BaseService
 */
export class SchemaService extends BaseService {
  /**
   * Get all schemas with optional filtering and pagination
   * 
   * @async
   * @param {SchemaParams} [params={}] - Query parameters
   * @param {ServiceOptions} [options={}] - Request options
   * @returns {Promise<Schema[]>} Array of schema objects
   * @throws {Error} If the request fails
   */
  async getAll(params = {}, options = {}) {
    // Create cancel token if not provided
    this.setupCancelToken(options, 'getSchemas', [params]);
    
    try {
      // Use cached request
      return await this.cachedGet('/schemas', params, options);
    } catch (error) {
      return this.handleError(error);
    }
  }
  
  /**
   * Get a schema by ID
   * 
   * @async
   * @param {string} id - Schema ID
   * @param {ServiceOptions} [options={}] - Request options
   * @returns {Promise<Schema>} Schema object
   * @throws {Error} If the request fails
   */
  async getById(id, options = {}) {
    // Create cancel token if not provided
    this.setupCancelToken(options, 'getSchemaById', [id]);
    
    try {
      // Use cached request
      return await this.cachedGet(`/schemas/${id}`, {}, options);
    } catch (error) {
      return this.handleError(error);
    }
  }
  
  /**
   * Create a new schema
   * 
   * @async
   * @param {SchemaData} data - Schema data
   * @param {ServiceOptions} [options={}] - Request options
   * @returns {Promise<Schema>} Created schema object
   * @throws {Error} If the request fails
   */
  async create(data, options = {}) {
    // Create cancel token if not provided
    this.setupCancelToken(options, 'createSchema', [data]);
    
    // Invalidation patterns
    const patterns = [
      '^schemas($|\\?)', // All schemas
      `^repositories/${data.repository_id}/schemas($|\\?)` // Repository schemas
    ];
    
    try {
      const result = await this.executePost('/schemas', data, options);
      
      // Invalidate cache for all patterns
      if (this.cacheManager) {
        patterns.forEach(pattern => {
          this.cacheManager.invalidate(pattern);
        });
      }
      
      return result;
    } catch (error) {
      return this.handleError(error);
    }
  }
  
  /**
   * Update a schema by ID
   * 
   * @async
   * @param {string} id - Schema ID
   * @param {SchemaData} data - Updated schema data
   * @param {ServiceOptions} [options={}] - Request options
   * @returns {Promise<Schema>} Updated schema object
   * @throws {Error} If the request fails
   */
  async update(id, data, options = {}) {
    // Create cancel token if not provided
    this.setupCancelToken(options, 'updateSchema', [id, data]);
    
    // Invalidation patterns
    const patterns = [
      '^schemas($|\\?)', // All schemas
      `^schemas/${id}($|\\?)`, // Specific schema
      `^schemas/${id}/relationships($|\\?)` // Relationships may be affected
    ];
    
    if (data.repository_id) {
      patterns.push(`^repositories/${data.repository_id}/schemas($|\\?)`);
    }
    
    try {
      const result = await this.executePut(`/schemas/${id}`, data, options);
      
      // Invalidate cache for all patterns
      if (this.cacheManager) {
        patterns.forEach(pattern => {
          this.cacheManager.invalidate(pattern);
        });
      }
      
      return result;
    } catch (error) {
      return this.handleError(error);
    }
  }
  
  /**
   * Delete a schema by ID
   * 
   * @async
   * @param {string} id - Schema ID
   * @param {ServiceOptions} [options={}] - Request options
   * @returns {Promise<boolean>} True if deletion was successful
   * @throws {Error} If the request fails
   */
  async delete(id, options = {}) {
    // Create cancel token if not provided
    this.setupCancelToken(options, 'deleteSchema', [id]);
    
    try {
      // Get schema first to know repository_id for cache invalidation
      const schema = await this.getById(id, { ...options, useCache: true });
      
      // Invalidation patterns
      const patterns = [
        '^schemas($|\\?)', // All schemas
        `^schemas/${id}($|\\?)`, // Specific schema
        `^schemas/${id}/relationships($|\\?)` // Relationships
      ];
      
      if (schema && schema.repository_id) {
        patterns.push(`^repositories/${schema.repository_id}/schemas($|\\?)`);
      }
      
      await this.executeDelete(`/schemas/${id}`, options);
      
      // Invalidate cache for all patterns
      if (this.cacheManager) {
        patterns.forEach(pattern => {
          this.cacheManager.invalidate(pattern);
        });
      }
      
      return true;
    } catch (error) {
      return this.handleError(error);
    }
  }
  
  /**
   * Get relationships for a schema
   * 
   * @async
   * @param {string} id - Schema ID
   * @param {ServiceOptions} [options={}] - Request options
   * @returns {Promise<Relationship[]>} Array of relationship objects
   * @throws {Error} If the request fails
   */
  async getRelationships(id, options = {}) {
    // Create cancel token if not provided
    this.setupCancelToken(options, 'getSchemaRelationships', [id]);
    
    try {
      // Use cached request with specific TTL for relationships
      return await this.cachedGet(
        `/schemas/${id}/relationships`, 
        {}, 
        { ...options, ttl: 300 } // 5 minutes TTL
      );
    } catch (error) {
      return this.handleError(error);
    }
  }
  
  /**
   * Export a schema to a specific format
   * 
   * @async
   * @param {string} id - Schema ID
   * @param {string} [format='json'] - Export format (json, yaml, sql, etc.)
   * @param {ServiceOptions} [options={}] - Request options
   * @returns {Promise<ExportResult>} Exported schema data
   * @throws {Error} If the request fails
   */
  async export(id, format = 'json', options = {}) {
    // Create cancel token if not provided
    this.setupCancelToken(options, 'exportSchema', [id, format]);
    
    try {
      const response = await this.apiClient.post(
        `/schemas/${id}/export`, 
        null, 
        {
          params: { format },
          ...options
        }
      );
      
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
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
