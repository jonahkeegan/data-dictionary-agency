/**
 * Mock API services for the Data Dictionary Agency frontend
 * Provides simulated API responses for development and testing
 */
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import { getConfig } from '../../config';
import { repositoryData } from './data/repositories';
import { schemaData } from './data/schemas';
import { formatData } from './data/formats';

// Set up mock response delay (ms)
const MOCK_DELAY = 800;

/**
 * Initialize mock services for the API client
 * @param {Object} apiClient - Axios instance to mock
 * @returns {Object|null} MockAdapter instance or null if mocks disabled
 */
export const setupMockServices = (apiClient) => {
  const config = getConfig();
  
  // Only enable mocks in development or if explicitly enabled
  if (!config.mockEnabled) {
    console.log('Mock API services disabled');
    return null;
  }
  
  console.log('🔶 Mock API services enabled');
  const mock = new MockAdapter(apiClient, { delayResponse: MOCK_DELAY });
  
  // Set up repository endpoints
  setupRepositoryMocks(mock);
  
  // Set up schema endpoints
  setupSchemaMocks(mock);
  
  // Set up format endpoints
  setupFormatMocks(mock);
  
  return mock;
};

/**
 * Set up repository endpoint mocks
 * @param {Object} mock - MockAdapter instance
 */
const setupRepositoryMocks = (mock) => {
  // GET /repositories
  mock.onGet('/repositories').reply((config) => {
    const params = new URLSearchParams(config.url.split('?')[1] || '');
    const skip = parseInt(params.get('skip') || '0', 10);
    const limit = parseInt(params.get('limit') || '100', 10);
    
    const paginatedData = repositoryData.slice(skip, skip + limit);
    
    return [200, paginatedData];
  });
  
  // GET /repositories/:id
  mock.onGet(/\/repositories\/\w+/).reply((config) => {
    const id = config.url.split('/').pop();
    const repository = repositoryData.find(r => r.id === id);
    
    return repository 
      ? [200, repository] 
      : [404, { detail: `Repository with ID ${id} not found` }];
  });
  
  // POST /repositories
  mock.onPost('/repositories').reply((config) => {
    // Parse request body
    const data = JSON.parse(config.data);
    
    // Create a new repository with generated ID
    const newRepository = {
      id: `mock-repo-${Date.now()}`,
      created_at: new Date().toISOString(),
      ...data
    };
    
    // In a real mock we'd push to the array, but this is stateless
    // In a more sophisticated implementation, we could use a mock store
    
    return [201, newRepository];
  });
  
  // DELETE /repositories/:id
  mock.onDelete(/\/repositories\/\w+/).reply((config) => {
    const id = config.url.split('/').pop();
    const repository = repositoryData.find(r => r.id === id);
    
    return repository 
      ? [204] 
      : [404, { detail: `Repository with ID ${id} not found` }];
  });
  
  // POST /repositories/:id/analyze
  mock.onPost(/\/repositories\/\w+\/analyze/).reply((config) => {
    const id = config.url.split('/').slice(-2)[0];
    const repository = repositoryData.find(r => r.id === id);
    
    if (!repository) {
      return [404, { detail: `Repository with ID ${id} not found` }];
    }
    
    // Return a mock analysis result
    return [200, {
      id: repository.id,
      status: 'analyzing',
      progress: 0,
      started_at: new Date().toISOString()
    }];
  });
};

/**
 * Set up schema endpoint mocks
 * @param {Object} mock - MockAdapter instance
 */
