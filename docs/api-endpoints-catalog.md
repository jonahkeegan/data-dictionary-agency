# API Endpoints Catalog

This document serves as a comprehensive catalog of all API endpoints available in the Data Dictionary Agency application. Each endpoint is described with its purpose, parameters, request and response formats, and corresponding frontend service methods.

## Overview

The Data Dictionary Agency API follows a RESTful design pattern. All endpoints use standard HTTP methods:

- `GET`: Retrieve resources
- `POST`: Create new resources
- `PUT`: Update existing resources
- `DELETE`: Remove resources

## Authentication

Most endpoints require authentication via JWT tokens. Authentication tokens are obtained through the `/auth/login` endpoint and should be included in the `Authorization` header of subsequent requests:

```
Authorization: Bearer [token]
```

## Base URL

All API paths in this document are relative to the base API URL:

- Development: `http://localhost:8000/api`
- Production: `https://api.data-dictionary-agency.example.com/api`

## Response Format

All responses follow a standard format:

```json
{
  "data": {
    // Resource data
  },
  "meta": {
    // Pagination or other metadata
  },
  "error": {
    // Error information (if applicable)
  }
}
```

## Repository Endpoints

### Get All Repositories

Retrieves a list of repositories with optional filtering and pagination.

- **URL**: `/repositories`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `skip` (number): Number of items to skip (default: 0)
  - `limit` (number): Maximum number of items to return (default: 100)
  - `sort` (string): Field to sort by
  - `order` (string): Sort order ('asc' or 'desc')
  - `status` (string): Filter by repository status

**Response**:
```json
{
  "data": [
    {
      "id": "repo-1",
      "name": "Example Repository",
      "description": "Example repository description",
      "url": "https://github.com/example/repo",
      "status": "active",
      "progress": 100,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    },
    // Additional repositories...
  ],
  "meta": {
    "total": 120,
    "skip": 0,
    "limit": 100
  }
}
```

**Service Method**:
```javascript
repositoryService.getAll({
  skip: 0,
  limit: 10,
  sort: 'name',
  order: 'asc'
});
```

**React Hook**:
```javascript
const { data, loading, error } = useRepositories();
```

### Get Repository by ID

Retrieves a specific repository by ID.

- **URL**: `/repositories/:id`
- **Method**: `GET`
- **Auth Required**: Yes
- **URL Parameters**:
  - `id` (string): Repository ID

**Response**:
```json
{
  "data": {
    "id": "repo-1",
    "name": "Example Repository",
    "description": "Example repository description",
    "url": "https://github.com/example/repo",
    "status": "active",
    "progress": 100,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
}
```

**Service Method**:
```javascript
repositoryService.getById('repo-1');
```

**React Hook**:
```javascript
const { repository, loading, error } = useRepositories('repo-1');
```

### Create Repository

Creates a new repository.

- **URL**: `/repositories`
- **Method**: `POST`
- **Auth Required**: Yes
- **Request Body**:
```json
{
  "name": "New Repository",
  "description": "New repository description",
  "url": "https://github.com/example/new-repo"
}
```

**Response**:
```json
{
  "data": {
    "id": "repo-2",
    "name": "New Repository",
    "description": "New repository description",
    "url": "https://github.com/example/new-repo",
    "status": "pending",
    "progress": 0,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
}
```

**Service Method**:
```javascript
repositoryService.create({
  name: "New Repository",
  description: "New repository description",
  url: "https://github.com/example/new-repo"
});
```

### Update Repository

Updates an existing repository.

- **URL**: `/repositories/:id`
- **Method**: `PUT`
- **Auth Required**: Yes
- **URL Parameters**:
  - `id` (string): Repository ID
- **Request Body**:
```json
{
  "name": "Updated Repository",
  "description": "Updated description"
}
```

**Response**:
```json
{
  "data": {
    "id": "repo-1",
    "name": "Updated Repository",
    "description": "Updated description",
    "url": "https://github.com/example/repo",
    "status": "active",
    "progress": 100,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-02T00:00:00Z"
  }
}
```

**Service Method**:
```javascript
repositoryService.update('repo-1', {
  name: "Updated Repository",
  description: "Updated description"
});
```

### Delete Repository

Deletes a repository.

- **URL**: `/repositories/:id`
- **Method**: `DELETE`
- **Auth Required**: Yes
- **URL Parameters**:
  - `id` (string): Repository ID

