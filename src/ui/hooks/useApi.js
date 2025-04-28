/**
 * Custom hooks for API integration
 * Simplifies component-level API interactions
 */
import { useState, useEffect, useCallback } from 'react';
import { useDispatch } from 'react-redux';
import { isCancel } from '../services/api/cancelToken';

/**
 * Custom hook for API calls with automatic handling of loading states and cleanup
 * 
 * @template T
 * @param {Function} apiFunction - Function that returns a Promise (typically a service method)
 * @param {Array} [dependencies=[]] - Dependencies array for useEffect/useCallback
 * @param {boolean} [immediate=false] - Whether to execute immediately
 * @returns {Object} Hook state and controls
 * @property {T|null} data - Response data
 * @property {boolean} loading - Whether request is in progress
 * @property {Error|null} error - Error if request failed
 * @property {Function} execute - Function to execute the request
 * @property {Function} reset - Function to reset state
 */
export const useApi = (apiFunction, dependencies = [], immediate = false) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState(null);
  
  // Memoize execute function
  const execute = useCallback((...args) => {
    setLoading(true);
    setError(null);
    
    return apiFunction(...args)
      .then(response => {
        setData(response);
        setLoading(false);
        return response;
      })
      .catch(err => {
        // Ignore cancellations
        if (!isCancel(err)) {
          setError(err);
          setLoading(false);
        }
        throw err; // Re-throw to allow further handling if needed
      });
  }, [apiFunction, ...dependencies]);
  
  // Reset state
  const reset = useCallback(() => {
    setData(null);
    setLoading(false);
    setError(null);
  }, []);
  
  // Execute immediately if requested
  useEffect(() => {
    if (immediate) {
      execute().catch(() => {}); // Catch to prevent unhandled rejection
    }
    
    // No cleanup needed for immediate execution
  }, [execute, immediate]);
  return { data, loading, error, execute, reset };
};

/**
 * Custom hook for paginated API calls
 * 
 * @template T
 * @param {Function} apiFunction - Function that returns a Promise (typically a service method)
 * @param {Object} [initialParams={}] - Initial pagination parameters
 * @returns {Object} Hook state and controls
 * @property {T[]|null} data - Response data (items array)
 * @property {boolean} loading - Whether request is in progress
 * @property {Error|null} error - Error if request failed
 * @property {number} page - Current page number (1-based)
 * @property {number} totalPages - Total number of pages
 * @property {number} totalItems - Total number of items
 * @property {boolean} hasMore - Whether there are more pages
 * @property {Function} nextPage - Function to go to next page
 * @property {Function} prevPage - Function to go to previous page
 * @property {Function} goToPage - Function to go to specific page
 * @property {Function} refresh - Function to refresh current page
 */
export const usePaginatedApi = (apiFunction, initialParams = {}) => {

  // Default pagination parameters
  const defaultParams = {
    skip: 0,
    limit: 10,
    ...initialParams
  };
  
  const [params, setParams] = useState(defaultParams);
  const [totalItems, setTotalItems] = useState(0);
  const [page, setPage] = useState(1);
  
  // Calculate total pages based on total items and limit
  const totalPages = Math.max(1, Math.ceil(totalItems / params.limit));
  const hasMore = page < totalPages;
  
  // Use the base hook
  const { data, loading, error, execute } = useApi(
    useCallback((queryParams = {}) => {
      return apiFunction({
        ...params,
        ...queryParams
      });
    }, [apiFunction, params]),
    [params], // Re-execute when params change
    true // Execute immediately
  );
  
  // Update total items when data changes
  useEffect(() => {
    if (data) {
      // Handle both array responses and wrapped responses
      if (Array.isArray(data)) {
        setTotalItems(Math.max(
          totalItems, 
          params.skip + data.length + (data.length === params.limit ? 1 : 0)
        ));
      } else if (data.items && Array.isArray(data.items)) {
        setTotalItems(data.total || data.items.length);
      }
    }
  }, [data, params.limit, params.skip, totalItems]);
  
  // Pagination controls
  const nextPage = useCallback(() => {
    if (hasMore) {
      setPage(p => p + 1);
      setParams(p => ({
        ...p,
        skip: p.skip + p.limit
      }));
    }
  }, [hasMore, params.limit]);
  
  const prevPage = useCallback(() => {
    if (page > 1) {
      setPage(p => p - 1);
      setParams(p => ({
        ...p,
        skip: Math.max(0, p.skip - p.limit)
      }));
    }
  }, [page, params.limit]);
  
  const goToPage = useCallback((pageNumber) => {
    const validPage = Math.max(1, Math.min(pageNumber, totalPages));
    setPage(validPage);
    setParams(p => ({
      ...p,
      skip: (validPage - 1) * p.limit
    }));
  }, [totalPages, params.limit]);
  
  // Refresh current page
  const refresh = useCallback(() => {
    execute();
  }, [execute]);
  
  // Extract items from response
  const items = data ? 
    (Array.isArray(data) ? data : (data.items || data)) :
    null;
    
  return {
    data: items,
    loading,
    error,
    page,
    totalPages,
    totalItems,
    hasMore,
    nextPage,
    prevPage,
    goToPage,
    refresh,
    params
  };
};

/**
 * Custom hook for repository operations
 * 
 * @param {string} [repositoryId] - Repository ID for specific operations
 * @param {boolean} [immediate=true] - Whether to fetch immediately
 * @returns {Object} Repository operations and state
 */
