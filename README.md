# Data Dictionary Agency (DDA)

A specialized data analysis tool designed to automatically scan GitHub repositories for structured data files, extract their schemas, map relationships between tables, and generate comprehensive documentation with interactive visualizations.

## Features

- GitHub repository scanning and analysis
- Multi-format detection system (supports 12 different data formats)
- Schema extraction with type inference
- Relationship mapping between data structures
- Interactive ER diagram visualization
- Comprehensive documentation generation
- Web interface for exploration and sharing
- Advanced caching with TTL and pattern-based invalidation
- Mock service layer for offline development

## Project Structure

```
dda/
├── .github/workflows/        # CI/CD configurations
├── docker/                   # Docker configurations
├── src/                      # Source code
│   ├── api/                  # API gateway and routing
│   ├── core/                 # Core application components
│   ├── db/                   # Database models and repositories
│   ├── repository/           # GitHub repository connector
│   ├── format_detection/     # Format detection framework
│   │   ├── plugins/          # Format parser plugins
│   │   └── core/             # Core detection engine
│   ├── ui/                   # Frontend application
│   │   ├── components/       # React UI components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── pages/            # Page components
│   │   ├── services/         # Service layer for API interaction
│   │   │   ├── api/          # API client and services
│   │   │   └── mock/         # Mock implementations for development
│   │   └── store/            # Redux state management
│   └── utils/                # Utility functions and helpers
└── tests/                    # Test suite
    ├── unit/                 # Unit tests
    ├── integration/          # Integration tests
    └── fixtures/             # Test fixtures
```

## Frontend Architecture

The frontend application uses a modern React architecture with:

- **React**: Component-based UI framework
- **Redux**: State management with slice-based organization
- **Chakra UI**: Component library for consistent styling
- **Service Layer**: Abstraction for API communication
  - **API Services**: RESTful service implementations
  - **Mock Services**: Development implementations with test data
  - **Custom Hooks**: React hooks for simplified data access
- **Caching System**: TTL-based caching with pattern invalidation
- **Circuit Breaker**: Protection against API failures

## Getting Started

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Git
- PostgreSQL (for local development)
- MongoDB (for local development)

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/jonahkeegan/data-dictionary-agency.git
   cd data-dictionary-agency
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

3. Build and start the development environment:
   ```bash
   docker-compose up -d
   ```

4. Run backend tests:
   ```bash
   docker-compose exec app pytest
   ```

5. Access the API documentation:
   ```
   http://localhost:8000/docs
   ```

### Frontend Development

1. Install Node.js dependencies:
   ```bash
   cd src/ui
   npm install
   ```

2. Start the frontend development server:
   ```bash
   npm run dev
   ```

3. Run frontend tests:
   ```bash
   npm test
   ```

4. Build for production:
   ```bash
   npm run build
   ```

5. The frontend application by default will:
   - Use mock services in development mode
   - Connect to the backend API in production mode
   - Toggle between modes using the `REACT_APP_USE_MOCK_SERVICES` environment variable or `?mock=true` URL parameter

## Architecture

### Backend Architecture

The DDA backend follows a modular microservices architecture with:
- Repository connector for GitHub integration
- Format detection engine with plugins for 12 formats
- Relationship analysis service
- Visualization engine for ER diagrams
- Documentation generator
- RESTful API layer
- Persistence layer for storing results

### Frontend Architecture

The frontend implements a layered architecture:

1. **Presentation Layer**:
   - React components for UI rendering
   - Chakra UI for styling and accessibility
   - Navigation using React Router

2. **State Management Layer**:
   - Redux for centralized state
   - Slice-based organization (repositories, schemas, formats)
   - Selectors for optimized data access

3. **Service Layer**:
   - Service Factory pattern
   - Abstract base service with shared functionality
   - Domain-specific services (repositories, schemas, formats, auth)
   - Mock service implementations for development/testing

4. **Communication Layer**:
   - Axios-based API client
   - Request/response interceptors
   - Error standardization
   - Request cancellation

5. **Optimization Layer**:
   - Advanced caching with TTL management
   - Pattern-based cache invalidation
   - Circuit breaker for API resilience
   - Request deduplication

For detailed documentation, see:
- [Service Layer Architecture](docs/service-layer-architecture.md)
- [Caching Strategy](docs/caching-strategy.md)
- [API Endpoints Catalog](docs/api-endpoints-catalog.md)

## License

[MIT License](LICENSE)
