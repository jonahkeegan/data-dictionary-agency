/**
 * Mock Format Service
 * 
 * Mock implementation of the format service for development and testing.
 * Uses mock data instead of making actual API calls.
 */

import mockData from './mockData';
const { formats, withDelay, withRandomFailure, filterData, generateId, pastDate } = mockData;

/**
 * Mock format service implementation
 */
export class MockFormatService {
  /**
   * Create a new mock format service
   * @param {Object} options - Configuration options
   */
  constructor(options = {}) {
    this.options = {
      failureRate: 0,
      minDelay: 50,
      maxDelay: 300,
      ...options
    };
    
    // Create a local copy of formats to manipulate
    this.formats = [...formats];
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
   * Get all formats with optional filtering and pagination
   * @param {Object} params - Query parameters
   * @param {Object} options - Request options
   * @returns {Promise<Array>} Array of formats
   */
  async getAll(params = {}, options = {}) {
    const filteredData = filterData(this.formats, params);
    return this.processRequest(filteredData);
  }
  
  /**
   * Get a format by ID
   * @param {string} id - Format ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Format object
   */
  async getById(id, options = {}) {
    const format = this.formats.find(format => format.id === id);
    
    if (!format) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Format with ID ${id} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    return this.processRequest(format);
  }
  
  /**
   * Get list of supported format names
   * @param {Object} options - Request options
   * @returns {Promise<Array<string>>} Array of supported format names
   */
  async getSupportedFormats(options = {}) {
    const formatNames = this.formats.map(format => format.name);
    return this.processRequest(formatNames);
  }
  
  /**
   * Validate schema content against a specific format
   * @param {string} formatId - Format ID
   * @param {Object} schemaContent - Schema content to validate
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Validation result
   */
  async validateSchema(formatId, schemaContent, options = {}) {
    const format = this.formats.find(format => format.id === formatId);
    
    if (!format) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Format with ID ${formatId} not found`,
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
      format: format.name,
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
   * Get detailed information about a format
   * @param {string} id - Format ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Format details
   */
  async getDetails(id, options = {}) {
    const format = this.formats.find(format => format.id === id);
    
    if (!format) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Format with ID ${id} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    // Add more detailed information about the format
    const formatDetails = {
      ...format,
      version: '1.0',
      specification_url: `https://example.com/specifications/${format.name.toLowerCase().replace(/\s+/g, '-')}`,
      data_types: [
        'string',
        'number',
        'boolean',
        'object',
        'array',
        'null'
      ],
      constraints: [
        'pattern',
        'minimum',
        'maximum',
        'required',
        'enum'
      ],
      supported_features: {
        inheritance: true,
        polymorphism: format.id === 'format-1' || format.id === 'format-7',
        circular_references: format.id === 'format-1' || format.id === 'format-7',
        union_types: format.id === 'format-1' || format.id === 'format-6'
      }
    };
    
    return this.processRequest(formatDetails);
  }
  
  /**
   * Get example schema for a format
   * @param {string} id - Format ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Example schema
   */
  async getExample(id, options = {}) {
    const format = this.formats.find(format => format.id === id);
    
    if (!format) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Format with ID ${id} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    return this.processRequest({
      format_id: id,
      format_name: format.name,
      example: format.example,
      comment: `This is an example of a simple ${format.name} schema`
    });
  }
  
