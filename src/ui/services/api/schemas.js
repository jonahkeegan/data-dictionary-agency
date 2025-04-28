/**
 * Schema Service
 * Handles API requests related to schemas
 */
import { apiClient } from './client';
import { generateRequestKey, createCancelToken } from './cancelToken';

/**
 * Service for schema-related API operations
 */
export const SchemaService = {
  /**
   * Get all schemas with optional filtering
   * @param {Object} params - Query parameters for filtering
   * @param {Object} options - Additional options for the request
   * @returns {Promise<Array>} Array of schemas
   */
  getAll: async (params = {}, options = {}) => {
    const requestKey = generateRequestKey('getSchemas', [params]);
    
    // If no cancel token provided, create one
    if (!options.cancelToken) {
      const source = createCancelToken(requestKey);
      options.cancelToken = source.token;
    }
    
    const response = await apiClient.get('/schemas', { 
      params,
      ...options 
    });
    
    return response.data;
  },
  
  /**
   * Get a schema by ID
   * @param {string} id - Schema ID
   * @param {Object} options - Additional options for the request
   * @returns {Promise<Object>} Schema details
   */
  getById: async (id, options = {}) => {
    const requestKey = generateRequestKey('getSchemaById', [id]);
    
    // If no cancel token provided, create one
    if (!options.cancelToken) {
      const source = createCancelToken(requestKey);
      options.cancelToken = source.token;
    }
    
    const response = await apiClient.get(`/schemas/${id}`, options);
    
    return response.data;
  },
  
  /**
   * Get schemas for a repository
   * @param {string} repositoryId - Repository ID
   * @param {Object} params - Query parameters for filtering
   * @param {Object} options - Additional options for the request
   * @returns {Promise<Array>} Array of schemas
   */
  getByRepository: async (repositoryId, params = {}, options = {}) => {
    const requestKey = generateRequestKey('getSchemasByRepository', [repositoryId, params]);
    
    // If no cancel token provided, create one
    if (!options.cancelToken) {
      const source = createCancelToken(requestKey);
      options.cancelToken = source.token;
    }
    
    const response = await apiClient.get(`/repositories/${repositoryId}/schemas`, {
      params,
      ...options
    });
    
    return response.data;
  },
  
  /**
   * Get relationships for a schema
   * @param {string} id - Schema ID
   * @param {Object} params - Query parameters for filtering
   * @param {Object} options - Additional options for the request
   * @returns {Promise<Array>} Array of relationships
   */
  getRelationships: async (id, params = {}, options = {}) => {
    const requestKey = generateRequestKey('getSchemaRelationships', [id, params]);
    
    // If no cancel token provided, create one
    if (!options.cancelToken) {
      const source = createCancelToken(requestKey);
      options.cancelToken = source.token;
    }
    
    const response = await apiClient.get(`/schemas/${id}/relationships`, {
      params,
      ...options
    });
    
    return response.data;
  },
  
  /**
   * Get fields for a schema
   * @param {string} id - Schema ID
   * @param {Object} params - Query parameters for filtering
   * @param {Object} options - Additional options for the request
   * @returns {Promise<Array>} Array of fields
   */
  getFields: async (id, params = {}, options = {}) => {
    const requestKey = generateRequestKey('getSchemaFields', [id, params]);
    
    // If no cancel token provided, create one
    if (!options.cancelToken) {
      const source = createCancelToken(requestKey);
      options.cancelToken = source.token;
    }
    
    const response = await apiClient.get(`/schemas/${id}/fields`, {
      params,
      ...options
    });
    
    return response.data;
  },
  
  /**
   * Update a schema
   * @param {string} id - Schema ID
   * @param {Object} data - Schema data to update
   * @param {Object} options - Additional options for the request
   * @returns {Promise<Object>} Updated schema
   */
  update: async (id, data, options = {}) => {
    const requestKey = generateRequestKey('updateSchema', [id, data]);
    
    // If no cancel token provided, create one
    if (!options.cancelToken) {
      const source = createCancelToken(requestKey);
      options.cancelToken = source.token;
    }
    
    const response = await apiClient.put(`/schemas/${id}`, data, options);
    
    return response.data;
  },
  
  /**
   * Delete a schema
   * @param {string} id - Schema ID
   * @param {Object} options - Additional options for the request
   * @returns {Promise<boolean>} Success status
   */
  delete: async (id, options = {}) => {
    const requestKey = generateRequestKey('deleteSchema', [id]);
    
    // If no cancel token provided, create one
    if (!options.cancelToken) {
      const source = createCancelToken(requestKey);
      options.cancelToken = source.token;
    }
    
    await apiClient.delete(`/schemas/${id}`, options);
    
    return true;
  }
};