**Response**:
```json
{
  "data": {
    "success": true,
    "message": "Repository deleted successfully"
  }
}
```

**Service Method**:
```javascript
repositoryService.delete('repo-1');
```

### Trigger Repository Analysis

Initiates an analysis process for a repository.

- **URL**: `/repositories/:id/analyze`
- **Method**: `POST`
- **Auth Required**: Yes
- **URL Parameters**:
  - `id` (string): Repository ID
- **Request Body**:
```json
{
  "options": {
    "deep": true,
    "include_branches": ["main", "develop"]
  }
}
```

**Response**:
```json
{
  "data": {
    "id": "analysis-1",
    "repository_id": "repo-1",
    "status": "in_progress",
    "progress": 0,
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

**Service Method**:
```javascript
repositoryService.triggerAnalysis('repo-1', {
  deep: true,
  include_branches: ["main", "develop"]
});
```

## Schema Endpoints

### Get All Schemas

Retrieves a list of schemas with optional filtering and pagination.

- **URL**: `/schemas`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `skip` (number): Number of items to skip (default: 0)
  - `limit` (number): Maximum number of items to return (default: 100)
  - `repository_id` (string): Filter by repository ID
  - `format_id` (string): Filter by format ID
  - `sort` (string): Field to sort by
  - `order` (string): Sort order ('asc' or 'desc')

**Response**:
```json
{
  "data": [
    {
      "id": "schema-1",
      "name": "User Schema",
      "description": "User data schema",
      "repository_id": "repo-1",
      "format_id": "format-1",
      "format_name": "JSON Schema",
      "file_path": "/schemas/user.json",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    },
    // Additional schemas...
  ],
  "meta": {
    "total": 45,
    "skip": 0,
    "limit": 100
  }
}
```

**Service Method**:
```javascript
schemaService.getAll({
  repository_id: 'repo-1',
  limit: 20
});
```

**React Hook**:
```javascript
const { schemas, loading, error } = useSchemas({
  repository_id: 'repo-1'
});
```

### Get Schema by ID

Retrieves a specific schema by ID.

- **URL**: `/schemas/:id`
- **Method**: `GET`
- **Auth Required**: Yes
- **URL Parameters**:
  - `id` (string): Schema ID

**Response**:
```json
{
  "data": {
    "id": "schema-1",
    "name": "User Schema",
    "description": "User data schema",
    "repository_id": "repo-1",
    "format_id": "format-1",
    "format_name": "JSON Schema",
    "file_path": "/schemas/user.json",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z",
    "content": {
      "type": "object",
      "properties": {
        "id": { "type": "string" },
        "name": { "type": "string" },
        "email": { "type": "string", "format": "email" }
      },
      "required": ["id", "name", "email"]
    }
  }
}
```

**Service Method**:
```javascript
schemaService.getById('schema-1');
```

**React Hook**:
```javascript
const { schemas, loading, error } = useSchemas();
const getSchema = useCallback(id => {
  return schemas.execute(id);
}, [schemas]);

