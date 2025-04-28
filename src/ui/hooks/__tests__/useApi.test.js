/**
 * Tests for useApi hook
 */
import { renderHook, act } from '@testing-library/react-hooks';
import { useApi, usePaginatedApi } from '../useApi';
import { isCancel } from '../../services/api/cancelToken'; 

// Mock the cancelToken module
jest.mock('../../services/api/cancelToken', () => ({
  isCancel: jest.fn()
}));

describe('useApi', () => {
  // Reset mocks before each test
  beforeEach(() => {
    isCancel.mockReset();
    isCancel.mockReturnValue(false);
  });
  
  it('should return initial state correctly', () => {
    // Create mock API function
    const mockApiFunction = jest.fn();
    
    // Render the hook
    const { result } = renderHook(() => useApi(mockApiFunction));
    
    // Verify initial state
    expect(result.current).toEqual({
      data: null,
      loading: false,
      error: null,
      execute: expect.any(Function),
      reset: expect.any(Function)
    });
    
    // Verify API function was not called
    expect(mockApiFunction).not.toHaveBeenCalled();
  });
  
  it('should execute API function when immediate is true', () => {
    // Create mock API function that resolves with data
    const mockData = { id: '1', name: 'Test' };
    const mockApiFunction = jest.fn().mockResolvedValue(mockData);
    
    // Render the hook with immediate=true
    const { result } = renderHook(() => useApi(mockApiFunction, [], true));
    
    // Verify loading state
    expect(result.current.loading).toBe(true);
    
    // Verify API function was called
    expect(mockApiFunction).toHaveBeenCalledTimes(1);
  });
  
  it('should update state when API function resolves', async () => {
    // Create mock API function that resolves with data
    const mockData = { id: '1', name: 'Test' };
    const mockApiFunction = jest.fn().mockResolvedValue(mockData);
    
    // Render the hook
    const { result, waitForNextUpdate } = renderHook(() => 
      useApi(mockApiFunction, [], true)
    );
    
    // Wait for API call to resolve
    await waitForNextUpdate();
    
    // Verify state after resolution
    expect(result.current).toEqual({
      data: mockData,
      loading: false,
      error: null,
      execute: expect.any(Function),
      reset: expect.any(Function)
    });
  });
  
  it('should update state when API function rejects', async () => {
    // Create error object
    const mockError = new Error('API Error');
    
    // Create mock API function that rejects
    const mockApiFunction = jest.fn().mockRejectedValue(mockError);
    
    // Render the hook
    const { result, waitForNextUpdate } = renderHook(() => 
      useApi(mockApiFunction, [], true)
    );
    
    // Wait for API call to reject
    await waitForNextUpdate();
    
    // Verify state after rejection
    expect(result.current).toEqual({
      data: null,
      loading: false,
      error: mockError,
      execute: expect.any(Function),
      reset: expect.any(Function)
    });
  });
  
  it('should execute API function with parameters when execute is called', async () => {
    // Create mock API function
    const mockData = { id: '1', name: 'Test' };
    const mockApiFunction = jest.fn().mockResolvedValue(mockData);
    
    // Render the hook
    const { result, waitForNextUpdate } = renderHook(() => 
      useApi(mockApiFunction)
    );
    
    // Call execute with parameters
    const params = { id: '1' };
    act(() => {
      result.current.execute(params);
    });
    
    // Verify loading state
    expect(result.current.loading).toBe(true);
    
    // Verify API function was called with parameters
    expect(mockApiFunction).toHaveBeenCalledWith(params);
    
    // Wait for API call to resolve
    await waitForNextUpdate();
    
    // Verify state after resolution
    expect(result.current).toEqual({
      data: mockData,
      loading: false,
      error: null,
      execute: expect.any(Function),
      reset: expect.any(Function)
    });
  });
  
  it('should not update error state on cancellation', async () => {
    // Create cancel error
    const mockCancelError = new Error('Request canceled');
    
    // Mock isCancel to return true for this error
    isCancel.mockImplementation((error) => error === mockCancelError);
    
    // Create mock API function that rejects with cancel error
    const mockApiFunction = jest.fn().mockRejectedValue(mockCancelError);
    
    // Render the hook
    const { result, waitForNextUpdate } = renderHook(() => 
      useApi(mockApiFunction, [], true)
    );
    
    // Call execute to trigger a rejection
    await act(async () => {
      try {
        await result.current.execute();
      } catch (e) {
        // Catch the rejection
      }
    });
    
    // Verify state - should still be loading because cancellations are ignored
    expect(result.current.loading).toBe(true);
    expect(result.current.error).toBe(null);
  });
  
  it('should reset state when reset is called', async () => {
    // Create mock API function that resolves with data
    const mockData = { id: '1', name: 'Test' };
    const mockApiFunction = jest.fn().mockResolvedValue(mockData);
    
    // Render the hook
    const { result, waitForNextUpdate } = renderHook(() => 
      useApi(mockApiFunction, [], true)
    );
    
    // Wait for API call to resolve
    await waitForNextUpdate();
    
    // Verify state has data
    expect(result.current.data).toEqual(mockData);
    
    // Call reset
    act(() => {
      result.current.reset();
    });
    
    // Verify state is reset
    expect(result.current).toEqual({
      data: null,
      loading: false,
      error: null,
      execute: expect.any(Function),
      reset: expect.any(Function)
    });
  });
});

