/**
 * Mock Data
 * 
 * Provides realistic test data for mock services.
 * This allows development and testing without a live backend.
 */

// Generate a random ID with a given prefix
const generateId = (prefix = 'id') => {
  return `${prefix}-${Math.random().toString(36).substring(2, 10)}`;
};

// Format dates in ISO format
const formatDate = (date) => {
  return date.toISOString();
};

// Generate a date in the past
const pastDate = (daysAgo = 0) => {
  const date = new Date();
  date.setDate(date.getDate() - daysAgo);
  return formatDate(date);
};

// Mock repository data
export const repositories = [
  {
    id: 'repo-1',
    name: 'Customer Data Warehouse',
    description: 'Central repository for customer data schemas and models',
    url: 'https://github.com/example-corp/customer-data-warehouse',
    status: 'active',
    progress: 100,
    created_at: pastDate(30),
    updated_at: pastDate(2)
  },
  {
    id: 'repo-2',
    name: 'Product Inventory System',
    description: 'Inventory management system schemas',
    url: 'https://github.com/example-corp/inventory-schemas',
    status: 'active',
    progress: 100,
    created_at: pastDate(45),
    updated_at: pastDate(5)
  },
  {
    id: 'repo-3',
    name: 'Sales Analytics Pipeline',
    description: 'Data pipeline configurations and schemas for sales analytics',
    url: 'https://github.com/example-corp/sales-analytics',
    status: 'active',
    progress: 75,
    created_at: pastDate(20),
    updated_at: pastDate(1)
  },
  {
    id: 'repo-4',
    name: 'Marketing Campaign Manager',
    description: 'Campaign management and audience segmentation schemas',
    url: 'https://github.com/example-corp/campaign-manager',
    status: 'inactive',
    progress: 50,
    created_at: pastDate(60),
    updated_at: pastDate(30)
  },
  {
    id: 'repo-5',
    name: 'Legacy Systems Integration',
    description: 'Integration schemas for legacy systems',
    url: 'https://github.com/example-corp/legacy-integration',
    status: 'pending',
    progress: 25,
    created_at: pastDate(10),
    updated_at: pastDate(10)
  }
];

// Mock format data
export const formats = [
  {
    id: 'format-1',
    name: 'JSON Schema',
    description: 'JSON Schema specification for describing JSON data structures',
    mime_type: 'application/schema+json',
    file_extensions: ['.json', '.schema.json'],
    detection_patterns: ['\\$schema'],
    example: '{ "$schema": "http://json-schema.org/draft-07/schema#" }',
    created_at: pastDate(90),
    updated_at: pastDate(30)
  },
  {
    id: 'format-2',
    name: 'SQL',
    description: 'SQL database schema definition language (DDL)',
    mime_type: 'text/plain',
    file_extensions: ['.sql'],
    detection_patterns: ['CREATE\\s+TABLE', 'ALTER\\s+TABLE'],
    example: 'CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100))',
    created_at: pastDate(90),
    updated_at: pastDate(30)
  },
  {
    id: 'format-3',
    name: 'XML Schema',
    description: 'XML Schema Definition (XSD) for describing XML documents',
    mime_type: 'application/xml',
    file_extensions: ['.xsd'],
    detection_patterns: ['<xs:schema', '<xsd:schema'],
    example: '<?xml version="1.0"?><xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"></xs:schema>',
    created_at: pastDate(90),
    updated_at: pastDate(30)
  },
  {
    id: 'format-4',
    name: 'Avro Schema',
    description: 'Apache Avro schema definition for binary serialization',
    mime_type: 'application/json',
    file_extensions: ['.avsc'],
    detection_patterns: ['"type"\\s*:\\s*"record"'],
    example: '{"type": "record", "name": "User", "fields": [{"name": "id", "type": "string"}]}',
    created_at: pastDate(90),
    updated_at: pastDate(30)
  },
  {
    id: 'format-5',
    name: 'Protocol Buffers',
    description: 'Google Protocol Buffers (Protobuf) schema definition',
    mime_type: 'text/plain',
    file_extensions: ['.proto'],
    detection_patterns: ['syntax\\s*=\\s*"proto[23]"', 'message\\s+[A-Za-z0-9_]+\\s*{'],
    example: 'syntax = "proto3"; message User { string id = 1; }',
    created_at: pastDate(90),
    updated_at: pastDate(30)
  },
  {
    id: 'format-6',
    name: 'GraphQL',
    description: 'GraphQL schema definition language (SDL)',
    mime_type: 'text/plain',
    file_extensions: ['.graphql', '.gql'],
    detection_patterns: ['type\\s+[A-Za-z0-9_]+\\s*{', 'input\\s+[A-Za-z0-9_]+\\s*{'],
    example: 'type User { id: ID! name: String }',
    created_at: pastDate(90),
    updated_at: pastDate(30)
  },
  {
    id: 'format-7',
    name: 'OpenAPI',
    description: 'OpenAPI (formerly Swagger) API specification format',
    mime_type: 'application/json',
    file_extensions: ['.json', '.yaml', '.yml'],
    detection_patterns: ['"openapi"\\s*:', 'openapi:'],
    example: '{ "openapi": "3.0.0", "info": { "title": "API", "version": "1.0.0" } }',
    created_at: pastDate(90),
    updated_at: pastDate(30)
  },
  {
    id: 'format-8',
    name: 'YAML',
    description: 'YAML schema definitions (custom or OpenAPI)',
    mime_type: 'text/yaml',
    file_extensions: ['.yaml', '.yml'],
    detection_patterns: [],
    example: 'type: object\nproperties:\n  id:\n    type: string',
    created_at: pastDate(90),
    updated_at: pastDate(30)
  }
];

