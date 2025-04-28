/**
 * Mock Repository Service
 * 
 * Mock implementation of the repository service for development and testing.
 * Uses mock data instead of making actual API calls.
 */

import mockData from './mockData';
const { repositories, schemas, withDelay, withRandomFailure, filterData, generateId, pastDate } = mockData;

/**
 * Mock repository service implementation
 */
export class MockRepositoryService {
  /**
   * Create a new mock repository service
   * @param {Object} options - Configuration options
   */
  constructor(options = {}) {
    this.options = {
      failureRate: 0,
      minDelay: 50,
      maxDelay: 300,
      ...options
    };
    
    // Create a local copy of repositories to manipulate
    this.repositories = [...repositories];
  }
  
  /**
   * Configure mock service behavior
   * @param {Object} options - Configuration options
   * @param {number} [options.failureRate] - Rate of random failures (0-1)
   * @param {number} [options.minDelay] - Minimum response delay in ms
   * @param {number} [options.maxDelay] - Maximum response delay in ms
   */
  configure(options = {}) {
    this.options = {
      ...this.options,
      ...options
    };
  }
  
  /**
   * Process the request with configured delay and failure rate
   * @param {*} data - Data to return
   * @returns {Promise} Promise resolving to the data or rejecting with error
   */
  async processRequest(data) {
    // Apply configured delay
    const delayedData = await withDelay(
      data, 
      this.options.minDelay, 
      this.options.maxDelay
    );
    
    // Apply configured failure rate
    return withRandomFailure(
      delayedData, 
      this.options.failureRate
    );
  }
  
  /**
   * Get all repositories with optional filtering and pagination
   * @param {Object} params - Query parameters
   * @param {Object} options - Request options
   * @returns {Promise<Array>} Array of repositories
   */
  async getAll(params = {}, options = {}) {
    const filteredData = filterData(this.repositories, params);
    return this.processRequest(filteredData);
  }
  
  /**
   * Get a repository by ID
   * @param {string} id - Repository ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Repository object
   */
  async getById(id, options = {}) {
    const repository = this.repositories.find(repo => repo.id === id);
    
    if (!repository) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Repository with ID ${id} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    return this.processRequest(repository);
  }
  
  /**
   * Create a new repository
   * @param {Object} data - Repository data
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Created repository
   */
  async create(data, options = {}) {
    const newRepository = {
      id: generateId('repo'),
      ...data,
      status: data.status || 'pending',
      progress: data.progress || 0,
      created_at: pastDate(0),
      updated_at: pastDate(0)
    };
    
    this.repositories.push(newRepository);
    
    return this.processRequest(newRepository);
  }
  
  /**
   * Update an existing repository
   * @param {string} id - Repository ID
   * @param {Object} data - Repository data to update
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Updated repository
   */
  async update(id, data, options = {}) {
    const index = this.repositories.findIndex(repo => repo.id === id);
    
    if (index === -1) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Repository with ID ${id} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    const updatedRepository = {
      ...this.repositories[index],
      ...data,
      updated_at: pastDate(0)
    };
    
    this.repositories[index] = updatedRepository;
    
    return this.processRequest(updatedRepository);
  }
  
  /**
   * Delete a repository
   * @param {string} id - Repository ID
   * @param {Object} options - Request options
   * @returns {Promise<boolean>} Success indicator
   */
  async delete(id, options = {}) {
    const index = this.repositories.findIndex(repo => repo.id === id);
    
    if (index === -1) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Repository with ID ${id} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    this.repositories.splice(index, 1);
    
    return this.processRequest({ success: true });
  }
  
  /**
   * Trigger an analysis process for a repository
   * @param {string} id - Repository ID
   * @param {Object} analysisOptions - Analysis options
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Analysis result
   */
  async triggerAnalysis(id, analysisOptions = {}, options = {}) {
    const repository = this.repositories.find(repo => repo.id === id);
    
    if (!repository) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Repository with ID ${id} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    const analysisId = generateId('analysis');
    
    return this.processRequest({
      id: analysisId,
      repository_id: id,
      status: 'in_progress',
      progress: 0,
      options: analysisOptions,
      created_at: pastDate(0)
    });
  }
  
  /**
   * Get analysis status for a repository
   * @param {string} id - Repository ID
   * @param {string} analysisId - Analysis ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Analysis status
   */
  async getAnalysisStatus(id, analysisId, options = {}) {
    const repository = this.repositories.find(repo => repo.id === id);
    
    if (!repository) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Repository with ID ${id} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    // Simulate progress increasing over time
    const secondsSinceCreation = Math.floor((Date.now() - new Date(repository.created_at).getTime()) / 1000);
    const progress = Math.min(100, secondsSinceCreation % 100);
    
    return this.processRequest({
      id: analysisId,
      repository_id: id,
      status: progress < 100 ? 'in_progress' : 'completed',
      progress,
      created_at: pastDate(0),
      updated_at: pastDate(0)
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
    const repository = this.repositories.find(repo => repo.id === id);
    
    if (!repository) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Repository with ID ${id} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    const repositorySchemas = schemas.filter(schema => schema.repository_id === id);
    const filteredSchemas = filterData(repositorySchemas, params);
    
    return this.processRequest(filteredSchemas);
  }
  
  /**
   * Search repositories by name or description
   * @param {string} query - Search query
   * @param {Object} params - Additional query parameters
   * @param {Object} options - Request options
   * @returns {Promise<Array>} Array of matching repositories
   */
  async search(query, params = {}, options = {}) {
    const searchParams = {
      ...params,
      query
    };
    
    const searchResults = filterData(this.repositories, searchParams);
    
    return this.processRequest(searchResults);
  }
  
  /**
   * Get repository statistics
   * @param {string} id - Repository ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Repository statistics
   */
  async getStats(id, options = {}) {
    const repository = this.repositories.find(repo => repo.id === id);
    
    if (!repository) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Repository with ID ${id} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    const repositorySchemas = schemas.filter(schema => schema.repository_id === id);
    
    return this.processRequest({
      schema_count: repositorySchemas.length,
      format_distribution: [
        { format: 'JSON Schema', count: repositorySchemas.filter(s => s.format_id === 'format-1').length },
        { format: 'SQL', count: repositorySchemas.filter(s => s.format_id === 'format-2').length },
        { format: 'XML Schema', count: repositorySchemas.filter(s => s.format_id === 'format-3').length },
        { format: 'Avro Schema', count: repositorySchemas.filter(s => s.format_id === 'format-4').length }
      ],
      relationship_count: 5,
      last_activity: repository.updated_at
    });
  }
}

export default MockRepositoryService;
