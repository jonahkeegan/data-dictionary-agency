/**
 * API Hooks
 * Custom hooks for API operations
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { createCancelToken, cancelPendingRequest, isCancel } from '../services/api/cancelToken';

/**
 * Hook for making API calls with loading, error, and result handling
 * @param {Function} apiFunction - Function that returns a promise for the API call
 * @param {Array} dependencies - Array of dependencies for the effect
 * @param {boolean} immediate - Whether to execute the API call immediately
 * @returns {Object} Object with data, loading, error, execute, and reset
 */
export const useApi = (apiFunction, dependencies = [], immediate = false) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Create a request key ref that will be used for cancellation
  const requestKeyRef = useRef(`api-call-${Math.random().toString(36).substring(2, 11)}`);
  
  // Execute API call function
  const execute = useCallback(async (...args) => {
    // Set loading state
    setLoading(true);
    setError(null);
    
    try {
      // Create a cancel token
      const source = createCancelToken(requestKeyRef.current);
      
      // Add the cancel token to the last argument if it's an object,
      // or add it as a new object if the last argument isn't an object
      const lastArg = args.length > 0 ? args[args.length - 1] : undefined;
      
      let newArgs;
      if (lastArg && typeof lastArg === 'object' && !Array.isArray(lastArg)) {
        // Last argument is an object, so add the cancel token to it
        newArgs = [...args.slice(0, -1), { ...lastArg, cancelToken: source.token }];
      } else {
        // Last argument is not an object, so add a new object with the cancel token
        newArgs = [...args, { cancelToken: source.token }];
      }
      
      // Execute the API call
      const response = await apiFunction(...newArgs);
      
      // Set the data
      setData(response);
      
      // Reset loading state
      setLoading(false);
      
      // Return the response for chaining
      return response;
    } catch (error) {
      // Don't set error state for cancelled requests
      if (!isCancel(error)) {
        setError(error);
      }
      
      // Reset loading state
      setLoading(false);
      
      // Re-throw the error for the caller to handle
      throw error;
    }
  }, [apiFunction]);
  
  // Reset the state
  const reset = useCallback(() => {
    setData(null);
    setLoading(false);
    setError(null);
  }, []);
  
  // Effect for immediate execution and cleanup
  useEffect(() => {
    // Only execute immediately if the flag is set
    if (immediate) {
      execute().catch(error => {
        // Ignore cancellation errors
        if (!isCancel(error)) {
          console.error('Error in immediate API execution:', error);
        }
      });
    }
    
    // Cleanup: cancel any pending requests when the dependencies change or the component unmounts
    return () => {
      cancelPendingRequest(requestKeyRef.current);
    };
  }, dependencies); // eslint-disable-line react-hooks/exhaustive-deps
  
  return { data, loading, error, execute, reset };
};

/**
 * Hook for paginated API calls
 * @param {Function} apiFunction - Function that returns a promise for the API call
 * @param {Object} initialParams - Initial parameters for the API call
 * @param {Array} dependencies - Array of dependencies for the effect
 * @returns {Object} Object with data, loading, error, page, goToPage, nextPage, prevPage
 */
export const usePaginatedApi = (apiFunction, initialParams = {}, dependencies = []) => {
  // Default pagination parameters
  const defaultParams = {
    skip: 0,
    limit: 10,
    ...initialParams
  };
  
  // State for data, loading, and error
  const [params, setParams] = useState(defaultParams);
  const [data, setData] = useState(null);
  const [totalItems, setTotalItems] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Calculate current page and total pages
  const page = Math.floor(params.skip / params.limit) + 1;
  const totalPages = Math.ceil(totalItems / params.limit) || 0;
  const hasMore = page < totalPages;
  
  // Effect for fetching data
  useEffect(() => {
    let mounted = true;
    const source = createCancelToken(`paginated-api-${Math.random().toString(36).substring(2, 11)}`);
    
    const fetchData = async () => {
      setLoading(true);
      
      try {
        // Call the API function with the current params
        const response = await apiFunction(params, { cancelToken: source.token });
        
        if (!mounted) return;
        
        // Handle different response formats (array vs. object with items)
        if (Array.isArray(response)) {
          setData(response);
          setTotalItems(Math.max(response.length, params.skip + response.length));
        } else if (response && typeof response === 'object') {
          // Handle response as object with items array
          const items = response.items || response.data || response.results || [];
          const total = response.total || response.totalCount || response.count || items.length;
          
          setData(items);
          setTotalItems(total);
        }
        
        setError(null);
      } catch (error) {
        if (!mounted || isCancel(error)) return;
        
        setError(error);
        setData(null);
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };
    
    fetchData();
    
    return () => {
      mounted = false;
      cancelPendingRequest(source._token);
    };
  }, [apiFunction, params, ...dependencies]); // eslint-disable-line react-hooks/exhaustive-deps
  
  // Navigation functions
  const goToPage = useCallback(
    (pageNumber) => {
      if (pageNumber < 1) pageNumber = 1;
      const newSkip = (pageNumber - 1) * params.limit;
      setParams(prevParams => ({ ...prevParams, skip: newSkip }));
    },
    [params.limit]
  );
  
  const nextPage = useCallback(
    () => {
      if (hasMore) {
        goToPage(page + 1);
      }
    },
    [goToPage, page, hasMore]
  );
  
  const prevPage = useCallback(
    () => {
      if (page > 1) {
        goToPage(page - 1);
      }
    },
    [goToPage, page]
  );
  
  // Update params function
  const updateParams = useCallback(
    (newParams) => {
      setParams(prevParams => ({ ...prevParams, ...newParams, skip: 0 }));
    },
    []
  );
  
  return {
    data,
    loading,
    error,
    page,
    totalPages,
    totalItems,
    hasMore,
    goToPage,
    nextPage,
    prevPage,
    params,
    updateParams
  };
};
