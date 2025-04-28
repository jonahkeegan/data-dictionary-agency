# System Patterns

This document outlines the architectural patterns, design principles, and conventions used throughout the Data Dictionary Agency.

## UI Patterns

### Component Architecture
The UI follows a component-based architecture using React:

```mermaid
flowchart TD
    subgraph App Container
        App[App.js] --> Layout[Layout Components]
        App --> Router[React Router]
        
        Layout --> Header[Header]
        Layout --> Sidebar[Sidebar]
        Layout --> Main[Main Content Area]
        
        Router --> Routes[Route Definitions]
        Routes --> Pages[Page Components]
        
        Pages --> Dashboard[Dashboard]
        Pages --> RepoBrowser[Repository Browser]
        Pages --> SchemaViewer[Schema Viewer]
        Pages --> Visualization[Visualization]
        Pages --> Settings[Settings]
        Pages --> NotFound[NotFound]
        
        subgraph Components
            UI[UI Components] --> LayoutComponents[Layout Components]
            UI --> DataComponents[Data-driven Components]
            UI --> CommonComponents[Common Components]
        end
        
        Pages -.-> Components
    end
```

### State Management
Redux is used for state management with a slice-based organization:

```mermaid
flowchart TD
    subgraph Redux Store
        Store[Store Configuration] --> Slices[Feature Slices]
        Store --> Middleware[Middleware]
        
        Slices --> RepoSlice[Repositories Slice]
        Slices --> SchemaSlice[Schemas Slice]
        Slices --> RelationshipSlice[Relationships Slice]
        Slices --> UISlice[UI Slice]
        Slices --> AuthSlice[Auth Slice]
        
        Middleware --> ThunkMiddleware[Thunk Middleware]
        Middleware --> LoggerMiddleware[Logger Middleware]
    end
    
    subgraph Components
        UI[UI Components] -- useSelector --> Store
        UI -- useDispatch --> Actions[Redux Actions]
    end
    
    Actions --> Thunks[Async Thunks]
    Actions --> Reducers[Reducers]
    
    Thunks --> APIServices[API Services]
    APIServices --> Backend[Backend API]
    
    Thunks --> Reducers
    Reducers --> Store
```

### Data Flow
The application follows a unidirectional data flow pattern:

```mermaid
sequenceDiagram
    participant User
    participant Component
    participant Action
    participant Thunk
    participant API
    participant Reducer
    participant Store
    
    User->>Component: Interaction
    Component->>Action: Dispatch action
    
    alt Synchronous Action
        Action->>Reducer: Process action
        Reducer->>Store: Update state
        Store->>Component: Notify changes
    else Asynchronous Action
        Action->>Thunk: Dispatch thunk
        Thunk->>API: Make API request
        API-->>Thunk: Return response
        Thunk->>Action: Dispatch success/error
        Action->>Reducer: Process action
        Reducer->>Store: Update state
        Store->>Component: Notify changes
    end
    
    Component->>User: Update UI
```

## Backend Patterns

### Repository Pattern
Data access logic is encapsulated in repository classes:

```python
class SchemaRepository:
    def __init__(self, db_session):
        self.db_session = db_session
        
    def get_by_id(self, schema_id):
        return self.db_session.query(Schema).filter(Schema.id == schema_id).first()
        
    def get_all(self):
        return self.db_session.query(Schema).all()
        
    def create(self, schema_data):
        schema = Schema(**schema_data)
        self.db_session.add(schema)
        self.db_session.commit()
        return schema
```

### Service Layer
Business logic is contained in service classes:

```python
class SchemaService:
    def __init__(self, schema_repo, relationship_repo):
        self.schema_repo = schema_repo
        self.relationship_repo = relationship_repo
        
    def detect_relationships(self, schema_id):
        schema = self.schema_repo.get_by_id(schema_id)
        if not schema:
            raise EntityNotFoundError("Schema not found")
            
        other_schemas = self.schema_repo.get_all()
        detector = RelationshipDetector()
        relationships = detector.detect(schema, other_schemas)
        
        for rel in relationships:
            self.relationship_repo.create(rel)
            
        return relationships
```

