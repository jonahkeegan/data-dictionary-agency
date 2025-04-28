# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Implemented Redux integration with service layer
  - Created dedicated Redux slices for repositories, schemas, relationships, and formats
  - Implemented async thunks that utilize service methods
  - Added standardized state management patterns
  - Implemented selectors for efficient state access
  - Created filtering and search capabilities within reducers

- Created comprehensive React hooks system
  - Implemented useReduxAction and useReduxThunk utility hooks
  - Created domain-specific hooks (useRepositories, useSchemas, useRelationships, useFormats)
  - Added entity-specific hooks (useRepository, useSchema, useRelationship, useFormat)
  - Implemented relationship-focused hooks (useRelationshipsBySchema, useRelationshipsByRepository)
  - Created utility hooks like useFormatDetector for specialized needs
  - Added automatic data loading patterns with loadImmediately options
  - Implemented consistent loading/error state handling

- Created comprehensive testing framework
  - Added unit tests for Redux slices with mock store
  - Implemented hook testing with @testing-library/react-hooks
  - Created unit tests for API client and interceptors
  - Implemented tests for BaseService core functionality
  - Added tests for RelationshipService implementation
  - Created tests for cache management system
  - Implemented tests for circuit breaker pattern
  - Added tests for request cancellation functionality
  - Implemented mock service implementations for testing

- Implemented API Client Architecture with Axios
  - Added environment-specific configuration management
  - Created centralized API client factory
  - Implemented request/response interceptors
  - Added standardized error handling
  - Integrated request cancellation support
  - Added automatic retry mechanism for transient failures

- Implemented advanced API client capabilities
  - Added circuit breaker pattern for resilience against API failures
  - Created sophisticated caching system with TTL and pattern-based invalidation
  - Added in-flight request deduplication
  - Implemented token refresh handling for authentication

- Created comprehensive service layer
  - Implemented BaseService abstract class with common functionality
  - Created RepositoryService for repository-related operations
  - Created SchemaService for schema-related operations
  - Created FormatService for format detection and conversion
  - Implemented AuthService for authentication and user management
  - Created ServiceFactory for centralized service instance management

- Developed mock services for development/testing
  - Created MockRepositoryService with realistic repository data
  - Created MockSchemaService with realistic schema data
  - Created MockFormatService with format detection and conversion
  - Implemented MockAuthService with simulated authentication
  - Added centralized mock data and utilities
  - Created MockServiceFactory for mock service management
  - Added controllable network conditions (delay, failure rate)

### Changed

- Updated service layer architecture documentation with Redux and hooks patterns
- Enhanced component integration examples in documentation
- Improved test coverage for service layer
- Enhanced error handling with standardized error formats
- Improved type definitions for API responses

### Fixed

- Fixed authentication token handling in API client
- Added proper cleanup for in-flight requests on component unmount