// Mock schema data generator
const createMockSchema = (id, repoId, formatId, name, description) => {
  const format = formats.find(f => f.id === formatId);
  
  return {
    id,
    name,
    description,
    repository_id: repoId,
    format_id: formatId,
    format_name: format ? format.name : 'Unknown Format',
    file_path: `/schemas/${name.toLowerCase().replace(/\s+/g, '-')}.${formatId === 'format-1' ? 'json' : formatId === 'format-2' ? 'sql' : 'txt'}`,
    created_at: pastDate(Math.floor(Math.random() * 30) + 1),
    updated_at: pastDate(Math.floor(Math.random() * 10)),
    content: format ? format.example : '{}'
  };
};

// Mock schema data
export const schemas = [
  createMockSchema('schema-1', 'repo-1', 'format-1', 'Customer Profile', 'Core customer profile data structure'),
  createMockSchema('schema-2', 'repo-1', 'format-1', 'Customer Address', 'Customer address information schema'),
  createMockSchema('schema-3', 'repo-1', 'format-1', 'Customer Preferences', 'Customer preference settings'),
  createMockSchema('schema-4', 'repo-1', 'format-2', 'Customer Database', 'SQL schema for customer database'),
  
  createMockSchema('schema-5', 'repo-2', 'format-1', 'Product Catalog', 'Product catalog schema definition'),
  createMockSchema('schema-6', 'repo-2', 'format-1', 'Inventory Status', 'Inventory levels and status schema'),
  createMockSchema('schema-7', 'repo-2', 'format-3', 'Product XML Format', 'XML format for product exports'),
  
  createMockSchema('schema-8', 'repo-3', 'format-1', 'Sales Transaction', 'Sales transaction data schema'),
  createMockSchema('schema-9', 'repo-3', 'format-4', 'Analytics Event', 'Avro schema for analytics events'),
  
  createMockSchema('schema-10', 'repo-4', 'format-1', 'Campaign Definition', 'Marketing campaign definition schema'),
  createMockSchema('schema-11', 'repo-4', 'format-1', 'Audience Segment', 'Audience segmentation schema'),
  
  createMockSchema('schema-12', 'repo-5', 'format-2', 'Legacy Database', 'Schema for legacy database integration')
];