### Strategy Pattern
Format detection leverages the strategy pattern:

```python
class FormatDetector:
    def __init__(self):
        self.strategies = {}
        
    def register_strategy(self, format_name, strategy):
        self.strategies[format_name] = strategy
        
    def detect(self, content):
        results = {}
        for name, strategy in self.strategies.items():
            confidence = strategy.detect(content)
            if confidence > 0:
                results[name] = confidence
                
        return results
```

## UI Design Patterns

### Responsive Layout
The application uses a responsive layout approach:

```jsx
// Responsive grid example
<SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={5}>
  <Card>Content 1</Card>
  <Card>Content 2</Card>
  <Card>Content 3</Card>
  <Card>Content 4</Card>
</SimpleGrid>
```

### Component Composition
UI components are composed from smaller, reusable components:

```jsx
// Component composition example
const DashboardCard = ({ title, children, ...props }) => (
  <Card {...props}>
    <CardHeader>
      <Heading size="md">{title}</Heading>
    </CardHeader>
    <CardBody>
      {children}
    </CardBody>
  </Card>
);

// Usage
const Dashboard = () => (
  <Box>
    <DashboardCard title="Statistics">
      <StatGroup>
        <Stat name="Repositories" value={5} />
        <Stat name="Schemas" value={42} />
      </StatGroup>
    </DashboardCard>
  </Box>
);
```

### Container/Presentation Pattern
Components are separated into container (smart) and presentation (dumb) components:

```jsx
// Container component
const RepositoryListContainer = () => {
  const dispatch = useDispatch();
  const { repositories, status } = useSelector(state => state.repositories);
  
  useEffect(() => {
    dispatch(fetchRepositories());
  }, [dispatch]);
  
  return (
    <RepositoryList 
      repositories={repositories} 
      isLoading={status === 'loading'} 
    />
  );
};

// Presentation component
const RepositoryList = ({ repositories, isLoading }) => {
  if (isLoading) {
    return <Spinner />;
  }
  
  return (
    <VStack spacing={4} align="stretch">
      {repositories.map(repo => (
        <RepositoryItem key={repo.id} repository={repo} />
      ))}
    </VStack>
  );
};
```

## Data Processing Patterns

### Pipeline Pattern
Data processing uses a pipeline approach:

```python
class ProcessingPipeline:
    def __init__(self):
        self.steps = []
        
    def add_step(self, step):
        self.steps.append(step)
        
    def process(self, data):
        result = data
        for step in self.steps:
            result = step.process(result)
        return result
```

### Observer Pattern
The system uses observers for event notification:

```python
class EventEmitter:
    def __init__(self):
        self.listeners = {}
        
    def on(self, event, callback):
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(callback)
        
    def emit(self, event, *args, **kwargs):
        if event in self.listeners:
            for callback in self.listeners[event]:
                callback(*args, **kwargs)
```

## Testing Patterns

### Unit Testing
Unit tests focus on individual functions and components:

```jsx
// React component test example
describe('RepositoryItem', () => {
  it('renders repository name', () => {
    const repo = { id: 1, name: 'Test Repo', description: 'Test description' };
    render(<RepositoryItem repository={repo} />);
    expect(screen.getByText('Test Repo')).toBeInTheDocument();
  });
});
```

```python
# Python unit test example
def test_schema_detection():
    detector = SchemaDetector()
    result = detector.detect(json_content)
    assert result.format == 'json'
    assert result.confidence > 0.8
```

### Integration Testing
Integration tests verify the interaction between components:

```python
def test_relationship_detection_service():
    # Setup test database
    db = setup_test_db()
    schema_repo = SchemaRepository(db)
    rel_repo = RelationshipRepository(db)
    
    # Create test schemas
    schema1 = schema_repo.create({'name': 'users', 'content': '...'})
    schema2 = schema_repo.create({'name': 'orders', 'content': '...'})
    
    # Test service
    service = SchemaService(schema_repo, rel_repo)
    relationships = service.detect_relationships(schema1.id)
    
    # Assertions
    assert len(relationships) > 0
    assert relationships[0].source_schema_id == schema1.id
    assert relationships[0].target_schema_id == schema2.id
```

