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
│   └── utils/                # Utility functions and helpers
└── tests/                    # Test suite
    ├── unit/                 # Unit tests
    ├── integration/          # Integration tests
    └── fixtures/             # Test fixtures
```

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

4. Run tests:
   ```bash
   docker-compose exec app pytest
   ```

5. Access the API documentation:
   ```
   http://localhost:8000/docs
   ```

## Architecture

The DDA follows a modular microservices architecture with:
- Repository connector for GitHub integration
- Format detection engine with plugins for 12 formats
- Relationship analysis service
- Visualization engine for ER diagrams
- Documentation generator
- Web application layer
- Persistence layer for storing results

## License

[MIT License](LICENSE)
