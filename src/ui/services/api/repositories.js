/**
 * Repository service for the Data Dictionary Agency frontend
 * Provides methods for interacting with repository-related API endpoints
 */
import BaseService from './baseService';
import { createCancelToken, generateRequestKey } from './cancelToken';

/**
 * @typedef {import('./baseService').ServiceOptions} ServiceOptions
 */

/**
 * @typedef {Object} Repository
 * @property {string} id - Repository ID
 * @property {string} name - Repository name
 * @property {string} description - Repository description
 * @property {string} url - Repository URL
 * @property {string} status - Repository status
 * @property {number} progress - Analysis progress (0-100)
 * @property {string} created_at - ISO 8601 creation timestamp
 * @property {string} updated_at - ISO 8601 update timestamp
 */

/**
 * @typedef {Object} RepositoryParams
 * @property {number} [skip=0] - Number of items to skip
 * @property {number} [limit=100] - Max number of items to return
 * @property {string} [sort] - Field to sort by
 * @property {string} [order] - Sort order ('asc' or 'desc')
 */

/**
 * @typedef {Object} RepositoryData
 * @property {string} name - Repository name
 * @property {string} description - Repository description
 * @property {string} url - Repository URL
 */

/**
 * @typedef {Object} AnalysisResult
 * @property {string} id - Analysis job ID
 * @property {string} status - Analysis status
 * @property {number} progress - Analysis progress (0-100)
 */

/**
 * Repository service implementation
 * @extends BaseService
 */
export class RepositoryService extends BaseService {
  /**
   * Get all repositories with optional filtering and pagination
   * 
   * @async
   * @param {RepositoryParams} [params={}] - Query parameters
   * @param {ServiceOptions} [options={}] - Request options
   * @returns {Promise<Repository[]>} Array of repository objects
   * @throws {Error} If the request fails
   */
  async getAll(params = {}, options = {}) {
    // Create cancel token if not provided
    this.setupCancelToken(options, 'getRepositories', [params]);
    
    try {
      // Use cached request
      return await this.cachedGet('/repositories', params, options);
    } catch (error) {
      return this.handleError(error);
    }
  }
  
  /**
   * Get a repository by ID
   * 
   * @async
   * @param {string} id - Repository ID
   * @param {ServiceOptions} [options={}] - Request options
   * @returns {Promise<Repository>} Repository object
   * @throws {Error} If the request fails
   */
  async getById(id, options = {}) {
    // Create cancel token if not provided
    this.setupCancelToken(options, 'getRepositoryById', [id]);
    
    try {
      // Use cached request
      return await this.cachedGet(`/repositories/${id}`, {}, options);
    } catch (error) {
      return this.handleError(error);
    }
  }
  
  /**
   * Create a new repository
   * 
   * @async
   * @param {RepositoryData} data - Repository data
   * @param {ServiceOptions} [options={}] - Request options
   * @returns {Promise<Repository>} Created repository object
   * @throws {Error} If the request fails
   */
  async create(data, options = {}) {
    // Create cancel token if not provided
    this.setupCancelToken(options, 'createRepository', [data]);
    
    // Execute POST with cache invalidation
    return this.executePost(
      '/repositories', 
      data, 
      options, 
      '^repositories($|\\?)'
    );
  }
  
  /**
   * Delete a repository by ID
   * 
   * @async
   * @param {string} id - Repository ID
   * @param {ServiceOptions} [options={}] - Request options
   * @returns {Promise<boolean>} True if deletion was successful
   * @throws {Error} If the request fails
   */
  async delete(id, options = {}) {
    // Create cancel token if not provided
    this.setupCancelToken(options, 'deleteRepository', [id]);
    
    // Create invalidation patterns
    const patterns = [
      '^repositories($|\\?)', // List endpoint
      `^repositories/${id}($|\\?)` // Specific repository
    ];
    
    try {
      await this.executeDelete(`/repositories/${id}`, options);
      
      // Invalidate cache for both patterns
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
   * Trigger analysis for a repository
   * 
   * @async
   * @param {string} id - Repository ID
   * @param {ServiceOptions} [options={}] - Request options
   * @returns {Promise<AnalysisResult>} Analysis result
   * @throws {Error} If the request fails
   */
  async triggerAnalysis(id, options = {}) {
    // Create cancel token if not provided
    this.setupCancelToken(options, 'triggerRepositoryAnalysis', [id]);
    
    // Invalidate repository data when triggering analysis
    return this.executePost(
      `/repositories/${id}/analyze`, 
      null, 
      options, 
      `^repositories/${id}($|\\?)`
    );
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
