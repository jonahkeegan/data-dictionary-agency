/**
 * Repository Service
 * Handles API requests related to repositories
 */
import { apiClient } from './client';
import { generateRequestKey, createCancelToken } from './cancelToken';

/**
 * Service for repository-related API operations
 */
export const RepositoryService = {
  /**
   * Get all repositories with optional filtering
   * @param {Object} params - Query parameters for filtering
   * @param {Object} options - Additional options for the request
   * @returns {Promise<Array>} Array of repositories
   */
  getAll: async (params = {}, options = {}) => {
    const requestKey = generateRequestKey('getRepositories', [params]);
    
    // If no cancel token provided, create one
    if (!options.cancelToken) {
      const source = createCancelToken(requestKey);
      options.cancelToken = source.token;
    }
    
    const response = await apiClient.get('/repositories', { 
      params,
      ...options 
    });
    
    return response.data;
  },
  
  /**
   * Get a repository by ID
   * @param {string} id - Repository ID
   * @param {Object} options - Additional options for the request
   * @returns {Promise<Object>} Repository details
   */
  getById: async (id, options = {}) => {
    const requestKey = generateRequestKey('getRepositoryById', [id]);
    
    // If no cancel token provided, create one
    if (!options.cancelToken) {
      const source = createCancelToken(requestKey);
      options.cancelToken = source.token;
    }
    
    const response = await apiClient.get(`/repositories/${id}`, options);
    
    return response.data;
  },
  
  /**
   * Create a new repository
   * @param {Object} data - Repository data
   * @param {Object} options - Additional options for the request
   * @returns {Promise<Object>} Created repository
   */
  create: async (data, options = {}) => {
    const requestKey = generateRequestKey('createRepository', [data]);
    
    // If no cancel token provided, create one
    if (!options.cancelToken) {
      const source = createCancelToken(requestKey);
      options.cancelToken = source.token;
    }
    
    const response = await apiClient.post('/repositories', data, options);
    
    return response.data;
  },
  
  /**
   * Update a repository
   * @param {string} id - Repository ID
   * @param {Object} data - Repository data to update
   * @param {Object} options - Additional options for the request
   * @returns {Promise<Object>} Updated repository
   */
  update: async (id, data, options = {}) => {
    const requestKey = generateRequestKey('updateRepository', [id, data]);
    
    // If no cancel token provided, create one
    if (!options.cancelToken) {
      const source = createCancelToken(requestKey);
      options.cancelToken = source.token;
    }
    
    const response = await apiClient.put(`/repositories/${id}`, data, options);
    
    return response.data;
  },
  
  /**
   * Delete a repository
   * @param {string} id - Repository ID
   * @param {Object} options - Additional options for the request
   * @returns {Promise<boolean>} Success status
   */
  delete: async (id, options = {}) => {
    const requestKey = generateRequestKey('deleteRepository', [id]);
    
    // If no cancel token provided, create one
    if (!options.cancelToken) {
      const source = createCancelToken(requestKey);
      options.cancelToken = source.token;
    }
    
    await apiClient.delete(`/repositories/${id}`, options);
    
    return true;
  },
  
  /**
   * Trigger analysis for a repository
   * @param {string} id - Repository ID
   * @param {Object} options - Additional options for the request
   * @returns {Promise<Object>} Analysis status
   */
  triggerAnalysis: async (id, options = {}) => {
    const requestKey = generateRequestKey('triggerRepositoryAnalysis', [id]);
    
    // If no cancel token provided, create one
    if (!options.cancelToken) {
      const source = createCancelToken(requestKey);
      options.cancelToken = source.token;
    }
    
    const response = await apiClient.post(`/repositories/${id}/analyze`, null, options);
    
    return response.data;
  },
  
  /**
   * Get analysis status for a repository
   * @param {string} id - Repository ID
   * @param {Object} options - Additional options for the request
   * @returns {Promise<Object>} Analysis status
   */
  getAnalysisStatus: async (id, options = {}) => {
    const requestKey = generateRequestKey('getRepositoryAnalysisStatus', [id]);
    
    // If no cancel token provided, create one
    if (!options.cancelToken) {
      const source = createCancelToken(requestKey);
      options.cancelToken = source.token;
    }
    
    const response = await apiClient.get(`/repositories/${id}/analyze/status`, options);
    
    return response.data;
  }
};