const setupSchemaMocks = (mock) => {
  // GET /schemas
  mock.onGet('/schemas').reply((config) => {
    const params = new URLSearchParams(config.url.split('?')[1] || '');
    const skip = parseInt(params.get('skip') || '0', 10);
    const limit = parseInt(params.get('limit') || '100', 10);
    const repositoryId = params.get('repository_id');
    const formatId = params.get('format_id');
    
    // Filter by repository and/or format if provided
    let filteredData = [...schemaData];
    if (repositoryId) {
      filteredData = filteredData.filter(s => s.repository_id === repositoryId);
    }
    if (formatId) {
      filteredData = filteredData.filter(s => s.format_id === formatId);
    }
    
    const paginatedData = filteredData.slice(skip, skip + limit);
    
    return [200, paginatedData];
  });
  
  // GET /schemas/:id
  mock.onGet(/\/schemas\/\w+$/).reply((config) => {
    const id = config.url.split('/').pop();
    const schema = schemaData.find(s => s.id === id);
    
    return schema 
      ? [200, schema] 
      : [404, { detail: `Schema with ID ${id} not found` }];
  });
  
  // POST /schemas
  mock.onPost('/schemas').reply((config) => {
    // Parse request body
    const data = JSON.parse(config.data);
    
    // Create a new schema with generated ID
    const newSchema = {
      id: `mock-schema-${Date.now()}`,
      created_at: new Date().toISOString(),
      ...data
    };
    
    return [201, newSchema];
  });
  
  // PUT /schemas/:id
  mock.onPut(/\/schemas\/\w+/).reply((config) => {
    const id = config.url.split('/').pop();
    const schema = schemaData.find(s => s.id === id);
    
    if (!schema) {
      return [404, { detail: `Schema with ID ${id} not found` }];
    }
    
    // Parse request body
    const data = JSON.parse(config.data);
    
    // Update schema
    const updatedSchema = {
      ...schema,
      ...data,
      updated_at: new Date().toISOString()
    };
    
    return [200, updatedSchema];
  });
  
  // DELETE /schemas/:id
  mock.onDelete(/\/schemas\/\w+/).reply((config) => {
    const id = config.url.split('/').pop();
    const schema = schemaData.find(s => s.id === id);
    
    return schema 
      ? [204] 
      : [404, { detail: `Schema with ID ${id} not found` }];
  });
  
  // GET /schemas/:id/relationships
  mock.onGet(/\/schemas\/\w+\/relationships/).reply((config) => {
    const id = config.url.split('/').slice(-2)[0];
    const schema = schemaData.find(s => s.id === id);
    
    if (!schema) {
      return [404, { detail: `Schema with ID ${id} not found` }];
    }
    
    // Generate mock relationships
    const relationships = schemaData
      .filter(s => s.id !== id) // Don't relate to self
      .slice(0, 3) // Limit to 3 random relationships
      .map(relatedSchema => ({
        id: `rel-${id}-${relatedSchema.id}`,
        source_schema_id: id,
        target_schema_id: relatedSchema.id,
        confidence: Math.random().toFixed(2),
        relationship_type: Math.random() > 0.5 ? 'CONTAINS' : 'REFERENCES',
        fields: [
          {
            source_field: 'id',
            target_field: 'reference_id'
          }
        ]
      }));
    
    return [200, relationships];
  });
  
  // POST /schemas/:id/export
  mock.onPost(/\/schemas\/\w+\/export/).reply((config) => {
    const id = config.url.split('/').slice(-2)[0];
    const schema = schemaData.find(s => s.id === id);
    
    if (!schema) {
      return [404, { detail: `Schema with ID ${id} not found` }];
    }
    
    const params = new URLSearchParams(config.url.split('?')[1] || '');
    const format = params.get('format') || 'json';
    
    // Return different export formats based on format parameter
    switch (format) {
      case 'json':
        return [200, { schema: schema.content, format: 'json' }];
      case 'yaml':
        return [200, { schema: `name: ${schema.name}\nfields:\n  id: string\n  name: string`, format: 'yaml' }];
      case 'sql':
        return [200, { 
          schema: `CREATE TABLE ${schema.name} (\n  id VARCHAR(50) PRIMARY KEY,\n  name VARCHAR(100) NOT NULL\n);`, 
          format: 'sql' 
        }];
      default:
        return [400, { detail: `Unsupported export format: ${format}` }];
    }
  });
};

/**
 * Set up format endpoint mocks
 * @param {Object} mock - MockAdapter instance
 */
