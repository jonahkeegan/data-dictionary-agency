/**
 * Mock Schema Service
 * 
 * Mock implementation of the schema service for development and testing.
 * Uses mock data instead of making actual API calls.
 */

import mockData from './mockData';
const { schemas, relationships, formats, withDelay, withRandomFailure, filterData, generateId, pastDate } = mockData;

/**
 * Mock schema service implementation
 */
export class MockSchemaService {
  /**
   * Create a new mock schema service
   * @param {Object} options - Configuration options
   */
  constructor(options = {}) {
    this.options = {
      failureRate: 0,
      minDelay: 50,
      maxDelay: 300,
      ...options
    };
    
    // Create a local copy of schemas to manipulate
    this.schemas = [...schemas];
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
   * Get all schemas with optional filtering and pagination
   * @param {Object} params - Query parameters
   * @param {Object} options - Request options
   * @returns {Promise<Array>} Array of schemas
   */
  async getAll(params = {}, options = {}) {
    const filteredData = filterData(this.schemas, params);
    return this.processRequest(filteredData);
  }
  
  /**
   * Get a schema by ID
   * @param {string} id - Schema ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Schema object
   */
  async getById(id, options = {}) {
    const schema = this.schemas.find(schema => schema.id === id);
    
    if (!schema) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Schema with ID ${id} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    return this.processRequest(schema);
  }
  
  /**
   * Get schemas by repository ID
   * @param {string} repositoryId - Repository ID
   * @param {Object} params - Query parameters
   * @param {Object} options - Request options
   * @returns {Promise<Array>} Array of schemas
   */
  async getByRepository(repositoryId, params = {}, options = {}) {
    const repositorySchemas = this.schemas.filter(schema => schema.repository_id === repositoryId);
    const filteredSchemas = filterData(repositorySchemas, params);
    
    return this.processRequest(filteredSchemas);
  }
  
  /**
   * Get relationships for a schema
   * @param {string} id - Schema ID
   * @param {Object} params - Query parameters
   * @param {Object} options - Request options
   * @returns {Promise<Array>} Array of relationships
   */
  async getRelationships(id, params = {}, options = {}) {
    const schema = this.schemas.find(schema => schema.id === id);
    
    if (!schema) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Schema with ID ${id} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    // Get relationships where this schema is the source or target
    const schemaRelationships = relationships.filter(
      rel => rel.source_schema_id === id || rel.target_schema_id === id
    );
    
    const filteredRelationships = filterData(schemaRelationships, params);
    
    return this.processRequest(filteredRelationships);
  }
  
  /**
   * Create a new schema
   * @param {Object} data - Schema data
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Created schema
   */
  async create(data, options = {}) {
    const format = formats.find(f => f.id === data.format_id);
    
    // Generate a schema ID
    const newSchema = {
      id: generateId('schema'),
      format_name: format ? format.name : 'Unknown Format',
      created_at: pastDate(0),
      updated_at: pastDate(0),
      ...data
    };
    
    this.schemas.push(newSchema);
    
    return this.processRequest(newSchema);
  }
  
  /**
   * Update an existing schema
   * @param {string} id - Schema ID
   * @param {Object} data - Schema data to update
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Updated schema
   */
  async update(id, data, options = {}) {
    const index = this.schemas.findIndex(schema => schema.id === id);
    
    if (index === -1) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Schema with ID ${id} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    // If updating format_id, also update format_name
    let formatName = this.schemas[index].format_name;
    if (data.format_id) {
      const format = formats.find(f => f.id === data.format_id);
      formatName = format ? format.name : 'Unknown Format';
    }
    
    const updatedSchema = {
      ...this.schemas[index],
      ...data,
      format_name: formatName,
      updated_at: pastDate(0)
    };
    
    this.schemas[index] = updatedSchema;
    
    return this.processRequest(updatedSchema);
  }
  
  /**
   * Validate a schema against its format rules
   * @param {string} id - Schema ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Validation result
   */
  async validate(id, options = {}) {
    const schema = this.schemas.find(schema => schema.id === id);
    
    if (!schema) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Schema with ID ${id} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    // Simulate validation results
    // In this mock, we'll randomly generate validation errors
    const valid = Math.random() > 0.3; // 70% chance of being valid
    
    const validationResult = {
      valid,
      schema_id: id,
      format: schema.format_name,
      errors: valid ? [] : [
        {
          path: '/properties/example',
          message: 'Property example is required',
          severity: 'error'
        }
      ]
    };
    
    return this.processRequest(validationResult);
  }
  
  /**
   * Export a schema in a specific format
   * @param {string} id - Schema ID
   * @param {string} format - Export format (e.g., 'json', 'yaml', 'xml')
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Exported schema
   */
  async export(id, format = 'json', options = {}) {
    const schema = this.schemas.find(schema => schema.id === id);
    
    if (!schema) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Schema with ID ${id} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    let exportedContent = schema.content;
    
    // Convert to the requested format (simple mock implementation)
    if (format === 'yaml' && typeof schema.content === 'object') {
      exportedContent = "type: object\nproperties:\n  id:\n    type: string";
    } else if (format === 'xml' && typeof schema.content === 'object') {
      exportedContent = '<?xml version="1.0"?><xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"></xs:schema>';
    }
    
    return this.processRequest({
      format,
      content: exportedContent,
      schema_id: schema.id,
      schema_name: schema.name
    });
  }
  
  /**
   * Search schemas by name, description, or content
   * @param {string} query - Search query
   * @param {Object} params - Additional query parameters
   * @param {Object} options - Request options
   * @returns {Promise<Array>} Array of matching schemas
   */
  async search(query, params = {}, options = {}) {
    const searchParams = {
      ...params,
      query
    };
    
    const searchResults = filterData(this.schemas, searchParams);
    
    return this.processRequest(searchResults);
  }
  
  /**
   * Compare two schemas to identify differences
   * @param {string} sourceId - Source schema ID
   * @param {string} targetId - Target schema ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Comparison result
   */
  async compare(sourceId, targetId, options = {}) {
    const sourceSchema = this.schemas.find(schema => schema.id === sourceId);
    const targetSchema = this.schemas.find(schema => schema.id === targetId);
    
    if (!sourceSchema) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Source schema with ID ${sourceId} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    if (!targetSchema) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Target schema with ID ${targetId} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    // Mock comparison result
    return this.processRequest({
      source_id: sourceId,
      target_id: targetId,
      source_name: sourceSchema.name,
      target_name: targetSchema.name,
      similarity_score: 0.75,
      differences: [
        {
          path: '/properties/name',
          source_value: { type: 'string' },
          target_value: { type: 'string', maxLength: 100 },
          difference_type: 'constraint_added'
        },
        {
          path: '/required',
          source_value: ['id', 'name'],
          target_value: ['id', 'name', 'created_at'],
          difference_type: 'array_item_added'
        }
      ],
      added_properties: [
        '/properties/created_at'
      ],
      removed_properties: [
        '/properties/legacy_id'
      ],
      modified_properties: [
        '/properties/name'
      ]
    });
  }
  
  /**
   * Get schema metadata and statistics
   * @param {string} id - Schema ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Schema metadata
   */
  async getMetadata(id, options = {}) {
    const schema = this.schemas.find(schema => schema.id === id);
    
    if (!schema) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Schema with ID ${id} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    // Find relationships
    const relatedRelationships = relationships.filter(
      rel => rel.source_schema_id === id || rel.target_schema_id === id
    );
    
    // Mock schema metadata
    return this.processRequest({
      id: schema.id,
      name: schema.name,
      repository_id: schema.repository_id,
      format_id: schema.format_id,
      format_name: schema.format_name,
      created_at: schema.created_at,
      updated_at: schema.updated_at,
      statistics: {
        property_count: 15,
        required_property_count: 5,
        depth: 3,
        relationship_count: relatedRelationships.length,
        type_distribution: [
          { type: 'string', count: 8 },
          { type: 'number', count: 3 },
          { type: 'boolean', count: 2 },
          { type: 'object', count: 2 }
        ]
      }
    });
  }
}

export default MockSchemaService;
