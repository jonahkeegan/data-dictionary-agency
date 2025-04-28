# Service Layer Architecture

This document provides a comprehensive overview of the Service Layer architecture for the Data Dictionary Agency frontend.

## Overview

The Service Layer acts as an abstraction between the frontend application and the backend API, providing:

- Type-safe, consistent interfaces for all API operations
- Centralized error handling and transformation
- Advanced caching with TTL and invalidation patterns
- Circuit breaker pattern for resilience against API failures
- Request cancellation support
- Mock service implementations for development and testing
- Integration with Redux state management

## Architecture Diagram

```mermaid
flowchart TD
    subgraph Frontend Components
        UI[UI Components]
        Hooks[Custom Hooks]
        Redux[Redux Store]
    end
    
    subgraph Service Layer
        Factory[Service Factory]
        Base[Base Service]
        
        subgraph Domain Services
            RS[Repository Service]
            SS[Schema Service] 
            FS[Format Service]
            AS[Auth Service]
        end
        
        subgraph Utilities
            ErrorHandler[Error Handler]
            CacheManager[Cache Manager]
            CircuitBreaker[Circuit Breaker]
            CancelToken[Request Cancellation]
        end
    end
    
    subgraph Backend Integration
        Client[API Client]
        Interceptors[Request/Response Interceptors]
        
        subgraph Mock Services
            MockFactory[Mock Service Factory]
            MockData[Mock Data Store]
        end
    end
    
    UI --> Hooks
    Hooks --> Redux
    Hooks --> Factory
    Redux --> Domain Services
    
    Factory --> Base
    Factory --> Domain Services
    Factory -.-> MockFactory
    
    Base --> ErrorHandler
    Base --> CacheManager
    Base --> CircuitBreaker
    Base --> CancelToken
    
    Domain Services --> Client
    Client --> Interceptors
    
    MockFactory --> MockData
```

## Component Responsibilities

### Service Factory

The `ServiceFactory` is the entry point to the Service Layer, providing:

- Singleton instances of each domain service
- Automatic switching between real and mock services
- Consistent service instantiation and configuration

```javascript
// Example usage
import { serviceFactory } from '../services/api/serviceFactory';

// Get service instances
const repositoryService = serviceFactory.getRepositoryService();
const schemaService = serviceFactory.getSchemaService();
const formatService = serviceFactory.getFormatService();
const authService = serviceFactory.getAuthService();
```

### Base Service

The `BaseService` class provides common functionality for all services:

- Error handling and standardization
- Cache management with TTL and invalidation
- Circuit breaker pattern for resilience
- Request cancellation support
- Retry mechanisms for transient failures

```javascript
// BaseService implements these methods:
service.cachedGet(endpoint, params, options);
service.executePost(endpoint, data, options, invalidatePattern);
service.executePut(endpoint, data, options, invalidatePattern);
service.executeDelete(endpoint, options, invalidatePattern);
service.clearCache(pattern);
service.withCircuitBreaker(requestFn, fallbackFn, options);
service.retryRequest(requestFn, maxRetries);
```

### Cache Manager

The Cache Manager provides intelligent caching:

- In-memory cache with TTL (Time-To-Live)
- Size-based cache eviction (LRU-like)
- Pattern-based cache invalidation
- Deduplication of in-flight requests
- Metrics collection for cache performance
- Protection against cache entry size explosion

### Circuit Breaker

The Circuit Breaker prevents cascading failures:

- Tracks failure counts per endpoint
- Opens circuit after threshold is exceeded
- Automatically resets after cool-down period
- Allows fallback mechanisms when circuit is open
- Provides circuit state inspection

### Domain Services

Each domain service provides type-safe methods for API endpoints:

#### Repository Service

```javascript
// Repository service methods
repositoryService.getAll(params, options);        // GET /repositories
repositoryService.getById(id, options);           // GET /repositories/:id
repositoryService.create(data, options);          // POST /repositories
repositoryService.delete(id, options);            // DELETE /repositories/:id
repositoryService.triggerAnalysis(id, options);   // POST /repositories/:id/analyze
```

#### Schema Service

