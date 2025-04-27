# Technical Context

This document outlines the technical stack, libraries, and technologies used in the Data Dictionary Agency.

## Technology Stack

### Frontend
- **React**: UI library for building the component-based interface
- **Redux**: State management library with Redux Toolkit for simplified Redux development
- **React Router**: Routing solution for the SPA architecture
- **Chakra UI**: Component library for styled and accessible UI elements
- **Axios**: HTTP client for API communication
- **D3.js**: Data visualization library for schema relationship graphs

### Backend
- **Python**: Primary backend language
- **FastAPI**: API framework for building the REST endpoints
- **SQLAlchemy**: ORM for database interactions
- **Pydantic**: Data validation and settings management
- **Alembic**: Database migration tool

### Data Processing
- **Pandas**: Data manipulation and analysis
- **NetworkX**: Graph analysis for relationship detection
- **NumPy**: Numerical operations support

### Testing
- **Jest**: JavaScript testing framework for frontend components
- **Testing Library**: Component testing utilities
- **Pytest**: Python testing framework for backend
- **Selenium**: End-to-end testing

### Development Tools
- **Webpack**: Module bundler for frontend assets
- **ESLint**: JavaScript linting
- **Prettier**: Code formatting
- **Poetry**: Python dependency management
- **Docker**: Containerization
- **GitHub Actions**: CI/CD pipeline

## UI Architecture

The frontend follows a modern React architecture with the following key patterns:

### Component Structure
- **Layout Components**: Reusable layout elements (Header, Sidebar)
- **Page Components**: Full page views (Dashboard, RepositoryBrowser, SchemaViewer, etc.)
- **Common Components**: Reusable UI elements shared across pages

### State Management
- **Redux Store**: Centralized state management
- **Redux Slices**: Feature-based state organization
  - `repositoriesSlice`: Repository data and operations
  - `schemasSlice`: Schema data and operations
  - `relationshipsSlice`: Relationship data and operations
  - `uiSlice`: UI state (theme, sidebar, etc.)
  - `authSlice`: Authentication state

### Data Flow
1. **API Services**: Communicate with backend endpoints
2. **Redux Thunks**: Handle async operations and API calls
3. **Redux Reducers**: Update state based on actions
4. **Selectors**: Access and derive data from state
5. **Components**: Consume and display data, dispatch actions

### Styling Approach
- **Chakra UI Theme**: Centralized theme configuration
- **Responsive Design**: Mobile-first approach with responsive layouts
- **Component-Based Styling**: Styles encapsulated within components

## API Structure

The backend API follows RESTful principles:

### Endpoints
- `/api/repositories`: Repository management
- `/api/schemas`: Schema management
- `/api/relationships`: Relationship management
- `/api/formats`: Format detection and information
- `/api/auth`: Authentication and user management

### Authentication
- JWT-based authentication
- Token refresh mechanism
- Role-based access control

## Deployment Architecture

- **Development**: Local Docker-based development environment
- **Staging**: Containerized deployment for testing
- **Production**: Kubernetes-based orchestration
  - API services
  - Database
  - Frontend static assets via CDN

## Database Architecture

- **PostgreSQL**: Primary relational database
- **Schema**:
  - `repositories`: External data sources
  - `schemas`: Detected data schemas
  - `relationships`: Connections between schemas
  - `users`: User information
  - `settings`: Application configuration

## Integration Points

- **GitHub API**: Repository access and management
- **Database Connectors**: Direct database analysis capabilities
- **File System**: Local file analysis
