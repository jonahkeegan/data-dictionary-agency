/**
 * Format Service
 * Handles API requests related to data formats
 */
import { apiClient } from './client';
import { generateRequestKey, createCancelToken } from './cancelToken';

/**
 * Service for format-related API operations
 */
export const FormatService = {
  /**
   * Get all supported formats
   * @param {Object} params - Query parameters for filtering
   * @param {Object} options - Additional options for the request
   * @returns {Promise<Array>} Array of supported formats
   */
  getAll: async (params = {}, options = {}) => {
    const requestKey = generateRequestKey('getFormats', [params]);
    
    // If no cancel token provided, create one
    if (!options.cancelToken) {
      const source = createCancelToken(requestKey);
      options.cancelToken = source.token;
    }
    
    const response = await apiClient.get('/formats', { 
      params,
      ...options 
    });
    
    return response.data;
  },
  
  /**
   * Get format details by ID or name
   * @param {string} idOrName - Format ID or name
   * @param {Object} options - Additional options for the request
   * @returns {Promise<Object>} Format details
   */
  getById: async (idOrName, options = {}) => {
    const requestKey = generateRequestKey('getFormatById', [idOrName]);
    
    // If no cancel token provided, create one
    if (!options.cancelToken) {
      const source = createCancelToken(requestKey);
      options.cancelToken = source.token;
    }
    
    const response = await apiClient.get(`/formats/${idOrName}`, options);
    
    return response.data;
  },
  
  /**
   * Detect format of provided content
   * @param {Object} data - Content data to analyze
   * @param {Object} options - Additional options for the request
   * @returns {Promise<Object>} Format detection results
   */
  detect: async (data, options = {}) => {
    const requestKey = generateRequestKey('detectFormat', [data]);
    
    // If no cancel token provided, create one
    if (!options.cancelToken) {
      const source = createCancelToken(requestKey);
      options.cancelToken = source.token;
    }
    
    const response = await apiClient.post('/formats/detect', data, options);
    
    return response.data;
  },
  
  /**
   * Get schemas by format
   * @param {string} formatId - Format ID
   * @param {Object} params - Query parameters for filtering
   * @param {Object} options - Additional options for the request
   * @returns {Promise<Array>} Array of schemas
   */
  getSchemas: async (formatId, params = {}, options = {}) => {
    const requestKey = generateRequestKey('getSchemasByFormat', [formatId, params]);
    
    // If no cancel token provided, create one
    if (!options.cancelToken) {
      const source = createCancelToken(requestKey);
      options.cancelToken = source.token;
    }
    
    const response = await apiClient.get(`/formats/${formatId}/schemas`, {
      params,
      ...options
    });
    
    return response.data;
  },
  
  /**
   * Get format capabilities
   * @param {string} formatId - Format ID
   * @param {Object} options - Additional options for the request
   * @returns {Promise<Object>} Format capabilities
   */
  getCapabilities: async (formatId, options = {}) => {
    const requestKey = generateRequestKey('getFormatCapabilities', [formatId]);
    
    // If no cancel token provided, create one
    if (!options.cancelToken) {
      const source = createCancelToken(requestKey);
      options.cancelToken = source.token;
    }
    
    const response = await apiClient.get(`/formats/${formatId}/capabilities`, options);
    
    return response.data;
  }
};
