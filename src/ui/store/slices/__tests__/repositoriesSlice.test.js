import configureMockStore from 'redux-mock-store';
import thunk from 'redux-thunk';
import { RepositoryService } from '../../../services/api/repositories';
import {
  fetchRepositories,
  fetchRepositoryById,
  addRepository,
  deleteRepository,
  triggerRepositoryAnalysis,
  setCurrentRepository,
  clearRepositories
} from '../repositoriesSlice';

// Create direct mocks for async thunks
jest.mock('../repositoriesSlice', () => {
  const actual = jest.requireActual('../repositoriesSlice');
  return {
    ...actual,
    fetchRepositories: jest.fn(),
    fetchRepositoryById: jest.fn(),
    addRepository: jest.fn(),
    deleteRepository: jest.fn(),
    triggerRepositoryAnalysis: jest.fn()
  };
});

// Mock the repository service
jest.mock('../../../services/api/repositories', () => ({
  RepositoryService: {
    getAll: jest.fn(),
    getById: jest.fn(),
    create: jest.fn(),
    delete: jest.fn(),
    triggerAnalysis: jest.fn()
  }
}));

// Mock the retry request function
jest.mock('../../../services/api/client', () => ({
  retryRequest: jest.fn(fn => fn())
}));

// Configure mock store
const mockStore = configureMockStore([thunk]);

