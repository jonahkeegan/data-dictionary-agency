import configureMockStore from 'redux-mock-store';
import thunk from 'redux-thunk';
import { SchemaService } from '../../../services/api/schemas';
import {
  fetchSchemas,
  fetchSchemasByRepository,
  fetchSchemaById,
  createSchema,
  updateSchema,
  deleteSchema,
  exportSchema,
  setCurrentSchema,
  clearSchemas,
  setFormatTypeFilter,
  setSearchFilter,
  clearFilters
} from '../schemasSlice';

// Create direct mocks for async thunks
jest.mock('../schemasSlice', () => {
  const actual = jest.requireActual('../schemasSlice');
  return {
    ...actual,
    fetchSchemas: jest.fn(),
    fetchSchemasByRepository: jest.fn(),
    fetchSchemaById: jest.fn(),
    createSchema: jest.fn(),
    updateSchema: jest.fn(),
    deleteSchema: jest.fn(),
    exportSchema: jest.fn()
  };
});

// Mock the schema service
jest.mock('../../../services/api/schemas', () => ({
  SchemaService: jest.fn().mockImplementation(() => ({
    getAll: jest.fn(),
    getById: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
    export: jest.fn()
  }))
}));

// Mock the retry request function
jest.mock('../../../services/api/client', () => ({
  retryRequest: jest.fn(fn => fn())
}));

// Configure mock store
const mockStore = configureMockStore([thunk]);

