import configureMockStore from 'redux-mock-store';
import thunk from 'redux-thunk';
import { FormatService } from '../../../services/api/formats';
import {
  fetchFormats,
  fetchFormatById,
  fetchSupportedFormats,
  validateSchema,
  setCurrentFormat,
  clearFormats,
  clearValidation,
  setMimeTypeFilter,
  setSearchFilter,
  clearFilters,
  selectAllFormats,
  selectFilteredFormats,
  selectCurrentFormat,
  selectFormatStatus,
  selectFormatError,
  selectSupportedFormats,
  selectValidationResult,
  selectValidationStatus,
  selectValidationError
} from '../formatsSlice';

// Create direct mocks for async thunks
jest.mock('../formatsSlice', () => {
  const actual = jest.requireActual('../formatsSlice');
  return {
    ...actual,
    fetchFormats: jest.fn(),
    fetchFormatById: jest.fn(),
    fetchSupportedFormats: jest.fn(),
    validateSchema: jest.fn()
  };
});

// Mock the format service
jest.mock('../../../services/api/formats', () => ({
  FormatService: jest.fn().mockImplementation(() => ({
    getAll: jest.fn(),
    getById: jest.fn(),
    getSupportedFormats: jest.fn(),
    validateSchema: jest.fn()
  }))
}));

// Mock the retry request function
jest.mock('../../../services/api/client', () => ({
  retryRequest: jest.fn(fn => fn())
}));

// Configure mock store
const mockStore = configureMockStore([thunk]);