// Usage
const schema = await getSchema('schema-1');
```

### Create Schema

Creates a new schema.

- **URL**: `/schemas`
- **Method**: `POST`
- **Auth Required**: Yes
- **Request Body**:
```json
{
  "name": "Product Schema",
  "description": "Product data schema",
  "repository_id": "repo-1",
  "format_id": "format-1",
  "file_path": "/schemas/product.json",
  "content": {
    "type": "object",
    "properties": {
      "id": { "type": "string" },
      "name": { "type": "string" },
      "price": { "type": "number" }
    },
    "required": ["id", "name", "price"]
  }
}
```

**Response**:
```json
{
  "data": {
    "id": "schema-2",
    "name": "Product Schema",
    "description": "Product data schema",
    "repository_id": "repo-1",
    "format_id": "format-1",
    "format_name": "JSON Schema",
    "file_path": "/schemas/product.json",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z",
    "content": {
      "type": "object",
      "properties": {
        "id": { "type": "string" },
        "name": { "type": "string" },
        "price": { "type": "number" }
      },
      "required": ["id", "name", "price"]
    }
  }
}
```

**Service Method**:
```javascript
schemaService.create({
  name: "Product Schema",
  description: "Product data schema",
  repository_id: "repo-1",
  format_id: "format-1",
  file_path: "/schemas/product.json",
  content: {
    // Schema content...
  }
});
```

### Get Schema Relationships

Retrieves relationships for a specific schema.

- **URL**: `/schemas/:id/relationships`
- **Method**: `GET`
- **Auth Required**: Yes
- **URL Parameters**:
  - `id` (string): Schema ID

**Response**:
```json
{
  "data": [
    {
      "id": "rel-1",
      "source_schema_id": "schema-1",
      "target_schema_id": "schema-2",
      "relationship_type": "one-to-many",
      "confidence": 0.95,
      "properties": {
        "source_field": "id",
        "target_field": "user_id"
      }
    },
    // Additional relationships...
  ]
}
```

**Service Method**:
```javascript
schemaService.getRelationships('schema-1');
```

**React Hook**:
```javascript
const { schemas, getRelationships } = useSchemas();
// Usage
const relationships = await getRelationships('schema-1');
```

### Export Schema

Exports a schema in a specific format.

- **URL**: `/schemas/:id/export`
- **Method**: `POST`
- **Auth Required**: Yes
- **URL Parameters**:
  - `id` (string): Schema ID
- **Query Parameters**:
  - `format` (string): Export format (default: 'json')

**Response**:
```json
{
  "data": {
    "format": "json",
    "content": "{\n  \"type\": \"object\",\n  \"properties\": {\n    \"id\": { \"type\": \"string\" },\n    \"name\": { \"type\": \"string\" },\n    \"price\": { \"type\": \"number\" }\n  },\n  \"required\": [\"id\", \"name\", \"price\"]\n}",
    "schema_id": "schema-2",
    "schema_name": "Product Schema"
  }
}
```

**Service Method**:
```javascript
schemaService.export('schema-2', 'json');
```

## Format Endpoints

### Get All Formats

Retrieves a list of supported data formats.

- **URL**: `/formats`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `skip` (number): Number of items to skip (default: 0)
  - `limit` (number): Maximum number of items to return (default: 100)

**Response**:
```json
{
  "data": [
    {
      "id": "format-1",
      "name": "JSON Schema",
      "description": "JSON Schema specification",
      "mime_type": "application/schema+json",
      "file_extensions": [".json", ".schema.json"],
      "detection_patterns": ["\\$schema"],
      "example": "{ \"$schema\": \"http://json-schema.org/draft-07/schema#\" }",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    },
    // Additional formats...
  ],
  "meta": {
    "total": 8,
    "skip": 0,
    "limit": 100
  }
}
```

**Service Method**:
```javascript
formatService.getAll();
```

**React Hook**:
```javascript
const { formats, loading, error } = useFormats();
```

### Get Format by ID

Retrieves a specific format by ID.

- **URL**: `/formats/:id`
- **Method**: `GET`
- **Auth Required**: Yes
- **URL Parameters**:
  - `id` (string): Format ID

**Response**:
```json
{
  "data": {
    "id": "format-1",
    "name": "JSON Schema",
    "description": "JSON Schema specification",
    "mime_type": "application/schema+json",
    "file_extensions": [".json", ".schema.json"],
    "detection_patterns": ["\\$schema"],
    "example": "{ \"$schema\": \"http://json-schema.org/draft-07/schema#\" }",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
}
```

**Service Method**:
```javascript
formatService.getById('format-1');
```

### Get Supported Formats

Retrieves a list of supported format names.

- **URL**: `/formats/supported`
- **Method**: `GET`
- **Auth Required**: Yes

**Response**:
```json
{
  "data": [
    "JSON Schema",
    "SQL",
    "XML Schema",
    "Avro",
    "Protocol Buffers",
    "GraphQL",
    "OpenAPI",
    "YAML"
  ]
}
```

**Service Method**:
```javascript
formatService.getSupportedFormats();
```

**React Hook**:
```javascript
const { supportedFormats } = useFormats();
```

### Validate Schema for Format

Validates a schema against a specific format.

- **URL**: `/formats/:id/validate`
- **Method**: `POST`
- **Auth Required**: Yes
- **URL Parameters**:
  - `id` (string): Format ID
- **Request Body**: Schema content

**Response**:
```json
{
  "data": {
    "valid": true,
    "errors": [],
    "format": "JSON Schema"
  }
}
```

**Service Method**:
```javascript
formatService.validateSchema('format-1', schemaContent);
```

**React Hook**:
```javascript
const { validateSchema } = useFormats();
// Usage
const result = await validateSchema('format-1', schemaContent);
```

## Authentication Endpoints

### Login

Authenticates a user and returns a JWT token.

- **URL**: `/auth/login`
- **Method**: `POST`
- **Auth Required**: No
- **Request Body**:
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response**:
```json
{
  "data": {
    "token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "user": {
      "id": "user-1",
      "username": "user@example.com",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "created_at": "2025-01-01T00:00:00Z",
      "last_login": "2025-01-01T00:00:00Z"
    }
  }
}
```

**Service Method**:
```javascript
authService.login({
  username: "user@example.com",
  password: "password123"
});
```

**React Hook**:
```javascript
const { login, isAuthenticated } = useAuth();
// Usage
await login({
  username: "user@example.com",
  password: "password123"
});
```

### Register

Creates a new user account.

- **URL**: `/auth/register`
- **Method**: `POST`
- **Auth Required**: No
- **Request Body**:
```json
{
  "username": "newuser@example.com",
  "email": "newuser@example.com",
  "password": "password123",
  "first_name": "Jane",
  "last_name": "Smith"
}
```

**Response**:
```json
{
  "data": {
    "token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "user": {
      "id": "user-2",
      "username": "newuser@example.com",
      "email": "newuser@example.com",
      "first_name": "Jane",
      "last_name": "Smith",
      "created_at": "2025-01-01T00:00:00Z",
      "last_login": "2025-01-01T00:00:00Z"
    }
  }
}
```

**Service Method**:
```javascript
authService.register({
  username: "newuser@example.com",
  email: "newuser@example.com",
  password: "password123",
  first_name: "Jane",
  last_name: "Smith"
});
```

**React Hook**:
```javascript
const { register } = useAuth();
// Usage
await register({
  username: "newuser@example.com",
  email: "newuser@example.com",
  password: "password123",
  first_name: "Jane",
  last_name: "Smith"
});
```

### Get Current User

Retrieves information about the currently authenticated user.

- **URL**: `/auth/me`
- **Method**: `GET`
- **Auth Required**: Yes

**Response**:
```json
{
  "data": {
    "id": "user-1",
    "username": "user@example.com",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "created_at": "2025-01-01T00:00:00Z",
    "last_login": "2025-01-01T00:00:00Z"
  }
}
```

**Service Method**:
```javascript
authService.getCurrentUser();
```

**React Hook**:
```javascript
const { user, userLoading } = useAuth();
```

### Refresh Token

Refreshes an authentication token using a refresh token.

- **URL**: `/auth/refresh`
- **Method**: `POST`
- **Auth Required**: No
- **Request Body**:
```json
{
  "refresh_token": "eyJhbGci..."
}
```

**Response**:
```json
{
  "data": {
    "token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "user": {
      "id": "user-1",
      "username": "user@example.com",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe"
    }
  }
}
```

**Service Method**:
```javascript
authService.refreshToken();
```

**React Hook**:
```javascript
const { refreshToken } = useAuth();
// Usage
await refreshToken();
```

### Logout

Invalidates the current authentication token.

- **URL**: `/auth/logout`
- **Method**: `POST`
- **Auth Required**: Yes

**Response**:
```json
{
  "data": {
    "success": true,
    "message": "Successfully logged out"
  }
}
```

**Service Method**:
```javascript
authService.logout();
```

**React Hook**:
```javascript
const { logout } = useAuth();
// Usage
await logout();
```

## Error Responses

All endpoints follow a standard error response format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      // Additional error details if available
    }
  }
}
```

Common error codes:

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `AUTHENTICATION_ERROR` | Authentication failure | 401 |
| `AUTHORIZATION_ERROR` | Insufficient permissions | 403 |
| `RESOURCE_NOT_FOUND` | Resource not found | 404 |
| `VALIDATION_ERROR` | Invalid request data | 400 |
| `DUPLICATE_RESOURCE` | Resource already exists | 409 |
| `INTERNAL_ERROR` | Internal server error | 500 |

**Service Error Handling**:
```javascript
try {
  const data = await repositoryService.getById('non-existent-id');
} catch (error) {
  console.error(error.message); // "Repository not found"
  console.error(error.status); // 404
  console.error(error.code); // "RESOURCE_NOT_FOUND"
}
```

**React Hook Error Handling**:
```javascript
const { data, loading, error } = useRepositories();

if (error) {
  console.error(error.message);
  console.error(error.status);
  console.error(error.code);
}