const setupFormatMocks = (mock) => {
  // GET /formats
  mock.onGet('/formats').reply((config) => {
    const params = new URLSearchParams(config.url.split('?')[1] || '');
    const skip = parseInt(params.get('skip') || '0', 10);
    const limit = parseInt(params.get('limit') || '100', 10);
    
    const paginatedData = formatData.slice(skip, skip + limit);
    
    return [200, paginatedData];
  });
  
  // GET /formats/:id
  mock.onGet(/\/formats\/\w+$/).reply((config) => {
    const id = config.url.split('/').pop();
    const format = formatData.find(f => f.id === id);
    
    return format 
      ? [200, format] 
      : [404, { detail: `Format with ID ${id} not found` }];
  });
  
  // POST /formats/detect
  mock.onPost('/formats/detect').reply((config) => {
    // Parse request body
    const data = JSON.parse(config.data);
    const content = data.content || '';
    const filename = data.filename || '';
    
    // Based on content and filename, detect format
    let detections = {};
    
    // JSON detection
    if (
      (filename.endsWith('.json') || content.trim().startsWith('{')) && 
      isValidJson(content)
    ) {
      detections['json'] = 0.95;
    }
    
    // YAML detection
    if (
      filename.endsWith('.yml') || 
      filename.endsWith('.yaml') || 
      content.includes('---')
    ) {
      detections['yaml'] = 0.90;
    }
    
    // XML detection
    if (
      filename.endsWith('.xml') || 
      content.includes('<?xml') || 
      (content.includes('<') && content.includes('</'))
    ) {
      detections['xml'] = 0.85;
    }
    
    // If no specific format detected, return some default detections
    if (Object.keys(detections).length === 0) {
      detections = {
        'json': 0.3,
        'yaml': 0.25,
        'xml': 0.2,
        'csv': 0.15
      };
    }
    
    return [200, {
      detections,
      best_match: Object.entries(detections).sort((a, b) => b[1] - a[1])[0][0]
    }];
  });
  
  // GET /formats/:id/schemas
  mock.onGet(/\/formats\/\w+\/schemas/).reply((config) => {
    const id = config.url.split('/').slice(-2)[0];
    const format = formatData.find(f => f.id === id);
    
    if (!format) {
      return [404, { detail: `Format with ID ${id} not found` }];
    }
    
    // Filter schemas by format
    const formatSchemas = schemaData.filter(s => s.format_id === id);
    
    const params = new URLSearchParams(config.url.split('?')[1] || '');
    const skip = parseInt(params.get('skip') || '0', 10);
    const limit = parseInt(params.get('limit') || '100', 10);
    
    const paginatedData = formatSchemas.slice(skip, skip + limit);
    
    return [200, paginatedData];
  });
  
  // GET /formats/:id/documentation
  mock.onGet(/\/formats\/\w+\/documentation/).reply((config) => {
    const id = config.url.split('/').pop();
    const format = formatData.find(f => f.id === id);
    
    if (!format) {
      return [404, { detail: `Format with ID ${id} not found` }];
    }
    
    // Return mock documentation based on format
    return [200, {
      id: format.id,
      name: format.name,
      description: format.description,
      specification_url: `https://example.com/specifications/${format.name.toLowerCase()}`,
      documentation: `# ${format.name} Format Documentation\n\n${format.description}\n\n## Example\n\`\`\`\n${format.example}\n\`\`\``,
      examples: [
        {
          name: 'Basic Example',
          content: format.example
        },
        {
          name: 'Advanced Example',
          content: format.example + '\n// Additional features'
        }
      ]
    }];
  });
};

/**
 * Helper function to check if a string is valid JSON
 * @param {string} str - String to check
 * @returns {boolean} Whether string is valid JSON
 */
const isValidJson = (str) => {
  try {
    JSON.parse(str);
    return true;
  } catch (e) {
    return false;
  }
};

// Initialize mock services with the default API client when imported
import { apiClient } from '../api/client';
export const mockAdapter = setupMockServices(apiClient);