// Mock relationship data
export const relationships = [
  {
    id: 'rel-1',
    source_schema_id: 'schema-1',
    target_schema_id: 'schema-2',
    relationship_type: 'one-to-many',
    confidence: 0.95,
    properties: {
      source_field: 'id',
      target_field: 'customer_id'
    }
  },
  {
    id: 'rel-2',
    source_schema_id: 'schema-1',
    target_schema_id: 'schema-3',
    relationship_type: 'one-to-one',
    confidence: 0.9,
    properties: {
      source_field: 'id',
      target_field: 'customer_id'
    }
  },
  {
    id: 'rel-3',
    source_schema_id: 'schema-1',
    target_schema_id: 'schema-8',
    relationship_type: 'one-to-many',
    confidence: 0.85,
    properties: {
      source_field: 'id',
      target_field: 'customer_id'
    }
  },
  {
    id: 'rel-4',
    source_schema_id: 'schema-5',
    target_schema_id: 'schema-6',
    relationship_type: 'one-to-one',
    confidence: 0.9,
    properties: {
      source_field: 'id',
      target_field: 'product_id'
    }
  },
  {
    id: 'rel-5',
    source_schema_id: 'schema-5',
    target_schema_id: 'schema-8',
    relationship_type: 'one-to-many',
    confidence: 0.8,
    properties: {
      source_field: 'id',
      target_field: 'product_id'
    }
  }
];

// Mock user data
export const users = [
  {
    id: 'user-1',
    username: 'admin',
    email: 'admin@example.com',
    first_name: 'Admin',
    last_name: 'User',
    roles: ['admin'],
    permissions: ['read', 'write', 'delete', 'manage_users'],
    created_at: pastDate(90),
    last_login: pastDate(1)
  },
  {
    id: 'user-2',
    username: 'johndoe',
    email: 'john.doe@example.com',
    first_name: 'John',
    last_name: 'Doe',
    roles: ['editor'],
    permissions: ['read', 'write'],
    created_at: pastDate(60),
    last_login: pastDate(5)
  },
  {
    id: 'user-3',
    username: 'janesmith',
    email: 'jane.smith@example.com',
    first_name: 'Jane',
    last_name: 'Smith',
    roles: ['viewer'],
    permissions: ['read'],
    created_at: pastDate(30),
    last_login: pastDate(2)
  }
];

// Helper to simulate network delay
export const withDelay = (data, minDelay = 100, maxDelay = 500) => {
  const delay = Math.floor(Math.random() * (maxDelay - minDelay + 1)) + minDelay;
  
  return new Promise(resolve => {
    setTimeout(() => {
      resolve(data);
    }, delay);
  });
};

// Helper to randomly fail requests (for testing error handling)
export const withRandomFailure = (data, failureRate = 0.1, errorStatus = 500) => {
  if (Math.random() < failureRate) {
    return Promise.reject({
      response: {
        status: errorStatus,
        data: {
          error: {
            message: 'Simulated random server error',
            code: 'SIMULATED_ERROR'
          }
        }
      }
    });
  }
  
  return Promise.resolve(data);
};

// Filter data by query parameters
export const filterData = (data, params = {}) => {
  let result = [...data];
  
  // Apply filters based on params
  Object.entries(params).forEach(([key, value]) => {
    if (key === 'skip' || key === 'limit' || key === 'sort' || key === 'order') {
      return; // Skip pagination and sorting params
    }
    
    result = result.filter(item => {
      if (key === 'query' && typeof value === 'string') {
        // Search in name and description
        const query = value.toLowerCase();
        return (
          (item.name && item.name.toLowerCase().includes(query)) ||
          (item.description && item.description.toLowerCase().includes(query))
        );
      }
      
      // Direct property match
      return item[key] === value;
    });
  });
  
  // Apply sorting
  if (params.sort) {
    const direction = (params.order === 'desc') ? -1 : 1;
    result.sort((a, b) => {
      if (a[params.sort] < b[params.sort]) return -1 * direction;
      if (a[params.sort] > b[params.sort]) return 1 * direction;
      return 0;
    });
  }
  
  // Apply pagination
  const skip = parseInt(params.skip, 10) || 0;
  const limit = parseInt(params.limit, 10) || result.length;
  
  result = result.slice(skip, skip + limit);
  
  return result;
};

export default {
  repositories,
  formats,
  schemas,
  relationships,
  users,
  withDelay,
  withRandomFailure,
  filterData,
  generateId,
  pastDate
};
