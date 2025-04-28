/**
 * Repository Service
 * 
 * Service for interacting with repository-related API endpoints.
 * Extends BaseService with repository-specific methods.
 */

import { BaseService } from './baseService';

/**
 * Repository service implementation
 */
export class RepositoryService extends BaseService {
  /**
   * Create a new repository service instance
   * @param {Object} options - Service options
   */
  constructor(options = {}) {
    super('repositories', options);
  }

  /**
   * Get all repositories with optional filtering and pagination
   * @param {Object} params - Query parameters
   * @param {number} [params.skip] - Number of items to skip
   * @param {number} [params.limit] - Maximum number of items to return
   * @param {string} [params.sort] - Field to sort by
   * @param {string} [params.order] - Sort order ('asc' or 'desc')
   * @param {string} [params.status] - Filter by repository status
   * @param {Object} options - Request options
   * @returns {Promise<Array>} Array of repositories
   */
  async getAll(params = {}, options = {}) {
    return this.cachedGet('', params, options);
  }

  /**
   * Get a repository by ID
   * @param {string} id - Repository ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Repository object
   */
  async getById(id, options = {}) {
    return this.cachedGet(`/${id}`, {}, options);
  }

  /**
   * Create a new repository
   * @param {Object} data - Repository data
   * @param {string} data.name - Repository name
   * @param {string} data.description - Repository description
   * @param {string} data.url - Repository URL
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Created repository
   */
  async create(data, options = {}) {
    return this.executePost('', data, options);
  }

  /**
   * Update an existing repository
   * @param {string} id - Repository ID
   * @param {Object} data - Repository data to update
   * @param {string} [data.name] - Repository name
   * @param {string} [data.description] - Repository description
   * @param {string} [data.url] - Repository URL
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Updated repository
   */
  async update(id, data, options = {}) {
    return this.executePut(`/${id}`, data, options);
  }

  /**
   * Delete a repository
   * @param {string} id - Repository ID
   * @param {Object} options - Request options
   * @returns {Promise<boolean>} Success indicator
   */
  async delete(id, options = {}) {
    return this.executeDelete(`/${id}`, options);
  }

  /**
   * Trigger an analysis process for a repository
   * @param {string} id - Repository ID
   * @param {Object} analysisOptions - Analysis options
   * @param {boolean} [analysisOptions.deep] - Perform deep analysis
   * @param {Array<string>} [analysisOptions.include_branches] - Branches to include
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Analysis result
   */
  async triggerAnalysis(id, analysisOptions = {}, options = {}) {
    return this.executePost(`/${id}/analyze`, { options: analysisOptions }, options);
  }

  /**
   * Get analysis status for a repository
   * @param {string} id - Repository ID
   * @param {string} analysisId - Analysis ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Analysis status
   */
  async getAnalysisStatus(id, analysisId, options = {}) {
    return this.cachedGet(`/${id}/analyze/${analysisId}`, {}, {
      ...options,
      cacheTTL: 5000 // Short TTL for status checks
    });
  }

  /**
   * Get schemas associated with a repository
   * @param {string} id - Repository ID
   * @param {Object} params - Query parameters
   * @param {Object} options - Request options
   * @returns {Promise<Array>} Array of schemas
   */
  async getSchemas(id, params = {}, options = {}) {
    return this.cachedGet(`/${id}/schemas`, params, options);
  }

  /**
   * Search repositories by name or description
   * @param {string} query - Search query
   * @param {Object} params - Additional query parameters
   * @param {Object} options - Request options
   * @returns {Promise<Array>} Array of matching repositories
   */
  async search(query, params = {}, options = {}) {
    return this.cachedGet('/search', { 
      query,
      ...params
    }, options);
  }

  /**
   * Get repository statistics
   * @param {string} id - Repository ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Repository statistics
   */
  async getStats(id, options = {}) {
    return this.cachedGet(`/${id}/stats`, {}, options);
  }
}

export default RepositoryService;