```javascript
// Schema service methods
schemaService.getAll(params, options);            // GET /schemas
schemaService.getById(id, options);               // GET /schemas/:id
schemaService.getByRepository(repoId, options);   // GET /repositories/:id/schemas
schemaService.getRelationships(id, options);      // GET /schemas/:id/relationships
schemaService.createSchema(data, options);        // POST /schemas
schemaService.updateSchema(id, data, options);    // PUT /schemas/:id
schemaService.validateSchema(id, options);        // POST /schemas/:id/validate
```

#### Format Service

```javascript
// Format service methods  
formatService.getAll(params, options);            // GET /formats
formatService.getById(id, options);               // GET /formats/:id
formatService.getSupportedFormats(options);       // GET /formats/supported
formatService.validateSchema(formatId, schema);   // POST /formats/:id/validate
```

#### Auth Service

```javascript
// Auth service methods
authService.login(credentials);                   // POST /auth/login
authService.logout();                             // POST /auth/logout
authService.register(userData);                   // POST /auth/register
authService.getCurrentUser();                     // GET /auth/me
authService.refreshToken();                       // POST /auth/refresh
authService.isAuthenticated();                    // Check if authenticated
```

## Type System

The Service Layer uses TypeScript interfaces to define:

### Domain Models

```typescript
// Example type definitions
export interface Repository {
  id: string;
  name: string;
  description: string;
  url: string;
  status: RepositoryStatus;
  progress: number;
  created_at: string;
  updated_at: string;
}

export interface Schema {
  id: string;
  repository_id: string;
  name: string;
  description: string;
  format_id: string;
  content: any;
  created_at: string;
  updated_at: string;
}

export interface Format {
  id: string;
  name: string;
  description: string;
  version: string;
  detection_patterns: string[];
  supports_validation: boolean;
}

export interface User {
  id: string;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  roles: string[];
  created_at: string;
}
```

### Request/Response Types

```typescript
// Example request parameters
export interface RepositoryParams {
  skip?: number;
  limit?: number;
  sort?: string;
  order?: 'asc' | 'desc';
}

export interface SchemaParams extends RepositoryParams {
  repository_id?: string;
  format_id?: string;
}

// Example request bodies
export interface RepositoryData {
  name: string;
  description: string;
  url: string;
}

export interface AuthCredentials {
  username: string;
  password: string;
}
```

### Error Types

```typescript
export interface ApiError extends Error {
  status: number;
  code: string;
  errors?: Array<{
    field?: string;
    message: string;
    code?: string;
  }>;
  isNetworkError: boolean;
  isServerError: boolean;
  isClientError: boolean;
  isAuthError: boolean;
  original?: any;
}
```

## Integration with React Components

### Custom Hooks

The Service Layer provides custom React hooks for simplified component integration:

#### Redux Action Hooks

```javascript
// Base action hooks
import { useReduxAction, useReduxThunk } from './hooks/useReduxAction';

// Use a regular action
const setCurrentRepo = useReduxAction(setCurrentRepository);
setCurrentRepo(repository); // Dispatches the action

// Use an async thunk
const fetchRepos = useReduxThunk(fetchRepositories);
fetchRepos({ limit: 10 }); // Dispatches the thunk with parameters
```

#### Domain-Specific Hooks

