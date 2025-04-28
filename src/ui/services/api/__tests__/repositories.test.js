/**
 * Tests for RepositoryService
 */
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import { createApiClient } from '../client';
import { RepositoryService } from '../repositories';
import ServiceFactory from '../serviceFactory';

// Mock data
const mockRepositories = [
  { id: '1', name: 'Repo 1', url: 'https://github.com/repo1', status: 'active', progress: 100 },
  { id: '2', name: 'Repo 2', url: 'https://github.com/repo2', status: 'pending', progress: 50 },
];

const mockRepository = {
  id: '1',
  name: 'Test Repository',
  description: 'Repository for testing',
  url: 'https://github.com/test-repo',
  status: 'active',
  progress: 100,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-02T00:00:00Z'
};

const mockAnalysisResult = {
  id: 'analysis-1',
  status: 'in_progress',
  progress: 25
};

describe('RepositoryService', () => {
  let mock;
  let apiClient;
  let repositoryService;
  
  beforeEach(() => {
    // Reset the ServiceFactory singleton for clean tests
    ServiceFactory.resetInstance();
    
    // Create a fresh API client for each test
    apiClient = createApiClient();
    
    // Create a mock adapter for the axios instance
    mock = new MockAdapter(apiClient);
    
    // Create repository service with the mocked client
    repositoryService = new RepositoryService(apiClient);
  });
  
  afterEach(() => {
    // Restore the axios instance
    mock.restore();
  });
  
  describe('getAll', () => {
    it('should fetch repositories with default parameters', async () => {
      // Setup mock response
      mock.onGet('/repositories').reply(200, mockRepositories);
      
      // Call the service method
      const result = await repositoryService.getAll();
      
      // Verify the result
      expect(result).toEqual(mockRepositories);
      
      // Verify the request
      expect(mock.history.get.length).toBe(1);
      expect(mock.history.get[0].url).toBe('/repositories');
    });
    
    it('should fetch repositories with custom parameters', async () => {
      // Setup mock response
      mock.onGet('/repositories').reply(200, mockRepositories);
      
      // Call the service method
      const result = await repositoryService.getAll({
        skip: 10,
        limit: 5,
        sort: 'name',
        order: 'asc'
      });
      
      // Verify the request
      expect(mock.history.get.length).toBe(1);
      expect(mock.history.get[0].params).toEqual({
        skip: 10,
        limit: 5,
        sort: 'name',
        order: 'asc'
      });
    });
    
    it('should handle error response', async () => {
      // Setup mock response
      mock.onGet('/repositories').reply(500, {
        error: {
          message: 'Internal server error'
        }
      });
      
      // Expect the method to throw
      await expect(repositoryService.getAll()).rejects.toThrow();
    });
  });
  
  describe('getById', () => {
    it('should fetch a repository by ID', async () => {
      // Setup mock response
      mock.onGet('/repositories/1').reply(200, mockRepository);
      
      // Call the service method
      const result = await repositoryService.getById('1');
      
      // Verify the result
      expect(result).toEqual(mockRepository);
      
      // Verify the request
      expect(mock.history.get.length).toBe(1);
      expect(mock.history.get[0].url).toBe('/repositories/1');
    });
    
    it('should handle error response', async () => {
      // Setup mock response
      mock.onGet('/repositories/999').reply(404, {
        error: {
          message: 'Repository not found'
        }
      });
      
      // Expect the method to throw
      await expect(repositoryService.getById('999')).rejects.toThrow();
    });
  });
  
  describe('create', () => {
    it('should create a repository', async () => {
      const newRepo = {
        name: 'New Repository',
        description: 'A new repository',
        url: 'https://github.com/new-repo'
      };
      
      // Setup mock response
      mock.onPost('/repositories').reply(201, {
        ...newRepo,
        id: '3'
      });
      
      // Call the service method
      const result = await repositoryService.create(newRepo);
      
      // Verify the result
      expect(result).toEqual({
        ...newRepo,
        id: '3'
      });
      
      // Verify the request
      expect(mock.history.post.length).toBe(1);
      expect(mock.history.post[0].url).toBe('/repositories');
      expect(JSON.parse(mock.history.post[0].data)).toEqual(newRepo);
    });
  });
  
  describe('delete', () => {
    it('should delete a repository by ID', async () => {
      // Setup mock response
      mock.onDelete('/repositories/1').reply(204);
      
      // Call the service method
      const result = await repositoryService.delete('1');
      
      // Verify the result
      expect(result).toBe(true);
      
      // Verify the request
      expect(mock.history.delete.length).toBe(1);
      expect(mock.history.delete[0].url).toBe('/repositories/1');
    });
  });
  
  describe('triggerAnalysis', () => {
    it('should trigger analysis for a repository', async () => {
      // Setup mock response
      mock.onPost('/repositories/1/analyze').reply(200, mockAnalysisResult);
      
      // Call the service method
      const result = await repositoryService.triggerAnalysis('1');
      
      // Verify the result
      expect(result).toEqual(mockAnalysisResult);
      
      // Verify the request
      expect(mock.history.post.length).toBe(1);
      expect(mock.history.post[0].url).toBe('/repositories/1/analyze');
    });
  });
  
  describe('caching', () => {
    it('should cache results and reuse them', async () => {
      // Setup mock response
      mock.onGet('/repositories').reply(200, mockRepositories);
      
      // Call the service method twice
      const result1 = await repositoryService.getAll();
      const result2 = await repositoryService.getAll();
      
      // Verify both results are equal
      expect(result1).toEqual(mockRepositories);
      expect(result2).toEqual(mockRepositories);
      
      // Verify only one request was made
      expect(mock.history.get.length).toBe(1);
    });
    
    it('should invalidate cache on write operations', async () => {
      // Setup mock responses
      mock.onGet('/repositories').reply(200, mockRepositories);
      mock.onPost('/repositories').reply(201, { id: '3', name: 'New Repo' });
      
      // Call getAll to cache the initial results
      const initialResult = await repositoryService.getAll();
      expect(initialResult).toEqual(mockRepositories);
      expect(mock.history.get.length).toBe(1);
      
      // Call create which should invalidate the cache
      await repositoryService.create({ name: 'New Repo' });
      
      // Reset history to clear the previous GET request
      mock.resetHistory();
      
      // Mock updated repository list
      const updatedRepositories = [
        ...mockRepositories,
        { id: '3', name: 'New Repo' }
      ];
      mock.onGet('/repositories').reply(200, updatedRepositories);
      
      // Call getAll again, which should make a new request
      const newResult = await repositoryService.getAll();
      
      // Verify a new request was made (cache was invalidated)
      expect(mock.history.get.length).toBe(1);
      expect(newResult).toEqual(updatedRepositories);
    });
    
    it('should bypass cache when useCache option is false', async () => {
      // Setup mock response
      mock.onGet('/repositories').reply(200, mockRepositories);
      
      // Call the service method with cache
      await repositoryService.getAll();
      
      // Then call with useCache: false
      await repositoryService.getAll({}, { useCache: false });
      
      // Verify two requests were made
      expect(mock.history.get.length).toBe(2);
    });
    
    it('should use custom ttl when provided', async () => {
      jest.useFakeTimers();
      
      // Setup mock response
      mock.onGet('/repositories').reply(200, mockRepositories);
      
      // Call with short TTL - 1 second
      await repositoryService.getAll({}, { ttl: 1 });
      
      // First call should be cached
      await repositoryService.getAll();
      expect(mock.history.get.length).toBe(1);
      
      // Advance time by 1.5 seconds (past the TTL)
      jest.advanceTimersByTime(1500);
      
      // Call again - should make a new request
      await repositoryService.getAll();
      expect(mock.history.get.length).toBe(2);
      
      jest.useRealTimers();
    });
  });
  
  describe('circuit breaker', () => {
    it('should open circuit after multiple failures', async () => {
      // Mock failing responses
      mock.onGet('/repositories').reply(500);
      
      // Setup spy on console.warn
      const warnSpy = jest.spyOn(console, 'warn').mockImplementation();
      
      // Call multiple times to trigger circuit breaker
      try { await repositoryService.getAll(); } catch (e) {}
      try { await repositoryService.getAll(); } catch (e) {}
      try { await repositoryService.getAll(); } catch (e) {}
      try { await repositoryService.getAll(); } catch (e) {}
      
      // Verify circuit breaker warning was logged
      expect(warnSpy).toHaveBeenCalledWith(expect.stringContaining('Circuit opened'));
      
      warnSpy.mockRestore();
    });
  });
});
