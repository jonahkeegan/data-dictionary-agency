# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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

- Updated service layer architecture documentation
- Enhanced error handling with standardized error formats
- Improved type definitions for API responses

### Fixed

- Fixed authentication token handling in API client
- Added proper cleanup for in-flight requests on component unmount