export const useRepositories = (repositoryId, immediate = true) => {
  const dispatch = useDispatch();
  
  // Import at hook level to prevent circular dependencies
  const { serviceFactory } = require('../services/api/serviceFactory');
  const repositoryService = serviceFactory.getRepositoryService();
  const { fetchRepositories, fetchRepositoryById } = require('../store/slices/repositoriesSlice');
  
  // Get all repositories
  const allRepositories = useApi(
    useCallback((params = {}) => {
      if (repositoryId) {
        return repositoryService.getById(repositoryId);
      } else {
        return dispatch(fetchRepositories(params)).unwrap();
      }
    }, [dispatch, repositoryId, repositoryService]),
    [repositoryId], // Re-execute when repository ID changes
    immediate
  );
  
  // Combine results based on whether a specific ID was requested
  return {
    repositories: !repositoryId ? allRepositories.data : null,
    repository: repositoryId ? allRepositories.data : null,
    loading: allRepositories.loading,
    error: allRepositories.error,
    fetchRepositories: allRepositories.execute
  };
};

/**
 * Custom hook for schema operations
 * 
 * @param {Object} [params={}] - Query parameters
 * @param {string} [params.repository_id] - Repository ID to filter by
 * @param {string} [params.format_id] - Format ID to filter by
 * @param {boolean} [immediate=true] - Whether to fetch immediately
 * @returns {Object} Schema operations and state
 */
export const useSchemas = (params = {}, immediate = true) => {
  // Import at hook level to prevent circular dependencies
  const { serviceFactory } = require('../services/api/serviceFactory');
  const schemaService = serviceFactory.getSchemaService();
  
  // Get schemas with parameters
  const schemas = useApi(
    useCallback((queryParams = {}) => {
      return schemaService.getAll({
        ...params,
        ...queryParams
      });
    }, [params, schemaService]),
    [params], // Re-execute when params change
    immediate
  );
  
  // Get a specific schema by ID
  const getSchema = useCallback((id) => {
    return schemaService.getById(id);
  }, [schemaService]);
  
  // Get relationships for a schema
  const getRelationships = useCallback((id) => {
    return schemaService.getRelationships(id);
  }, [schemaService]);
  
  return {
    schemas: schemas.data,
    loading: schemas.loading,
    error: schemas.error,
    fetchSchemas: schemas.execute,
    getSchema,
    getRelationships
  };
};

/**
 * Custom hook for format operations
 * 
 * @param {boolean} [immediate=true] - Whether to fetch immediately
 * @returns {Object} Format operations and state
 */
export const useFormats = (immediate = true) => {
  // Import at hook level to prevent circular dependencies
  const { serviceFactory } = require('../services/api/serviceFactory');
  const formatService = serviceFactory.getFormatService();
  
  // Get all formats
  const formats = useApi(
    useCallback((params = {}) => {
      return formatService.getAll(params);
    }, [formatService]),
    [],
    immediate
  );
  
  // Get supported formats
  const supportedFormats = useApi(
    useCallback(() => {
      return formatService.getSupportedFormats();
    }, [formatService]),
    [],
    immediate
  );
  
  // Validate a schema against a format
  const validateSchema = useCallback((formatId, schema) => {
    return formatService.validateSchema(formatId, schema);
  }, [formatService]);
  
  return {
    formats: formats.data,
    loading: formats.loading,
    error: formats.error,
    supportedFormats: supportedFormats.data,
    validateSchema
  };
};

/**
 * Custom hook for authentication operations
 * 
 * @param {boolean} [checkAuth=true] - Whether to check authentication status immediately
 * @returns {Object} Auth operations and state
 */
export const useAuth = (checkAuth = true) => {
  // State for authenticated status
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
  // Import at hook level to prevent circular dependencies
  const { serviceFactory } = require('../services/api/serviceFactory');
  const authService = serviceFactory.getAuthService();
  
  // Check authentication on mount if requested
  useEffect(() => {
    if (checkAuth) {
      setIsAuthenticated(authService.isAuthenticated());
    }
  }, [authService, checkAuth]);
  
  // Get current user
  const currentUser = useApi(
    useCallback(() => {
      if (isAuthenticated) {
        return authService.getCurrentUser();
      }
      return Promise.resolve(null);
    }, [authService, isAuthenticated]),
    [isAuthenticated],
    isAuthenticated && checkAuth
  );
  
  // Login function
  const login = useCallback(async (credentials) => {
    try {
      const result = await authService.login(credentials);
      setIsAuthenticated(true);
      return result;
    } catch (error) {
      setIsAuthenticated(false);
      throw error;
    }
  }, [authService]);
  
  // Logout function
  const logout = useCallback(async () => {
    try {
      await authService.logout();
      setIsAuthenticated(false);
      return true;
    } catch (error) {
      // Still consider logged out even if API call fails
      setIsAuthenticated(false);
      throw error;
    }
  }, [authService]);
  
  // Register function
  const register = useCallback(async (userData) => {
    try {
      const result = await authService.register(userData);
      setIsAuthenticated(true);
      return result;
    } catch (error) {
      setIsAuthenticated(false);
      throw error;
    }
  }, [authService]);
  
  // Refresh token function
  const refreshToken = useCallback(async () => {
    try {
      const result = await authService.refreshToken();
      setIsAuthenticated(true);
      return result;
    } catch (error) {
      setIsAuthenticated(false);
      throw error;
    }
  }, [authService]);
  
  return {
    isAuthenticated,
    user: currentUser.data,
    userLoading: currentUser.loading,
    userError: currentUser.error,
    login,
    logout,
    register,
    refreshToken
  };
};