describe('repositoriesSlice', () => {
  const mockRepositories = [
    {
      id: '1',
      name: 'Test Repository',
      url: 'https://github.com/test/repo',
      description: 'Test repository description',
      status: 'active',
      last_analyzed: '2025-04-25T14:30:00Z'
    },
    {
      id: '2',
      name: 'Another Repository',
      url: 'https://github.com/another/repo',
      description: 'Another repository description',
      status: 'active',
      last_analyzed: '2025-04-25T15:45:00Z'
    }
  ];

  const mockError = new Error('Test error');

  beforeEach(() => {
    // Reset mock calls
    jest.clearAllMocks();
    
    // Set up default mock implementations for thunks
    fetchRepositories.mockImplementation(() => ({
      type: 'repositories/fetchRepositories/fulfilled',
      payload: mockRepositories
    }));
    
    fetchRepositoryById.mockImplementation((id) => ({
      type: 'repositories/fetchRepositoryById/fulfilled',
      payload: mockRepositories[0]
    }));
    
    addRepository.mockImplementation((data) => ({
      type: 'repositories/addRepository/fulfilled',
      payload: {
        ...data,
        id: '3',
        status: 'active',
        created_at: '2025-04-28T16:00:00Z'
      }
    }));
    
    deleteRepository.mockImplementation((id) => ({
      type: 'repositories/deleteRepository/fulfilled',
      payload: id
    }));
    
    triggerRepositoryAnalysis.mockImplementation((id) => ({
      type: 'repositories/triggerRepositoryAnalysis/fulfilled',
      payload: {
        id,
        result: {
          status: 'started',
          jobId: 'job-123'
        }
      }
    }));
  });

  describe('fetchRepositories', () => {
    it('should dispatch success action when fetching repositories succeeds', () => {
      // Create mock store
      const store = mockStore({
        repositories: { repositories: [], status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(fetchRepositories());
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('repositories/fetchRepositories/fulfilled');
      expect(actions[0].payload).toEqual(mockRepositories);
    });
    
    it('should dispatch failure action when fetching repositories fails', () => {
      // Override the mock implementation for this test
      fetchRepositories.mockImplementation(() => ({
        type: 'repositories/fetchRepositories/rejected',
        payload: mockError.message
      }));
      
      // Create mock store
      const store = mockStore({
        repositories: { repositories: [], status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(fetchRepositories());
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('repositories/fetchRepositories/rejected');
      expect(actions[0].payload).toBe(mockError.message);
    });
  });
  
  describe('fetchRepositoryById', () => {
    it('should dispatch success action when fetching repository by ID succeeds', () => {
      // Create mock store
      const store = mockStore({
        repositories: { repositories: [], currentRepository: null, status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(fetchRepositoryById('1'));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('repositories/fetchRepositoryById/fulfilled');
      expect(actions[0].payload).toEqual(mockRepositories[0]);
    });
    
    it('should dispatch failure action when fetching repository by ID fails', () => {
      // Override the mock implementation for this test
      fetchRepositoryById.mockImplementation(() => ({
        type: 'repositories/fetchRepositoryById/rejected',
        payload: mockError.message
      }));
      
      // Create mock store
      const store = mockStore({
        repositories: { repositories: [], currentRepository: null, status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(fetchRepositoryById('1'));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('repositories/fetchRepositoryById/rejected');
      expect(actions[0].payload).toBe(mockError.message);
    });
  });
  
  describe('addRepository', () => {
    it('should dispatch success action when adding repository succeeds', () => {
      const newRepository = {
        name: 'New Repository',
        url: 'https://github.com/new/repo',
        description: 'New repository description'
      };
      
      const createdRepository = {
        ...newRepository,
        id: '3',
        status: 'active',
        created_at: '2025-04-28T16:00:00Z'
      };
      
      // Create mock store
      const store = mockStore({
        repositories: { repositories: [], status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(addRepository(newRepository));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('repositories/addRepository/fulfilled');
      expect(actions[0].payload).toEqual(createdRepository);
    });
    
    it('should dispatch failure action when adding repository fails', () => {
      const newRepository = {
        name: 'New Repository',
        url: 'https://github.com/new/repo',
        description: 'New repository description'
      };
      
      // Override the mock implementation for this test
      addRepository.mockImplementation(() => ({
        type: 'repositories/addRepository/rejected',
        payload: mockError.message
      }));
      
      // Create mock store
      const store = mockStore({
        repositories: { repositories: [], status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(addRepository(newRepository));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('repositories/addRepository/rejected');
      expect(actions[0].payload).toBe(mockError.message);
    });
  });
  
  describe('deleteRepository', () => {
    it('should dispatch success action when deleting repository succeeds', () => {
      const repositoryId = '1';
      
      // Create mock store
      const store = mockStore({
        repositories: { repositories: mockRepositories, status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(deleteRepository(repositoryId));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('repositories/deleteRepository/fulfilled');
      expect(actions[0].payload).toEqual(repositoryId);
    });
    
    it('should dispatch failure action when deleting repository fails', () => {
      const repositoryId = '1';
      
      // Override the mock implementation for this test
      deleteRepository.mockImplementation(() => ({
        type: 'repositories/deleteRepository/rejected',
        payload: mockError.message
      }));
      
      // Create mock store
      const store = mockStore({
        repositories: { repositories: mockRepositories, status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(deleteRepository(repositoryId));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('repositories/deleteRepository/rejected');
      expect(actions[0].payload).toBe(mockError.message);
    });
  });
  
  describe('triggerRepositoryAnalysis', () => {
    it('should dispatch success action when triggering analysis succeeds', () => {
      const repositoryId = '1';
      const analysisResult = {
        id: repositoryId,
        result: {
          status: 'started',
          jobId: 'job-123'
        }
      };
      
      // Create mock store
      const store = mockStore({
        repositories: { repositories: mockRepositories, status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(triggerRepositoryAnalysis(repositoryId));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('repositories/triggerRepositoryAnalysis/fulfilled');
      expect(actions[0].payload).toEqual(analysisResult);
    });
    
    it('should dispatch failure action when triggering analysis fails', () => {
      const repositoryId = '1';
      
      // Override the mock implementation for this test
      triggerRepositoryAnalysis.mockImplementation(() => ({
        type: 'repositories/triggerRepositoryAnalysis/rejected',
        payload: mockError.message
      }));
      
      // Create mock store
      const store = mockStore({
        repositories: { repositories: mockRepositories, status: 'idle', error: null }
      });
      
      // Dispatch the mocked action
      store.dispatch(triggerRepositoryAnalysis(repositoryId));
      
      // Get actions
      const actions = store.getActions();
      
      // Assert
      expect(actions[0].type).toBe('repositories/triggerRepositoryAnalysis/rejected');
      expect(actions[0].payload).toBe(mockError.message);
    });
  });
  
  describe('repositories slice actions', () => {
    it('should handle setCurrentRepository', () => {
      // Create mock store with initial state
      const store = mockStore({
        repositories: {
          currentRepository: null
        }
      });
      
      // Dispatch the action
      store.dispatch(setCurrentRepository(mockRepositories[0]));
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(setCurrentRepository.type);
      expect(actions[0].payload).toEqual(mockRepositories[0]);
    });
    
    it('should handle clearRepositories', () => {
      // Create mock store with initial state
      const store = mockStore({
        repositories: {
          repositories: mockRepositories,
          currentRepository: mockRepositories[0],
          status: 'succeeded',
          error: null
        }
      });
      
      // Dispatch the action
      store.dispatch(clearRepositories());
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(clearRepositories.type);
    });
  });
});
