# Changelog

All notable changes to the Data Dictionary Agency project will be documented in this file.

## [Unreleased]

### Added
- Web UI Framework implementation
  - Added React/Redux based UI architecture
  - Created core layout components (Header, Sidebar)
  - Implemented page components:
    - Dashboard
    - Repository Browser
    - Schema Viewer
    - Visualization
    - Settings
    - NotFound (404)
  - Set up Redux store with slices for:
    - Repositories
    - Schemas
    - Relationships
    - UI state
    - Authentication
  - Added Chakra UI for styling and component library
  - Created theme configuration for consistent styling
  - Implemented responsive layouts for all pages

## [0.1.0] - 2024-04-15

### Added
- Initial project setup
- Core architecture and directory structure
- Basic backend API implementation
- Format detection plugins:
  - JSON Schema
  - XML
  - Avro
  - Parquet
  - OpenAPI
  - GraphQL
  - SQL
  - CSV
  - ORC
  - Protobuf
- Type inference system for schema detection
- Relationship detection between schemas
- Repository management for external sources
- Core test suite