## Error Handling Patterns

### Try-Except Pattern
Backend code uses structured exception handling:

```python
def process_schema(schema_id):
    try:
        schema = schema_repository.get_by_id(schema_id)
        if not schema:
            raise EntityNotFoundError(f"Schema {schema_id} not found")
            
        result = schema_processor.process(schema)
        return result
    except EntityNotFoundError as e:
        logger.warning(f"Entity not found: {str(e)}")
        raise
    except ProcessingError as e:
        logger.error(f"Processing error: {str(e)}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise UnexpectedError(f"An unexpected error occurred: {str(e)}")
```

### Async/Await Pattern
Frontend code uses async/await for asynchronous operations:

```jsx
const fetchData = async () => {
  try {
    setLoading(true);
    const response = await api.getRepositories();
    setRepositories(response.data);
    setError(null);
  } catch (err) {
    setError(err.message || 'Failed to fetch repositories');
    setRepositories([]);
  } finally {
    setLoading(false);
  }
};
```

## Frontend API Patterns

### API Client Architecture
The frontend uses a comprehensive, centralized API client architecture with advanced features:

```mermaid
flowchart TD
    subgraph "API Client Layer"
        Config[Configuration] --> ClientFactory[API Client Factory]
        ClientFactory --> Client[Base Axios Client]
        Client --> RequestInterceptors[Request Interceptors]
        Client --> ResponseInterceptors[Response Interceptors]
        Client --> ErrorHandler[Error Handler]
        Client --> CircuitBreaker[Circuit Breaker]
    end
    
    subgraph "Service Layer"
        Client --> BaseService[Base Service]
        BaseService --> RepoService[Repository Service]
        BaseService --> SchemaService[Schema Service]
        BaseService --> FormatService[Format Service]
        BaseService --> AuthService[Auth Service]
        
        CacheManager[Cache Manager] --- BaseService
    end
    
    subgraph "Mock Service Layer"
        MockServiceFactory[Mock Service Factory]
        MockServiceFactory --> MockRepoService[Mock Repository Service]
        MockServiceFactory --> MockSchemaService[Mock Schema Service]
        MockServiceFactory --> MockFormatService[Mock Format Service]
        MockServiceFactory --> MockAuthService[Mock Auth Service]
        MockDataStore[Mock Data Store] --- MockServiceFactory
    end
    
    subgraph "Service Factory"
        EnvConfig[Environment Config] --> ServiceFactory[Service Factory]
        ServiceFactory --> RepoService
        ServiceFactory --> SchemaService
        ServiceFactory --> FormatService
        ServiceFactory --> AuthService
        ServiceFactory -.-> MockServiceFactory
    end
    
    subgraph "Integration Layer"
        RepoService & SchemaService & FormatService & AuthService --> CustomHooks[Custom React Hooks]
        CustomHooks --> ReactComponents[React Components]
        CustomHooks --> ReduxThunks[Redux Thunks]
    end
```

### Service Abstraction Pattern
API endpoints are abstracted through service modules:

```javascript
// Repository service example
export const RepositoryService = {
  getAll: async (params = {}, options = {}) => {
    const requestKey = generateRequestKey('getRepositories', [params]);
    
    // If no cancel token provided, create one
    if (!options.cancelToken) {
      const source = createCancelToken(requestKey);
      options.cancelToken = source.token;
    }
    
    const response = await apiClient.get('/repositories', { 
      params,
      ...options 
    });
    
    return response.data;
  },
  
  getById: async (id, options = {}) => {
    // Implementation...
  },
  
  // Additional methods...
};
```

### Request Cancellation Pattern
Request cancellation is managed through cancel tokens:

```javascript
// Cancel token usage example
const source = createCancelToken('my-request');

// Make cancellable request
apiClient.get('/long-running-operation', {
  cancelToken: source.token
});

// Cancel the request if needed
cancelPendingRequest('my-request');
```

### Custom Hooks Pattern
Custom hooks abstract API interaction for components:

```jsx
// Custom hook for API calls
export const useApi = (apiFunction, dependencies = [], immediate = false) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Execute API call
  const execute = useCallback(async (...args) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiFunction(...args);
      setData(response);
      return response;
    } catch (error) {
      if (!isCancel(error)) {
        setError(error);
      }
      throw error;
    } finally {
      setLoading(false);
    }
  }, [apiFunction]);
  
  // Effect for immediate execution and cleanup
  useEffect(() => {
    let mounted = true;
    
    if (immediate) {
      execute().catch(error => {
        // Handle errors...
      });
    }
    
    return () => {
      mounted = false;
      // Cancel pending requests on unmount
    };
  }, dependencies);
  
  return { data, loading, error, execute };
};

// Usage example
const RepositoryList = () => {
  const { data, loading, error } = useApi(
    () => RepositoryService.getAll(),
    [],
    true
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

### Advanced Caching Pattern
The application uses a sophisticated caching system with TTL and pattern-based invalidation:

```javascript
// Cache manager implementation with TTL
export class CacheManager {
  constructor(options = {}) {
    this.cache = new Map();
    this.defaultTTL = options.defaultTTL || 300; // 5 minutes default
    this.maxEntries = options.maxEntries || 100;
    this.stats = { hits: 0, misses: 0 };
  }
  
  // Get item from cache
  get(path, params = {}) {
    const key = this._generateCacheKey(path, params);
    const entry = this.cache.get(key);
    
    if (!entry) {
      this.stats.misses++;
      return null;
    }
    
    // Check if entry has expired
    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      this.stats.misses++;
      return null;
    }
    
    this.stats.hits++;
    return entry.data;
  }
  
  // Store item in cache
  set(path, params = {}, data, ttl) {
    const key = this._generateCacheKey(path, params);
    const expiresAt = Date.now() + (ttl || this.defaultTTL) * 1000;
    
    // If cache is full, remove oldest entry
    if (this.cache.size >= this.maxEntries) {
      const oldestKey = [...this.cache.keys()][0];
      this.cache.delete(oldestKey);
    }
    
    this.cache.set(key, { data, expiresAt });
    return true;
  }
  
  // Invalidate cache entries by pattern
  invalidate(pattern) {
    const regex = new RegExp(pattern);
    let count = 0;
    
    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.cache.delete(key);
        count++;
      }
    }
    
    return count;
  }
  
  // Generate cache key from path and params
  _generateCacheKey(path, params) {
    return `${path}:${JSON.stringify(params)}`;
  }
  
  // Clear entire cache
  clear() {
    const size = this.cache.size;
    this.cache.clear();
    return size;
  }
  
  // Get cache statistics
  getStats() {
    return {
      ...this.stats,
      size: this.cache.size,
      hitRate: this.stats.hits / (this.stats.hits + this.stats.misses) || 0
    };
  }
}
```

Usage example:

```javascript
// Service using cache manager
export class RepositoryService extends BaseService {
  constructor(apiClient, options = {}) {
    super(apiClient, options);
    this.defaultTTL = options.defaultTTL || 600; // 10 minutes for repositories
  }
  
  async getAll(params = {}, options = {}) {
    // Skip cache if explicitly requested
    if (options.useCache !== false && this.cacheManager) {
      const cached = this.cacheManager.get('/repositories', params);
      if (cached) {
        return cached;
      }
    }
    
    const data = await this._request('/repositories', 'GET', { params });
    
    // Store in cache if not disabled
    if (options.useCache !== false && this.cacheManager) {
      this.cacheManager.set('/repositories', params, data, options.ttl || this.defaultTTL);
    }
    
    return data;
  }
  