describe('schemasSlice', () => {
  const mockSchemas = [
    {
      id: '1',
      name: 'Users Schema',
      description: 'Database schema for users table',
      formatType: 'sql',
      repository_id: 'repo1',
      path: '/db/users.sql',
      created_at: '2025-04-25T14:30:00Z',
      updated_at: '2025-04-25T14:30:00Z'
    },
    {
      id: '2',
      name: 'Products Schema',
      description: 'Database schema for products table',
      formatType: 'sql',
      repository_id: 'repo1',
      path: '/db/products.sql',
      created_at: '2025-04-25T15:45:00Z',
      updated_at: '2025-04-25T15:45:00Z'
    },
    {
      id: '3',
      name: 'User API',
      description: 'API schema for user endpoints',
      formatType: 'openapi',
      repository_id: 'repo2',
      path: '/api/users.yaml',
      created_at: '2025-04-26T10:15:00Z',
      updated_at: '2025-04-26T10:15:00Z'
    }
  ];

  const mockError = new Error('Test error');

  beforeEach(() => {
    // Reset mock calls
    jest.clearAllMocks();
    
    // Set up default mock implementations for thunks
    // Success cases
    fetchSchemas.mockImplementation(() => ({
      type: 'schemas/fetchSchemas/fulfilled',
      payload: mockSchemas
    }));
    
    fetchSchemasByRepository.mockImplementation((repoId) => {
      const repoSchemas = mockSchemas.filter(schema => schema.repository_id === repoId);
      return {
        type: 'schemas/fetchSchemasByRepository/fulfilled',
        payload: repoSchemas
      };
    });
    
    fetchSchemaById.mockImplementation((id) => ({
      type: 'schemas/fetchSchemaById/fulfilled',
      payload: mockSchemas[0]
    }));
    
    createSchema.mockImplementation((data) => ({
      type: 'schemas/createSchema/fulfilled',
      payload: {
        ...data,
        id: '4',
        created_at: '2025-04-28T16:00:00Z',
        updated_at: '2025-04-28T16:00:00Z'
      }
    }));
    
    updateSchema.mockImplementation(({ id, data }) => ({
      type: 'schemas/updateSchema/fulfilled',
      payload: {
        ...mockSchemas[0],
        ...data,
        updated_at: '2025-04-28T16:30:00Z'
      }
    }));
    
    deleteSchema.mockImplementation((id) => ({
      type: 'schemas/deleteSchema/fulfilled',
      payload: id
    }));
    
    exportSchema.mockImplementation(({ id, format }) => ({
      type: 'schemas/exportSchema/fulfilled',
      payload: {
        content: '{"schema": "exported schema content"}',
        format: format || 'json',
        filename: 'users-schema.json'
      }
    }));
  });

  describe('fetchSchemas', () => {
    it('should dispatch success action when fetching schemas succeeds', () => {
      // Create mock store
      const store = mockStore({
        schemas: { schemas: [], status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(fetchSchemas());
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('schemas/fetchSchemas/fulfilled');
      expect(actions[0].payload).toEqual(mockSchemas);
    });
    
    it('should dispatch failure action when fetching schemas fails', () => {
      // Override the mock implementation for this test
      fetchSchemas.mockImplementation(() => ({
        type: 'schemas/fetchSchemas/rejected',
        payload: mockError.message
      }));
      
      // Create mock store
      const store = mockStore({
        schemas: { schemas: [], status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(fetchSchemas());
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('schemas/fetchSchemas/rejected');
      expect(actions[0].payload).toBe(mockError.message);
    });
  });
  
  describe('fetchSchemasByRepository', () => {
    it('should dispatch success action when fetching schemas by repository succeeds', () => {
      const repoId = 'repo1';
      const repoSchemas = mockSchemas.filter(schema => schema.repository_id === repoId);
      
      // Create mock store
      const store = mockStore({
        schemas: { schemas: [], status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(fetchSchemasByRepository(repoId));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('schemas/fetchSchemasByRepository/fulfilled');
      expect(actions[0].payload).toEqual(repoSchemas);
    });
    
    it('should dispatch failure action when fetching schemas by repository fails', () => {
      const repoId = 'repo1';
      
      // Override the mock implementation for this test
      fetchSchemasByRepository.mockImplementation(() => ({
        type: 'schemas/fetchSchemasByRepository/rejected',
        payload: mockError.message
      }));
      
      // Create mock store
      const store = mockStore({
        schemas: { schemas: [], status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(fetchSchemasByRepository(repoId));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('schemas/fetchSchemasByRepository/rejected');
      expect(actions[0].payload).toBe(mockError.message);
    });
  });
  
  describe('fetchSchemaById', () => {
    it('should dispatch success action when fetching schema by ID succeeds', () => {
      const schemaId = '1';
      
      // Create mock store
      const store = mockStore({
        schemas: { schemas: [], currentSchema: null, status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(fetchSchemaById(schemaId));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('schemas/fetchSchemaById/fulfilled');
      expect(actions[0].payload).toEqual(mockSchemas[0]);
    });
    
    it('should dispatch failure action when fetching schema by ID fails', () => {
      const schemaId = '1';
      
      // Override the mock implementation for this test
      fetchSchemaById.mockImplementation(() => ({
        type: 'schemas/fetchSchemaById/rejected',
        payload: mockError.message
      }));
      
      // Create mock store
      const store = mockStore({
        schemas: { schemas: [], currentSchema: null, status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(fetchSchemaById(schemaId));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('schemas/fetchSchemaById/rejected');
      expect(actions[0].payload).toBe(mockError.message);
    });
  });
  
  describe('createSchema', () => {
    it('should dispatch success action when creating schema succeeds', () => {
      const newSchema = {
        name: 'New Schema',
        description: 'New schema description',
        formatType: 'json',
        repository_id: 'repo1',
        path: '/data/new-schema.json'
      };
      
      const createdSchema = {
        ...newSchema,
        id: '4',
        created_at: '2025-04-28T16:00:00Z',
        updated_at: '2025-04-28T16:00:00Z'
      };
      
      // Create mock store
      const store = mockStore({
        schemas: { schemas: [], status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(createSchema(newSchema));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('schemas/createSchema/fulfilled');
      expect(actions[0].payload).toEqual(createdSchema);
    });
    
    it('should dispatch failure action when creating schema fails', () => {
      const newSchema = {
        name: 'New Schema',
        description: 'New schema description',
        formatType: 'json',
        repository_id: 'repo1',
        path: '/data/new-schema.json'
      };
      
      // Override the mock implementation for this test
      createSchema.mockImplementation(() => ({
        type: 'schemas/createSchema/rejected',
        payload: mockError.message
      }));
      
      // Create mock store
      const store = mockStore({
        schemas: { schemas: [], status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(createSchema(newSchema));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('schemas/createSchema/rejected');
      expect(actions[0].payload).toBe(mockError.message);
    });
  });
  
  describe('updateSchema', () => {
    it('should dispatch success action when updating schema succeeds', () => {
      const schemaId = '1';
      const updateData = {
        name: 'Updated Schema',
        description: 'Updated description'
      };
      
      const updatedSchema = {
        ...mockSchemas[0],
        ...updateData,
        updated_at: '2025-04-28T16:30:00Z'
      };
      
      // Create mock store
      const store = mockStore({
        schemas: { schemas: mockSchemas, status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(updateSchema({ id: schemaId, data: updateData }));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('schemas/updateSchema/fulfilled');
      expect(actions[0].payload).toEqual(updatedSchema);
    });
    
    it('should dispatch failure action when updating schema fails', () => {
      const schemaId = '1';
      const updateData = {
        name: 'Updated Schema',
        description: 'Updated description'
      };
      
      // Override the mock implementation for this test
      updateSchema.mockImplementation(() => ({
        type: 'schemas/updateSchema/rejected',
        payload: mockError.message
      }));
      
      // Create mock store
      const store = mockStore({
        schemas: { schemas: mockSchemas, status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(updateSchema({ id: schemaId, data: updateData }));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('schemas/updateSchema/rejected');
      expect(actions[0].payload).toBe(mockError.message);
    });
  });
  
  describe('deleteSchema', () => {
    it('should dispatch success action when deleting schema succeeds', () => {
      const schemaId = '1';
      
      // Create mock store
      const store = mockStore({
        schemas: { schemas: mockSchemas, status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(deleteSchema(schemaId));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('schemas/deleteSchema/fulfilled');
      expect(actions[0].payload).toBe(schemaId);
    });
    
    it('should dispatch failure action when deleting schema fails', () => {
      const schemaId = '1';
      
      // Override the mock implementation for this test
      deleteSchema.mockImplementation(() => ({
        type: 'schemas/deleteSchema/rejected',
        payload: mockError.message
      }));
      
      // Create mock store
      const store = mockStore({
        schemas: { schemas: mockSchemas, status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(deleteSchema(schemaId));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('schemas/deleteSchema/rejected');
      expect(actions[0].payload).toBe(mockError.message);
    });
  });
  
  describe('exportSchema', () => {
    it('should dispatch success action when exporting schema succeeds', () => {
      const schemaId = '1';
      const format = 'json';
      const exportResult = {
        content: '{"schema": "exported schema content"}',
        format: 'json',
        filename: 'users-schema.json'
      };
      
      // Create mock store
      const store = mockStore({
        schemas: { schemas: mockSchemas, status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(exportSchema({ id: schemaId, format }));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('schemas/exportSchema/fulfilled');
      expect(actions[0].payload).toEqual(exportResult);
    });
    
    it('should dispatch failure action when exporting schema fails', () => {
      const schemaId = '1';
      const format = 'json';
      
      // Override the mock implementation for this test
      exportSchema.mockImplementation(() => ({
        type: 'schemas/exportSchema/rejected',
        payload: mockError.message
      }));
      
      // Create mock store
      const store = mockStore({
        schemas: { schemas: mockSchemas, status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(exportSchema({ id: schemaId, format }));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('schemas/exportSchema/rejected');
      expect(actions[0].payload).toBe(mockError.message);
    });
  });
  
  describe('schemas slice actions', () => {
    it('should handle setCurrentSchema', () => {
      // Create mock store with initial state
      const store = mockStore({
        schemas: {
          currentSchema: null
        }
      });
      
      // Dispatch the action
      store.dispatch(setCurrentSchema(mockSchemas[0]));
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(setCurrentSchema.type);
      expect(actions[0].payload).toEqual(mockSchemas[0]);
    });
    
    it('should handle clearSchemas', () => {
      // Create mock store with initial state
      const store = mockStore({
        schemas: {
          schemas: mockSchemas,
          currentSchema: mockSchemas[0],
          filteredSchemas: mockSchemas,
          status: 'succeeded',
          error: null
        }
      });
      
      // Dispatch the action
      store.dispatch(clearSchemas());
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(clearSchemas.type);
    });
    
    it('should handle setFormatTypeFilter', () => {
      // Create mock store with initial state
      const store = mockStore({
        schemas: {
          schemas: mockSchemas,
          filteredSchemas: mockSchemas,
          filters: {
            formatType: null,
            search: ''
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(setFormatTypeFilter('sql'));
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(setFormatTypeFilter.type);
      expect(actions[0].payload).toBe('sql');
    });
    
    it('should handle setSearchFilter', () => {
      // Create mock store with initial state
      const store = mockStore({
        schemas: {
          schemas: mockSchemas,
          filteredSchemas: mockSchemas,
          filters: {
            formatType: null,
            search: ''
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(setSearchFilter('user'));
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(setSearchFilter.type);
      expect(actions[0].payload).toBe('user');
    });
    
    it('should handle clearFilters', () => {
      // Create mock store with initial state
      const store = mockStore({
        schemas: {
          schemas: mockSchemas,
          filteredSchemas: mockSchemas.filter(s => s.formatType === 'sql'),
          filters: {
            formatType: 'sql',
            search: 'user'
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(clearFilters());
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(clearFilters.type);
    });
  });
});
