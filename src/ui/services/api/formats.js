/**
 * Format service for the Data Dictionary Agency frontend
 * Provides methods for interacting with format-related API endpoints
 */
import BaseService from './baseService';
import { createCancelToken, generateRequestKey } from './cancelToken';

/**
 * @typedef {import('./baseService').ServiceOptions} ServiceOptions
 */

/**
 * @typedef {Object} Format
 * @property {string} id - Format ID
 * @property {string} name - Format name
 * @property {string} description - Format description
 * @property {string} mime_type - MIME type
 * @property {string[]} file_extensions - File extensions
 * @property {string} created_at - ISO 8601 creation timestamp
 * @property {string} updated_at - ISO 8601 update timestamp
 * @property {number} schema_count - Number of schemas using this format
 * @property {string[]} detection_patterns - Regex patterns for detection
 * @property {string} example - Example content
 */

/**
 * @typedef {Object} FormatParams
 * @property {number} [skip=0] - Number of items to skip
 * @property {number} [limit=100] - Max number of items to return
 * @property {string} [sort] - Field to sort by
 * @property {string} [order] - Sort order ('asc' or 'desc')
 */

/**
 * @typedef {Object} ValidationResult
 * @property {boolean} valid - Whether the schema is valid
 * @property {Array<Object>} errors - Validation errors if any
 * @property {string} format - Format name
 */

/**
 * Format service implementation
 * @extends BaseService
 */
export class FormatService extends BaseService {
  /**
   * Get all formats with optional filtering and pagination
   * 
   * @async
   * @param {FormatParams} [params={}] - Query parameters
   * @param {ServiceOptions} [options={}] - Request options
   * @returns {Promise<Format[]>} Array of format objects
   * @throws {Error} If the request fails
   */
  async getAll(params = {}, options = {}) {
    // Create cancel token if not provided
    this.setupCancelToken(options, 'getFormats', [params]);
    
    try {
      // Use cached request with longer TTL for formats (30 min default)
      return await this.cachedGet('/formats', params, options);
    } catch (error) {
      return this.handleError(error);
    }
  }
  
  /**
   * Get a format by ID
   * 
   * @async
   * @param {string} id - Format ID
   * @param {ServiceOptions} [options={}] - Request options
   * @returns {Promise<Format>} Format object
   * @throws {Error} If the request fails
   */
  async getById(id, options = {}) {
    // Create cancel token if not provided
    this.setupCancelToken(options, 'getFormatById', [id]);
    
    try {
      // Use cached request
      return await this.cachedGet(`/formats/${id}`, {}, options);
    } catch (error) {
      return this.handleError(error);
    }
  }
  
  /**
   * Get list of supported formats
   * 
   * @async
   * @param {ServiceOptions} [options={}] - Request options
   * @returns {Promise<string[]>} Array of format strings
   * @throws {Error} If the request fails
   */
  async getSupportedFormats(options = {}) {
    // Create cancel token if not provided
    this.setupCancelToken(options, 'getSupportedFormats', []);
    
    try {
      // Use cached request with long TTL (formats rarely change)
      return await this.cachedGet('/formats/supported', {}, {
        ...options,
        ttl: 3600 // 1 hour TTL for supported formats list
      });
    } catch (error) {
      return this.handleError(error);
    }
  }
  
  /**
   * Validate schema against format
   * 
   * @async
   * @param {string} formatId - Format ID
   * @param {Object} schema - Schema to validate
   * @param {ServiceOptions} [options={}] - Request options
   * @returns {Promise<ValidationResult>} Validation result
   * @throws {Error} If the request fails
   */
  async validateSchema(formatId, schema, options = {}) {
    // Create cancel token if not provided
    this.setupCancelToken(options, 'validateSchema', [formatId, schema]);
    
    try {
      // Don't cache validation requests (always fresh)
      const response = await this.apiClient.post(
        `/formats/${formatId}/validate`, 
        schema,
        options
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
