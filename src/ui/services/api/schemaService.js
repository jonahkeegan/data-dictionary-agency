/**
 * Schema Service
 * 
 * Service for interacting with schema-related API endpoints.
 * Extends BaseService with schema-specific methods.
 */

import { BaseService } from './baseService';

/**
 * Schema service implementation
 */
export class SchemaService extends BaseService {
  /**
   * Create a new schema service instance
   * @param {Object} options - Service options
   */
  constructor(options = {}) {
    super('schemas', options);
  }

  /**
   * Get all schemas with optional filtering and pagination
   * @param {Object} params - Query parameters
   * @param {number} [params.skip] - Number of items to skip
   * @param {number} [params.limit] - Maximum number of items to return
   * @param {string} [params.repository_id] - Filter by repository ID
   * @param {string} [params.format_id] - Filter by format ID
   * @param {string} [params.sort] - Field to sort by
   * @param {string} [params.order] - Sort order ('asc' or 'desc')
   * @param {Object} options - Request options
   * @returns {Promise<Array>} Array of schemas
   */
  async getAll(params = {}, options = {}) {
    return this.cachedGet('', params, options);
  }

  /**
   * Get a schema by ID
   * @param {string} id - Schema ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Schema object
   */
  async getById(id, options = {}) {
    return this.cachedGet(`/${id}`, {}, options);
  }

  /**
   * Get schemas by repository ID
   * @param {string} repositoryId - Repository ID
   * @param {Object} params - Query parameters
   * @param {Object} options - Request options
   * @returns {Promise<Array>} Array of schemas
   */
  async getByRepository(repositoryId, params = {}, options = {}) {
    return this.cachedGet(`/repository/${repositoryId}`, params, options);
  }

  /**
   * Get relationships for a schema
   * @param {string} id - Schema ID
   * @param {Object} params - Query parameters
   * @param {Object} options - Request options
   * @returns {Promise<Array>} Array of relationships
   */
  async getRelationships(id, params = {}, options = {}) {
    return this.cachedGet(`/${id}/relationships`, params, options);
  }

  /**
   * Create a new schema
   * @param {Object} data - Schema data
   * @param {string} data.name - Schema name
   * @param {string} data.description - Schema description
   * @param {string} data.repository_id - Repository ID
   * @param {string} data.format_id - Format ID
   * @param {string} data.file_path - File path within repository
   * @param {Object} data.content - Schema content
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Created schema
   */
  async create(data, options = {}) {
    return this.executePost('', data, options);
  }

  /**
   * Update an existing schema
   * @param {string} id - Schema ID
   * @param {Object} data - Schema data to update
   * @param {string} [data.name] - Schema name
   * @param {string} [data.description] - Schema description
   * @param {Object} [data.content] - Schema content
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Updated schema
   */
  async update(id, data, options = {}) {
    return this.executePut(`/${id}`, data, options);
  }

  /**
   * Validate a schema against its format rules
   * @param {string} id - Schema ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Validation result
   */
  async validate(id, options = {}) {
    return this.executePost(`/${id}/validate`, {}, options);
  }

  /**
   * Export a schema in a specific format
   * @param {string} id - Schema ID
   * @param {string} format - Export format (e.g., 'json', 'yaml', 'xml')
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Exported schema
   */
  async export(id, format = 'json', options = {}) {
    return this.cachedGet(`/${id}/export`, { format }, options);
  }

  /**
   * Search schemas by name, description, or content
   * @param {string} query - Search query
   * @param {Object} params - Additional query parameters
   * @param {Object} options - Request options
   * @returns {Promise<Array>} Array of matching schemas
   */
  async search(query, params = {}, options = {}) {
    return this.cachedGet('/search', { 
      query,
      ...params
    }, options);
  }

  /**
   * Compare two schemas to identify differences
   * @param {string} sourceId - Source schema ID
   * @param {string} targetId - Target schema ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Comparison result
   */
  async compare(sourceId, targetId, options = {}) {
    return this.cachedGet(`/compare/${sourceId}/${targetId}`, {}, options);
  }

  /**
   * Get schema metadata and statistics
   * @param {string} id - Schema ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Schema metadata
   */
  async getMetadata(id, options = {}) {
    return this.cachedGet(`/${id}/metadata`, {}, options);
  }
}

export default SchemaService;