  /**
   * Detect format from schema content
   * @param {Object} content - Schema content
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Detected format information
   */
  async detectFormat(content, options = {}) {
    // Simulate format detection
    let detectedFormat = null;
    let confidence = 0;
    
    // Simple mock detection based on detection patterns
    for (const format of this.formats) {
      if (format.detection_patterns && format.detection_patterns.length > 0) {
        // Convert content to string if it's an object
        const contentStr = typeof content === 'object' ? 
          JSON.stringify(content) : String(content);
        
        // Check if any pattern matches
        const matches = format.detection_patterns.some(pattern => {
          try {
            return new RegExp(pattern).test(contentStr);
          } catch (e) {
            return false;
          }
        });
        
        if (matches) {
          detectedFormat = format;
          confidence = 0.8 + Math.random() * 0.2; // 0.8-1.0
          break;
        }
      }
    }
    
    // If no format detected, pick one randomly with low confidence
    if (!detectedFormat) {
      detectedFormat = this.formats[Math.floor(Math.random() * this.formats.length)];
      confidence = 0.3 + Math.random() * 0.3; // 0.3-0.6
    }
    
    return this.processRequest({
      detected: true,
      format_id: detectedFormat.id,
      format_name: detectedFormat.name,
      confidence,
      alternative_formats: this.formats
        .filter(f => f.id !== detectedFormat.id)
        .slice(0, 2)
        .map(f => ({
          format_id: f.id,
          format_name: f.name,
          confidence: Math.random() * 0.4 // 0-0.4
        }))
    });
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
    const sourceFormat = this.formats.find(format => format.id === sourceFormatId);
    const targetFormat = this.formats.find(format => format.id === targetFormatId);
    
    if (!sourceFormat) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Source format with ID ${sourceFormatId} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    if (!targetFormat) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Target format with ID ${targetFormatId} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    // Mock conversion - just return the example of the target format
    return this.processRequest({
      source_format_id: sourceFormatId,
      source_format_name: sourceFormat.name,
      target_format_id: targetFormatId,
      target_format_name: targetFormat.name,
      converted_content: targetFormat.example,
      conversion_notes: [
        'Mock conversion completed',
        'Some features may not be fully converted'
      ],
      success: true
    });
  }
  
  /**
   * Get format compatibility information
   * @param {string} formatId - Format ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Compatibility information
   */
  async getCompatibility(formatId, options = {}) {
    const format = this.formats.find(format => format.id === formatId);
    
    if (!format) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Format with ID ${formatId} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    // Generate compatibility information with other formats
    const compatibilityInfo = {
      format_id: formatId,
      format_name: format.name,
      compatibility: this.formats
        .filter(f => f.id !== formatId)
        .map(f => ({
          format_id: f.id,
          format_name: f.name,
          compatibility_score: Math.random() * 0.6 + 0.4, // 0.4-1.0
          conversion_notes: [
            `${f.name} has ${Math.random() > 0.5 ? 'good' : 'limited'} compatibility with ${format.name}`,
            `Some features may not convert perfectly`
          ],
          feature_mapping: {
            data_types: Math.random() > 0.7 ? 'partial' : 'full',
            constraints: Math.random() > 0.7 ? 'partial' : 'full',
            references: Math.random() > 0.5 ? 'partial' : 'full'
          }
        }))
    };
    
    return this.processRequest(compatibilityInfo);
  }
  
  /**
   * Check if a format supports a specific feature
   * @param {string} formatId - Format ID
   * @param {string} featureId - Feature ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Feature support information
   */
  async supportsFeature(formatId, featureId, options = {}) {
    const format = this.formats.find(format => format.id === formatId);
    
    if (!format) {
      return Promise.reject({
        response: {
          status: 404,
          data: {
            error: {
              message: `Format with ID ${formatId} not found`,
              code: 'RESOURCE_NOT_FOUND'
            }
          }
        }
      });
    }
    
    // List of possible features
    const features = [
      'inheritance',
      'polymorphism',
      'union_types',
      'circular_references',
      'conditional_schemas',
      'nested_schemas',
      'validation',
      'comments',
      'default_values',
      'examples',
      'extensibility'
    ];
    
    // Check if the requested feature is valid
    if (!features.includes(featureId)) {
      return Promise.reject({
        response: {
          status: 400,
          data: {
            error: {
              message: `Invalid feature ID: ${featureId}`,
              code: 'INVALID_PARAMETER'
            }
          }
        }
      });
    }
    
    // Simulate feature support based on format
    const isSupported = Math.random() > 0.3; // 70% chance of supporting
    
    return this.processRequest({
      format_id: formatId,
      format_name: format.name,
      feature_id: featureId,
      supported: isSupported,
      details: isSupported ? 
        `${format.name} fully supports ${featureId}` : 
        `${format.name} does not support ${featureId} directly, but may have workarounds`,
      examples: isSupported ? 
        [`Example of ${featureId} in ${format.name}: ${format.example}`] : []
    });
  }
}

export default MockFormatService;