```javascript
// Repository hooks
import { useRepositories, useRepository } from './hooks/useRepositories';

// Get all repositories
const {
  repositories,       // Array of repositories
  currentRepository,  // Currently selected repository
  status,             // 'idle' | 'loading' | 'succeeded' | 'failed'
  isLoading,          // Boolean shorthand for status === 'loading'
  isSuccess,          // Boolean shorthand for status === 'succeeded'
  isError,            // Boolean shorthand for status === 'failed'
  error,              // Error message if status === 'failed'
  
  // Actions
  fetch,              // Fetch all repositories
  fetchById,          // Fetch a repository by ID
  create,             // Create a new repository
  delete,             // Delete a repository
  triggerAnalysis,    // Trigger analysis for a repository
  setCurrent,         // Set current repository
  clear,              // Clear repositories state
  refresh,            // Refresh repositories
  
  // Helpers
  getRepositoryById,  // Get a repository by ID from the local cache
} = useRepositories({ loadImmediately: true });

// Get a specific repository
const {
  repository,         // The specific repository
  isLoading,          // Loading state
  isSuccess,          // Success state
  isError,            // Error state
  error,              // Error message
  
  // Actions
  triggerAnalysis,    // Trigger analysis for this repository
  delete,             // Delete this repository
  refresh,            // Refresh this repository
} = useRepository(repoId, { loadImmediately: true });

// Schema hooks
import { useSchemas, useSchema, useSchemasByRepository } from './hooks/useSchemas';

// Get all schemas
const { schemas, filteredSchemas, currentSchema, /* ... */ } = useSchemas();

// Get a specific schema
const { schema, update, delete, export, /* ... */ } = useSchema(schemaId);

// Get schemas for a repository
const { schemas, create, /* ... */ } = useSchemasByRepository(repoId);

// Relationship hooks
import { 
  useRelationships, 
  useRelationship, 
  useRelationshipsByRepository, 
  useRelationshipsBySchema 
} from './hooks/useRelationships';

// Format hooks
import { useFormats, useFormat, useFormatDetector } from './hooks/useFormats';

// Format detector example
const { 
  detectFormatFromPath,
  getFormatByMimeType,
  getFormatByExtension 
} = useFormatDetector();

const fileFormat = detectFormatFromPath('schema.json');
```

### Redux Integration

The Service Layer integrates with Redux via async thunks and dedicated slices:

```javascript
// Redux slice with thunks for repositories
const repositoriesSlice = createSlice({
  name: 'repositories',
  initialState: {
    repositories: [],
    currentRepository: null,
    status: 'idle', // 'idle' | 'loading' | 'succeeded' | 'failed'
    error: null,
  },
  reducers: {
    setCurrentRepository: (state, action) => {
      state.currentRepository = action.payload;
    },
    clearRepositories: (state) => {
      state.repositories = [];
      state.currentRepository = null;
      state.status = 'idle';
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch repositories
      .addCase(fetchRepositories.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchRepositories.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.repositories = action.payload;
        state.error = null;
      })
      .addCase(fetchRepositories.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      })
      // Additional cases for other thunks...
  }
});

// Thunk implementation
export const fetchRepositories = createAsyncThunk(
  'repositories/fetchRepositories',
  async (params = {}, { rejectWithValue }) => {
    try {
      return await retryRequest(() => repositoryService.getAll(params));
    } catch (error) {
      return rejectWithValue(error.message || 'Failed to fetch repositories');
    }
  }
);

// Similar slices exist for:
// - schemasSlice
// - relationshipsSlice 
// - formatsSlice
// - authSlice
// - uiSlice
```

## Error Handling Strategy

The Service Layer provides consistent error handling:

1. **Standardization**: All errors are converted to a consistent format
2. **Classification**: Errors are classified by type (network, server, client, auth)
3. **Retry Logic**: Transient errors can be automatically retried
4. **Circuit Breaking**: Repeated failures trigger circuit breaking to prevent cascading failures
5. **Component Integration**: Error states propagate consistently to components

```javascript
try {
  await repositoryService.getById('invalid-id');
} catch (error) {
  // Standardized error properties
  console.log(error.status);       // HTTP status code
  console.log(error.message);      // Human-readable message
  console.log(error.code);         // Error code 
  console.log(error.errors);       // Detailed validation errors

  // Error classification
  if (error.isNetworkError) {
    // Handle offline state
  } else if (error.isAuthError) {
    // Handle authentication errors
  } else if (error.isServerError) {
    // Handle server errors
  } else if (error.isClientError) {
    // Handle client errors
  }
}
```

## Caching Strategy

The Service Layer implements an intelligent caching system:

1. **TTL-based caching**: Responses are cached with configurable TTL
2. **Pattern-based invalidation**: Cache entries are invalidated by patterns when data changes
3. **Size limiting**: Cache size is limited to prevent memory issues
4. **Request deduplication**: Identical in-flight requests are deduplicated
5. **Configurability**: Caching can be configured per service and per request

```javascript
// Cache configuration
const schemaService = new SchemaService(apiClient, {
  enableCache: true,
  defaultTTL: 300, // 5 minutes
  maxCacheSize: 50 * 1024 * 1024 // 50MB
});

// Per-request cache options
const schema = await schemaService.getById(id, {
  useCache: true,
  ttl: 600, // 10 minutes for this specific request
  cacheKey: `special-schema-${id}` // Custom cache key
});

// Cache invalidation
schemaService.clearCache(`^schemas/${id}`); // Clear specific schema
schemaService.clearCache(`^schemas`); // Clear all schemas
```