  // When updating a repository, invalidate related cache entries
  async update(id, data, options = {}) {
    const result = await this._request(`/repositories/${id}`, 'PUT', { data });
    
    // Invalidate cache entries matching patterns
    if (this.cacheManager) {
      this.cacheManager.invalidate(`^/repositories($|\\?)`); // All repositories list
      this.cacheManager.invalidate(`^/repositories/${id}($|\\?)`); // Specific repository
      this.cacheManager.invalidate(`^/schemas\\?.*repository_id=${id}`); // Related schemas
    }
    
    return result;
  }
}
```

### Centralized Mock Service Pattern
Development is accelerated through centralized mock services with realistic data:

```javascript
// Mock service factory
export class MockServiceFactory {
  constructor(options = {}) {
    this.delay = options.delay || 800;
    this.errorRate = options.errorRate || 0;
    this.dataStore = new MockDataStore();
  }
  
  // Get repository service mock
  getRepositoryService() {
    return new MockRepositoryService(this.dataStore, {
      delay: this.delay,
      errorRate: this.errorRate
    });
  }
  
  // Get schema service mock
  getSchemaService() {
    return new MockSchemaService(this.dataStore, {
      delay: this.delay,
      errorRate: this.errorRate
    });
  }
  
  // Get format service mock
  getFormatService() {
    return new MockFormatService(this.dataStore, {
      delay: this.delay,
      errorRate: this.errorRate
    });
  }
  
  // Get auth service mock
  getAuthService() {
    return new MockAuthService(this.dataStore, {
      delay: this.delay,
      errorRate: this.errorRate
    });
  }
  
  // Configure mock behavior
  configure(options) {
    if (options.delay !== undefined) this.delay = options.delay;
    if (options.errorRate !== undefined) this.errorRate = options.errorRate;
    if (options.seed) this.dataStore.seed(options.seed);
  }
}

// Mock repository service example
export class MockRepositoryService {
  constructor(dataStore, options = {}) {
    this.dataStore = dataStore;
    this.delay = options.delay || 800;
    this.errorRate = options.errorRate || 0;
  }
  
  async getAll(params = {}) {
    await this._simulateNetworkDelay();
    
    // Simulate random error if errorRate > 0
    if (Math.random() < this.errorRate) {
      throw new Error("Network error");
    }
    
    let repositories = [...this.dataStore.repositories];
    
    // Apply filtering
    if (params.status) {
      repositories = repositories.filter(repo => repo.status === params.status);
    }
    
    // Apply sorting
    if (params.sort) {
      repositories.sort((a, b) => {
        const direction = params.order === 'desc' ? -1 : 1;
        return direction * (a[params.sort] > b[params.sort] ? 1 : -1);
      });
    }
    
    // Apply pagination
    const skip = params.skip || 0;
    const limit = params.limit || repositories.length;
    
    return {
      data: repositories.slice(skip, skip + limit),
      meta: {
        total: repositories.length,
        skip: skip,
        limit: limit
      }
    };
  }
  
  async getById(id) {
    await this._simulateNetworkDelay();
    
    const repository = this.dataStore.repositories.find(repo => repo.id === id);
    
    if (!repository) {
      throw { status: 404, message: "Repository not found" };
    }
    
    return { data: repository };
  }
  
  // More methods...
  
  async _simulateNetworkDelay() {
    return new Promise(resolve => setTimeout(resolve, this.delay));
  }
}

## Security Patterns

### Authentication Middleware
API endpoints are protected by authentication middleware:

```python
@app.middleware("http")
async def authenticate(request, call_next):
    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)
        
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401, 
            content={"detail": "Authentication required"}
        )
        
    token = auth_header.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        request.state.user = payload
    except jwt.PyJWTError:
        return JSONResponse(
            status_code=401, 
            content={"detail": "Invalid authentication token"}
        )
        
    return await call_next(request)
```

### RBAC (Role-Based Access Control)
Access control is managed through user roles:

```python
def require_role(role):
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            user = request.state.user
            if user["role"] not in [role, "admin"]:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Insufficient permissions"}
                )
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