describe('usePaginatedApi', () => {
  it('should return initial paginated state correctly', () => {
    // Create mock API function
    const mockData = [{ id: '1' }, { id: '2' }];
    const mockApiFunction = jest.fn().mockResolvedValue(mockData);
    
    // Render the hook
    const { result } = renderHook(() => usePaginatedApi(mockApiFunction));
    
    // Verify initial state
    expect(result.current).toEqual({
      data: null,
      loading: true,
      error: null,
      page: 1,
      totalPages: 1,
      totalItems: 0,
      hasMore: false,
      nextPage: expect.any(Function),
      prevPage: expect.any(Function),
      goToPage: expect.any(Function),
      refresh: expect.any(Function),
      params: {
        skip: 0,
        limit: 10
      }
    });
    
    // Verify API function was called with default params
    expect(mockApiFunction).toHaveBeenCalledTimes(1);
    expect(mockApiFunction).toHaveBeenCalledWith({
      skip: 0,
      limit: 10
    });
  });
  
  it('should handle array responses', async () => {
    // Create mock API function that returns an array
    const mockData = [{ id: '1' }, { id: '2' }];
    const mockApiFunction = jest.fn().mockResolvedValue(mockData);
    
    // Render the hook
    const { result, waitForNextUpdate } = renderHook(() => 
      usePaginatedApi(mockApiFunction)
    );
    
    // Wait for API call to resolve
    await waitForNextUpdate();
    
    // Verify state includes the array data
    expect(result.current.data).toEqual(mockData);
    
    // Verify pagination state is updated
    expect(result.current.totalItems).toBeGreaterThan(0);
  });
  
  it('should handle pagination controls correctly', async () => {
    // Create mock data for different pages
    const page1Data = Array.from({ length: 10 }, (_, i) => ({ id: String(i + 1) }));
    const page2Data = Array.from({ length: 10 }, (_, i) => ({ id: String(i + 11) }));
    
    // Create mock API function
    const mockApiFunction = jest.fn()
      .mockImplementation(params => {
        // Return different data based on skip value
        if (params.skip === 0) {
          return Promise.resolve(page1Data);
        } else {
          return Promise.resolve(page2Data);
        }
      });
    
    // Render the hook
    const { result, waitForNextUpdate } = renderHook(() => 
      usePaginatedApi(mockApiFunction)
    );
    
    // Wait for initial API call to resolve
    await waitForNextUpdate();
    
    // Verify first page data
    expect(result.current.data).toEqual(page1Data);
    expect(result.current.page).toBe(1);
    
    // Go to next page
    act(() => {
      result.current.nextPage();
    });
    
    // Verify loading state
    expect(result.current.loading).toBe(true);
    
    // Wait for second API call to resolve
    await waitForNextUpdate();
    
    // Verify second page data
    expect(result.current.data).toEqual(page2Data);
    expect(result.current.page).toBe(2);
    expect(result.current.params.skip).toBe(10);
    
    // Go back to previous page
    act(() => {
      result.current.prevPage();
    });
    
    // Wait for API call to resolve
    await waitForNextUpdate();
    
    // Verify back to first page
    expect(result.current.page).toBe(1);
    expect(result.current.params.skip).toBe(0);
  });
});