## Mock Service Implementation

The Service Layer provides mock implementations for development and testing:

1. **Environment Detection**: Automatically switches to mocks in development
2. **Realistic Data**: Provides realistic mock data with proper relationships
3. **Controllable Behavior**: Simulates network delays and errors
4. **Interface Consistency**: Implements the same interface as real services

```javascript
// Mock service factory configuration
import mockServiceFactory from '../services/mock/mockServiceFactory';

// Mock repository service with the same interface
const repositoryService = mockServiceFactory.getRepositoryService();

// Use exactly like the real service
const repositories = await repositoryService.getAll();
```

## Request Cancellation

The Service Layer supports cancellation of in-flight requests:

1. **Component Unmounting**: Automatically cancels requests when components unmount
2. **Navigation**: Prevents stale data updates when navigating between pages
3. **User Action**: Allows cancellation of long-running requests based on user action

```javascript
// Automatic cancellation via hooks
const { data, loading } = useApi(
  () => repositoryService.getAll(),
  [],
  true // Requests are automatically cancelled on unmount
);

// Manual cancellation
import { createCancelToken, cancelPendingRequest } from '../services/api/cancelToken';

// Create a token
const source = createCancelToken('my-request');

// Make a cancellable request
repositoryService.getAll({}, { cancelToken: source.token });

// Cancel the request
cancelPendingRequest('my-request');
```

## Best Practices

### Using Services in Components

```jsx
// Best practice: Use domain-specific hooks
function RepositoryList() {
  const { repositories, loading, error } = useRepositories();
  
  if (loading) return <Loading />;
  if (error) return <ErrorDisplay error={error} />;
  
  return (
    <List>
      {repositories.map(repo => (
        <ListItem key={repo.id}>{repo.name}</ListItem>
      ))}
    </List>
  );
}

// Alternative: Use generic hooks for custom logic
function CustomRepositoryView() {
  const { data, loading, error, execute } = useApi(
    (filter) => repositoryService.getAll({ filter }),
    [], // Dependencies
    false // Don't execute immediately
  );
  
  useEffect(() => {
    execute(props.filter); // Manual execution with parameters
  }, [props.filter, execute]);
  
  // Rendering logic...
}
```

### Error Handling in Components

```jsx
function ErrorAwareComponent() {
  const { data, error } = useApi(/* ... */);
  
  // Intelligent error handling
  if (error) {
    if (error.isAuthError) {
      return <LoginPrompt />;
    } else if (error.isNetworkError) {
      return <OfflineIndicator onRetry={() => execute()} />;
    } else if (error.status === 404) {
      return <NotFound />;
    } else {
      return <ErrorMessage message={error.message} />;
    }
  }
  
  // Normal rendering...
}
```

### Testing with Services

```jsx
// Mocking services in tests
jest.mock('../services/api/serviceFactory', () => ({
  serviceFactory: {
    getRepositoryService: () => ({
      getAll: jest.fn().mockResolvedValue([
        { id: '1', name: 'Test Repo' }
      ])
    })
  }
}));

// Testing components that use services
test('renders repository list', async () => {
  render(<RepositoryList />);
  
  // Initial loading state
  expect(screen.getByTestId('loading')).toBeInTheDocument();
  
  // Wait for data
  const listItem = await screen.findByText('Test Repo');
  expect(listItem).toBeInTheDocument();
});
```

## API Endpoint Catalog

