/**
 * Format Service
 * 
 * Service for interacting with format-related API endpoints.
 * Extends BaseService with format-specific methods.
 */

import { BaseService } from './baseService';

/**
 * Format service implementation
 */
export class FormatService extends BaseService {
  /**
   * Create a new format service instance
   * @param {Object} options - Service options
   */
  constructor(options = {}) {
    super('formats', options);
  }

  /**
   * Get all formats with optional filtering and pagination
   * @param {Object} params - Query parameters
   * @param {number} [params.skip] - Number of items to skip
   * @param {number} [params.limit] - Maximum number of items to return
   * @param {string} [params.sort] - Field to sort by
   * @param {string} [params.order] - Sort order ('asc' or 'desc')
   * @param {Object} options - Request options
   * @returns {Promise<Array>} Array of formats
   */
  async getAll(params = {}, options = {}) {
    return this.cachedGet('', params, options);
  }

  /**
   * Get a format by ID
   * @param {string} id - Format ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Format object
   */
  async getById(id, options = {}) {
    return this.cachedGet(`/${id}`, {}, options);
  }

  /**
   * Get list of supported format names
   * @param {Object} options - Request options
   * @returns {Promise<Array<string>>} Array of supported format names
   */
  async getSupportedFormats(options = {}) {
    return this.cachedGet('/supported', {}, options);
  }

  /**
   * Validate schema content against a specific format
   * @param {string} formatId - Format ID
   * @param {Object} schemaContent - Schema content to validate
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Validation result
   */
  async validateSchema(formatId, schemaContent, options = {}) {
    return this.executePost(`/${formatId}/validate`, schemaContent, options);
  }

  /**
   * Get detailed information about a format
   * @param {string} id - Format ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Format details
   */
  async getDetails(id, options = {}) {
    return this.cachedGet(`/${id}/details`, {}, options);
  }

  /**
   * Get example schema for a format
   * @param {string} id - Format ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Example schema
   */
  async getExample(id, options = {}) {
    return this.cachedGet(`/${id}/example`, {}, options);
  }

  /**
   * Detect format from schema content
   * @param {Object} content - Schema content
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Detected format information
   */
  async detectFormat(content, options = {}) {
    return this.executePost('/detect', { content }, options);
  }

  /**
   * Convert schema from one format to another
   * @param {string} sourceFormatId - Source format ID
   * @param {string} targetFormatId - Target format ID
   * @param {Object} schemaContent - Schema content to convert
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Converted schema
   */
  async convertSchema(sourceFormatId, targetFormatId, schemaContent, options = {}) {
    return this.executePost(`/convert/${sourceFormatId}/${targetFormatId}`, 
      { content: schemaContent }, 
      options
    );
  }

  /**
   * Get format compatibility information
   * @param {string} formatId - Format ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Compatibility information
   */
  async getCompatibility(formatId, options = {}) {
    return this.cachedGet(`/${formatId}/compatibility`, {}, options);
  }

  /**
   * Check if a format supports a specific feature
   * @param {string} formatId - Format ID
   * @param {string} featureId - Feature ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Feature support information
   */
  async supportsFeature(formatId, featureId, options = {}) {
    return this.cachedGet(`/${formatId}/features/${featureId}`, {}, options);
  }
}

export default FormatService;