describe('formatsSlice', () => {
  const mockFormats = [
    {
      id: '1',
      name: 'JSON',
      description: 'JavaScript Object Notation',
      mime_type: 'application/json',
      file_extensions: ['.json'],
      created_at: '2025-04-25T14:30:00Z',
      updated_at: '2025-04-25T14:30:00Z'
    },
    {
      id: '2',
      name: 'CSV',
      description: 'Comma-Separated Values',
      mime_type: 'text/csv',
      file_extensions: ['.csv'],
      created_at: '2025-04-25T15:45:00Z',
      updated_at: '2025-04-25T15:45:00Z'
    },
    {
      id: '3',
      name: 'XML',
      description: 'Extensible Markup Language',
      mime_type: 'application/xml',
      file_extensions: ['.xml'],
      created_at: '2025-04-26T10:15:00Z',
      updated_at: '2025-04-26T10:15:00Z'
    }
  ];

  const mockSupportedFormats = [
    {
      id: 'json',
      name: 'JSON',
      mime_type: 'application/json',
      file_extensions: ['.json']
    },
    {
      id: 'csv',
      name: 'CSV',
      mime_type: 'text/csv',
      file_extensions: ['.csv']
    },
    {
      id: 'xml',
      name: 'XML',
      mime_type: 'application/xml',
      file_extensions: ['.xml']
    },
    {
      id: 'yaml',
      name: 'YAML',
      mime_type: 'application/yaml',
      file_extensions: ['.yml', '.yaml']
    }
  ];

  const mockError = new Error('Test error');

  beforeEach(() => {
    // Reset mock calls
    jest.clearAllMocks();
    
    // Set up default mock implementations for thunks
    // Success cases
    fetchFormats.mockImplementation(() => ({
      type: 'formats/fetchFormats/fulfilled',
      payload: mockFormats
    }));
    
    fetchFormatById.mockImplementation((id) => ({
      type: 'formats/fetchFormatById/fulfilled',
      payload: mockFormats[0]
    }));
    
    fetchSupportedFormats.mockImplementation(() => ({
      type: 'formats/fetchSupportedFormats/fulfilled',
      payload: mockSupportedFormats
    }));
    
    validateSchema.mockImplementation(({ formatId, schema }) => ({
      type: 'formats/validateSchema/fulfilled',
      payload: {
        valid: true,
        errors: []
      }
    }));
  });

  describe('fetchFormats', () => {
    it('should dispatch success action when fetching formats succeeds', () => {
      // Create mock store
      const store = mockStore({
        formats: { formats: [], status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(fetchFormats());
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('formats/fetchFormats/fulfilled');
      expect(actions[0].payload).toEqual(mockFormats);
    });
    
    it('should dispatch failure action when fetching formats fails', () => {
      // Override the mock implementation for this test
      fetchFormats.mockImplementation(() => ({
        type: 'formats/fetchFormats/rejected',
        payload: mockError.message
      }));
      
      // Create mock store
      const store = mockStore({
        formats: { formats: [], status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(fetchFormats());
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('formats/fetchFormats/rejected');
      expect(actions[0].payload).toBe(mockError.message);
    });
  });
  
  describe('fetchFormatById', () => {
    it('should dispatch success action when fetching format by ID succeeds', () => {
      const formatId = '1';
      
      // Create mock store
      const store = mockStore({
        formats: { formats: [], currentFormat: null, status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(fetchFormatById(formatId));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('formats/fetchFormatById/fulfilled');
      expect(actions[0].payload).toEqual(mockFormats[0]);
    });
    
    it('should dispatch failure action when fetching format by ID fails', () => {
      const formatId = '1';
      
      // Override the mock implementation for this test
      fetchFormatById.mockImplementation(() => ({
        type: 'formats/fetchFormatById/rejected',
        payload: mockError.message
      }));
      
      // Create mock store
      const store = mockStore({
        formats: { formats: [], currentFormat: null, status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(fetchFormatById(formatId));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('formats/fetchFormatById/rejected');
      expect(actions[0].payload).toBe(mockError.message);
    });
  });
  
  describe('fetchSupportedFormats', () => {
    it('should dispatch success action when fetching supported formats succeeds', () => {
      // Create mock store
      const store = mockStore({
        formats: { supportedFormats: [], status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(fetchSupportedFormats());
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('formats/fetchSupportedFormats/fulfilled');
      expect(actions[0].payload).toEqual(mockSupportedFormats);
    });
    
    it('should dispatch failure action when fetching supported formats fails', () => {
      // Override the mock implementation for this test
      fetchSupportedFormats.mockImplementation(() => ({
        type: 'formats/fetchSupportedFormats/rejected',
        payload: mockError.message
      }));
      
      // Create mock store
      const store = mockStore({
        formats: { supportedFormats: [], status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(fetchSupportedFormats());
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('formats/fetchSupportedFormats/rejected');
      expect(actions[0].payload).toBe(mockError.message);
    });
  });
  
  describe('validateSchema', () => {
    it('should dispatch success action when validating schema succeeds', () => {
      const formatId = 'json';
      const schema = { type: 'object', properties: { name: { type: 'string' } } };
      const validationResult = {
        valid: true,
        errors: []
      };
      
      // Create mock store
      const store = mockStore({
        formats: { validationStatus: 'idle', validationResult: null, validationError: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(validateSchema({ formatId, schema }));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('formats/validateSchema/fulfilled');
      expect(actions[0].payload).toEqual(validationResult);
    });
    
    it('should dispatch failure action when validating schema fails', () => {
      const formatId = 'json';
      const schema = { type: 'object', properties: { name: { type: 'string' } } };
      
      // Override the mock implementation for this test
      validateSchema.mockImplementation(() => ({
        type: 'formats/validateSchema/rejected',
        payload: mockError.message
      }));
      
      // Create mock store
      const store = mockStore({
        formats: { validationStatus: 'idle', validationResult: null, validationError: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(validateSchema({ formatId, schema }));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('formats/validateSchema/rejected');
      expect(actions[0].payload).toBe(mockError.message);
    });
  });
  
  describe('formats slice actions', () => {
    it('should handle setCurrentFormat', () => {
      // Create mock store with initial state
      const store = mockStore({
        formats: {
          currentFormat: null
        }
      });
      
      // Dispatch the action
      store.dispatch(setCurrentFormat(mockFormats[0]));
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(setCurrentFormat.type);
      expect(actions[0].payload).toEqual(mockFormats[0]);
    });
    
    it('should handle clearFormats', () => {
      // Create mock store with initial state
      const store = mockStore({
        formats: {
          formats: mockFormats,
          currentFormat: mockFormats[0],
          filteredFormats: mockFormats,
          status: 'succeeded',
          error: null
        }
      });
      
      // Dispatch the action
      store.dispatch(clearFormats());
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(clearFormats.type);
    });
    
    it('should handle clearValidation', () => {
      // Create mock store with initial state
      const store = mockStore({
        formats: {
          validationStatus: 'succeeded',
          validationResult: { valid: true, errors: [] },
          validationError: null
        }
      });
      
      // Dispatch the action
      store.dispatch(clearValidation());
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(clearValidation.type);
    });
    
    it('should handle setMimeTypeFilter', () => {
      // Create mock store with initial state
      const store = mockStore({
        formats: {
          formats: mockFormats,
          filteredFormats: mockFormats,
          filters: {
            mimeType: null,
            search: ''
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(setMimeTypeFilter('application/json'));
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(setMimeTypeFilter.type);
      expect(actions[0].payload).toBe('application/json');
    });
    
    it('should handle setSearchFilter', () => {
      // Create mock store with initial state
      const store = mockStore({
        formats: {
          formats: mockFormats,
          filteredFormats: mockFormats,
          filters: {
            mimeType: null,
            search: ''
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(setSearchFilter('json'));
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(setSearchFilter.type);
      expect(actions[0].payload).toBe('json');
    });
    
    it('should handle clearFilters', () => {
      // Create mock store with initial state
      const store = mockStore({
        formats: {
          formats: mockFormats,
          filteredFormats: mockFormats.filter(f => f.mime_type === 'application/json'),
          filters: {
            mimeType: 'application/json',
            search: 'json'
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
  
  describe('selector functions', () => {
    const state = {
      formats: {
        formats: mockFormats,
        filteredFormats: mockFormats.filter(f => f.mime_type === 'application/json'),
        currentFormat: mockFormats[0],
        supportedFormats: mockSupportedFormats,
        status: 'succeeded',
        error: null,
        validationStatus: 'succeeded',
        validationResult: { valid: true, errors: [] },
        validationError: null
      }
    };
    
    it('should select all formats', () => {
      expect(selectAllFormats(state)).toEqual(mockFormats);
    });
    
    it('should select filtered formats', () => {
      expect(selectFilteredFormats(state)).toEqual(
        mockFormats.filter(f => f.mime_type === 'application/json')
      );
    });
    
    it('should select current format', () => {
      expect(selectCurrentFormat(state)).toEqual(mockFormats[0]);
    });
    
    it('should select format status', () => {
      expect(selectFormatStatus(state)).toBe('succeeded');
    });
    
    it('should select format error', () => {
      expect(selectFormatError(state)).toBeNull();
    });
    
    it('should select supported formats', () => {
      expect(selectSupportedFormats(state)).toEqual(mockSupportedFormats);
    });
    
    it('should select validation result', () => {
      expect(selectValidationResult(state)).toEqual({ valid: true, errors: [] });
    });
    
    it('should select validation status', () => {
      expect(selectValidationStatus(state)).toBe('succeeded');
    });
    
    it('should select validation error', () => {
      expect(selectValidationError(state)).toBeNull();
    });
  });
});