| Endpoint | Method | Description | Service Method | Response Type |
|----------|--------|-------------|---------------|---------------|
| `/repositories` | GET | Get all repositories | `repositoryService.getAll()` | `Repository[]` |
| `/repositories/:id` | GET | Get repository by ID | `repositoryService.getById(id)` | `Repository` |
| `/repositories` | POST | Create a repository | `repositoryService.create(data)` | `Repository` |
| `/repositories/:id` | DELETE | Delete a repository | `repositoryService.delete(id)` | `boolean` |
| `/repositories/:id/analyze` | POST | Trigger repository analysis | `repositoryService.triggerAnalysis(id)` | `AnalysisResult` |
| `/schemas` | GET | Get all schemas | `schemaService.getAll()` | `Schema[]` |
| `/schemas/:id` | GET | Get schema by ID | `schemaService.getById(id)` | `Schema` |
| `/repositories/:id/schemas` | GET | Get schemas by repository | `schemaService.getByRepository(repoId)` | `Schema[]` |
| `/schemas/:id/relationships` | GET | Get schema relationships | `schemaService.getRelationships(id)` | `Relationship[]` |
| `/schemas` | POST | Create a schema | `schemaService.createSchema(data)` | `Schema` |
| `/schemas/:id` | PUT | Update a schema | `schemaService.updateSchema(id, data)` | `Schema` |
| `/schemas/:id/validate` | POST | Validate a schema | `schemaService.validateSchema(id)` | `ValidationResult` |
| `/formats` | GET | Get all formats | `formatService.getAll()` | `Format[]` |
| `/formats/:id` | GET | Get format by ID | `formatService.getById(id)` | `Format` |
| `/formats/supported` | GET | Get supported formats | `formatService.getSupportedFormats()` | `Format[]` |
| `/formats/:id/validate` | POST | Validate against format | `formatService.validateSchema(formatId, schema)` | `ValidationResult` |
| `/auth/login` | POST | Login with credentials | `authService.login(credentials)` | `AuthResult` |
| `/auth/logout` | POST | Logout current user | `authService.logout()` | `boolean` |
| `/auth/register` | POST | Register new user | `authService.register(userData)` | `AuthResult` |
| `/auth/me` | GET | Get current user profile | `authService.getCurrentUser()` | `User` |
| `/auth/refresh` | POST | Refresh auth token | `authService.refreshToken()` | `AuthResult` |

## Implementation Roadmap

1. **Base infrastructure**: (Complete)
   - BaseService with caching and error handling
   - API client with interceptors
   - Service factory pattern
   
2. **Core services**: (Complete)
   - RepositoryService (Complete)
   - SchemaService (Complete)
   - FormatService (Complete)
   - AuthService (Complete)
   
3. **React integration**: (In Progress)
   - Custom hooks for services (Complete)
   - Error boundary components (Not Started)
   - Loading state components (Not Started)
   
4. **Redux integration**: (Complete)
   - Service-connected thunks (Complete)
   - Redux slices for all domain services (Complete)
   - Memoized selectors (Complete)
   
5. **React integration**: (Complete)
   - Custom hooks for accessing Redux state (Complete)
   - Helper hooks for simplified state management (Complete)
   - Integration patterns for components (Complete)
   
6. **Custom hooks system**: (Complete)
   - Utility hooks (useReduxAction, useReduxThunk) (Complete)
   - Domain-specific hooks (useRepositories, useSchemas, etc.) (Complete)
   - Entity-specific hooks (useRepository, useSchema, etc.) (Complete)
   - Relationship-focused hooks (useRelationshipsBySchema, etc.) (Complete)
   - Automatic data loading with loadImmediately (Complete)
   - Consistent loading/error state handling (Complete)
   
7. **Testing and documentation**: (In Progress)
   - Service unit tests (Complete)
   - Redux slice tests (Complete)
   - Hook tests (Complete)
   - Component integration tests (Not Started)

## Conclusion

The Service Layer architecture provides a robust, type-safe, and maintainable way to interact with backend APIs. By centralizing concerns like error handling, caching, and resilience patterns, we significantly reduce boilerplate in components and create a consistent development experience.

The combination of well-designed service classes, Redux integration, and custom React hooks creates a powerful and developer-friendly architecture that promotes:

1. **Separation of concerns** - UI components focus on rendering and user interaction, while data fetching, transformation, and state management are handled by dedicated layers
2. **Code reusability** - Services and hooks can be reused across the application
3. **Type safety** - TypeScript interfaces ensure proper data handling throughout the application
4. **Testing** - Each layer can be tested in isolation, with appropriate mocking
5. **Consistent patterns** - Developers can follow established patterns for new features
6. **Resilience** - Error handling, caching, and circuit breaking protect the application from failures