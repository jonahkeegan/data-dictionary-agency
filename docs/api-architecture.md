# API Client Architecture

This document outlines the API client architecture for the Data Dictionary Agency frontend.

## Overview

The API client architecture provides a centralized system for making HTTP requests to the backend API, with built-in support for:

- Environment-specific configuration
- Authentication
- Error handling and standardization
- Request cancellation
- Retry mechanisms for transient failures
- Mock services for development and testing

## Architecture Diagram

```mermaid
flowchart TD
    subgraph Component Layer
        Components[React Components]
        Hooks[Custom Hooks]
    end
    
    subgraph State Management
        ReduxStore[Redux Store]
        Thunks[Async Thunks]
    end
    
    subgraph Service Layer
        RepoService[Repository Service]
        SchemaService[Schema Service]
        FormatService[Format Service]
        AuthService[Auth Service]
    end
    
    subgraph API Client
        ClientFactory[API Client Factory]
        BaseClient[Base Axios Client]
        RequestInterceptors[Request Interceptors]
        ResponseInterceptors[Response Interceptors]
        ErrorHandler[Error Handler]
    end
    
    subgraph Configuration
        ConfigManager[Config Manager]
        EnvConfig[Environment Config]
    end
    
    subgraph Backend Simulation
        MockService[Mock Service]
        MockData[Mock Data]
    end
    
    Components --> Hooks
    Hooks --> ReduxStore
    Hooks --> Thunks
    
    Thunks --> Service Layer
    
    RepoService --> ClientFactory
    SchemaService --> ClientFactory
    FormatService --> ClientFactory
    AuthService --> ClientFactory
    
    ClientFactory --> BaseClient
    BaseClient --> RequestInterceptors
    BaseClient --> ResponseInterceptors
    BaseClient --> ErrorHandler
    
    ClientFactory --> ConfigManager
    ConfigManager --> EnvConfig
    
    ClientFactory -.-> MockService
    MockService --> MockData
```

## Request Flow

```mermaid
sequenceDiagram
    participant Component
    participant Hook
    participant Redux
    participant Service
    participant APIClient
    participant Server
    
    Component->>Hook: Call hook (e.g., useRepositories)
    Hook->>Redux: Dispatch thunk action
    Redux->>Service: Call service method
    Service->>APIClient: Make HTTP request
    alt Successful Request
        APIClient->>Server: Send HTTP request
        Server-->>APIClient: Return response
        APIClient-->>Service: Return parsed data
        Service-->>Redux: Return data
        Redux-->>Hook: Update state
        Hook-->>Component: Re-render with data
    else Failed Request
        APIClient->>Server: Send HTTP request
        Server-->>APIClient: Error response
        APIClient-->>APIClient: Transform error
        alt Retryable Error
            APIClient->>APIClient: Wait with backoff
            APIClient->>Server: Retry request
            Server-->>APIClient: Return response
            APIClient-->>Service: Return parsed data
            Service-->>Redux: Return data
            Redux-->>Hook: Update state
            Hook-->>Component: Re-render with data
        else Non-retryable Error
            APIClient-->>Service: Throw standardized error
            Service-->>Redux: Dispatch failure action
            Redux-->>Hook: Update error state
            Hook-->>Component: Re-render with error
        end
    end
```

## Components

### Configuration Management

The configuration system provides environment-specific settings:

```javascript
// Example usage
import { getConfig } from '../config';

const config = getConfig();
console.log(`API URL: ${config.apiUrl}`);
```

Key configuration options:

| Option | Description | Default |
|--------|-------------|---------|
| `apiUrl` | Base URL for API requests | `http://localhost:8000/api` (development) |
| `timeout` | Request timeout in ms | `10000` (development) |
| `retryCount` | Max number of retries | `3` (development) |
| `mockEnabled` | Enable mock services | `true` (development) |
| `logLevel` | Logging verbosity | `debug` (development) |

### API Client Factory

The client factory creates configured Axios instances:

```javascript
// Example usage
import { createApiClient, apiClient } from '../services/api/client';

// Use default client
apiClient.get('/repositories');

// Create custom client
const customClient = createApiClient({
  baseURL: 'https://alternative-api.com',
  timeout: 30000
});
```

Features:

- **Request Interceptors**: Automatically adds authentication headers and handles request processing
- **Response Interceptors**: Transforms responses and standardizes error handling
- **Error Transformation**: Converts various error types into a consistent format
- **Retry Logic**: Automatically retries requests that fail due to network or server errors

### Service Layer

Services encapsulate API endpoint logic:

```javascript
// Example usage
import { RepositoryService } from '../services/api/repositories';

// Get all repositories
const repositories = await RepositoryService.getAll();

// Get repository by ID
const repository = await RepositoryService.getById('repo-123');
```

Available services:

- **RepositoryService**: Manages repository-related API calls
- **SchemaService**: Manages schema-related API calls
- **FormatService**: Manages format-related API calls

### Request Cancellation

Cancellation tokens allow aborting in-flight requests:

```javascript
import { createCancelToken, cancelPendingRequest } from '../services/api/cancelToken';

// Create token
const source = createCancelToken('my-request');

// Make cancellable request
apiClient.get('/long-running-operation', {
  cancelToken: source.token
});

// Cancel the request if needed
cancelPendingRequest('my-request');
```

This is particularly useful for component unmounting or navigation events to prevent state updates on unmounted components.

### Mock Services

Mock services provide simulated backend responses for development:

```javascript
// Automatically configured based on environment
// No code changes needed to switch between real and mock
```

The mock service system:

- Is enabled by default in development environments
- Automatically generates realistic looking data
- Simulates network delays and errors
- Can be toggled via configuration

### Custom Hooks

Custom hooks abstract API interaction for components:

```jsx
// Example usage in a component
const RepositoryList = () => {
  const { data, loading, error } = useApi(
    () => RepositoryService.getAll(),
    [], // Dependencies
    true // Execute immediately
  );
  
  if (loading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;
  
  return (
    <List>
      {data.map(repo => (
        <ListItem key={repo.id}>{repo.name}</ListItem>
      ))}
    </List>
  );
};
```

Available hooks:

- **useApi**: General purpose hook for API calls
- **usePaginatedApi**: Hook for paginated API calls with navigation controls

## Error Handling

Errors are standardized into a consistent format:

```javascript
try {
  await RepositoryService.getById('invalid-id');
} catch (error) {
  console.log(error.status);    // HTTP status code (e.g., 404)
  console.log(error.message);   // Human-readable message
  console.log(error.code);      // Error code (e.g., 'NOT_FOUND')
  console.log(error.errors);    // Array of detailed errors
  
  // Error classification helpers
  console.log(error.isNetworkError); // Connection issues
  console.log(error.isServerError);  // 5xx status codes
  console.log(error.isClientError);  // 4xx status codes
  console.log(error.isAuthError);    // 401/403 status codes
}
```

The error handling system:

- Provides consistent error structure across all API calls
- Classifies errors for easier handling
- Includes original error details for debugging
- Support retrying for transient errors

## Integration with Redux

API services are integrated with Redux via thunks:

```javascript
// Redux slice example
export const fetchRepositories = createAsyncThunk(
  'repositories/fetchRepositories',
  async (params = {}, { rejectWithValue }) => {
    try {
      // Use retry mechanism for this critical operation
      return await retryRequest(() => RepositoryService.getAll(params));
    } catch (error) {
      return rejectWithValue(error.message || 'Failed to fetch repositories');
    }
  }
);
```

The Redux integration:

- Uses async thunks for API calls
- Handles loading, success, and error states
- Standardizes error handling
- Provides retry functionality for critical operations

## Best Practices

### Making API Calls from Components

Prefer using custom hooks instead of direct service calls:

```jsx
// Good - using hooks
const { data, loading, error } = useApi(
  () => RepositoryService.getById(id),
  [id],
  true
);

// Avoid - direct service call
const [data, setData] = useState(null);
const [loading, setLoading] = useState(true);
useEffect(() => {
  RepositoryService.getById(id)
    .then(response => setData(response))
    .finally(() => setLoading(false));
}, [id]);
```

### Error Handling in Components

Use the standardized error properties for consistent UI handling:

```jsx
if (error) {
  if (error.isAuthError) {
    return <LoginPrompt />;
  }
  
  if (error.isNetworkError) {
    return <OfflineIndicator onRetry={retryFn} />;
  }
  
  return <ErrorMessage message={error.message} />;
}
```

### Cancellation on Component Unmounting

The `useApi` hook automatically handles cancellation on unmount, but for manual service calls:

```jsx
useEffect(() => {
  const source = createCancelToken('my-request');
  
  RepositoryService.getAll({}, { cancelToken: source.token })
    .then(/* ... */);
    
  return () => {
    // Cancel on unmount
    cancelPendingRequest('my-request');
  };
}, []);
```

### Handling Pagination

Use the `usePaginatedApi` hook for paginated API requests:

```jsx
const {
  data,
  loading,
  page,
  totalPages,
  nextPage,
  prevPage,
  goToPage
} = usePaginatedApi(
  (params) => RepositoryService.getAll(params),
  { skip: 0, limit: 10 }
);
```

## Testing

### Mocking services in unit tests

Services can be easily mocked for component tests:

```jsx
jest.mock('../services/api/repositories', () => ({
  RepositoryService: {
    getAll: jest.fn().mockResolvedValue([
      { id: '1', name: 'Mock Repo 1' },
      { id: '2', name: 'Mock Repo 2' }
    ])
  }
}));
```

### Testing hooks

Custom hooks can be tested using `@testing-library/react-hooks`:

```jsx
const { result, waitForNextUpdate } = renderHook(() => 
  useApi(() => RepositoryService.getAll(), [], true)
);

// Initial state
expect(result.current.loading).toBe(true);

// Wait for update
await waitForNextUpdate();

// Updated state
expect(result.current.loading).toBe(false);
expect(result.current.data).toEqual(expectedData);
```

## Conclusion

This API client architecture provides a robust foundation for frontend-backend communication, with features that enhance development productivity, code quality, and user experience. By centralizing API communication patterns and implementing best practices, we ensure a consistent and maintainable codebase.
