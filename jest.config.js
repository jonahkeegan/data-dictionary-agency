/**
 * Jest Configuration for Data Dictionary Agency
 * 
 * Configures testing environment with the following features:
 * - React Testing Library for component testing
 * - Mock Service Worker for API mocking
 * - Redux Mock Store for state management testing
 * - Coverage reporting for all source files
 */
module.exports = {
  // Root directory: the root of your project
  rootDir: '.',
  
  // Test environment: jsdom for browser-like environment
  testEnvironment: 'jsdom',
  
  // Test paths: where to look for test files
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{js,jsx,ts,tsx}',
    '<rootDir>/src/**/*.{spec,test}.{js,jsx,ts,tsx}'
  ],
  
  // Module file extensions: which file types Jest should look for
  moduleFileExtensions: ['js', 'jsx', 'ts', 'tsx', 'json', 'node'],
  
  // Module name mapper: map file imports to mock files
  moduleNameMapper: {
    // Mock CSS modules
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    // Mock asset imports
    '\\.(jpg|jpeg|png|gif|svg|eot|otf|webp|ttf|woff|woff2|mp4|webm|wav|mp3|m4a|aac|oga)$': '<rootDir>/src/__mocks__/fileMock.js',
    // Path aliases if used in the project
    '^@/(.*)$': '<rootDir>/src/$1'
  },
  
  // Transform: what transformers to use for different file types
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': 'babel-jest'
  },
  
  // Setup files: run before each test file
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  
  // Coverage configuration
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/mocks/**',
    '!src/**/index.{js,jsx,ts,tsx}',
    '!src/**/main.{js,jsx,ts,tsx}',
    '!src/serviceWorker.js',
    '!<rootDir>/node_modules/'
  ],
  
  // Coverage directory
  coverageDirectory: '<rootDir>/coverage',
  
  // Coverage thresholds (optional)
  coverageThreshold: {
    global: {
      statements: 80,
      branches: 70,
      functions: 80,
      lines: 80
    }
  },
  
  // Watch plugins (optional)
  watchPlugins: [
    'jest-watch-typeahead/filename',
    'jest-watch-typeahead/testname'
  ],
  
  // Test timeout
  testTimeout: 10000, // 10 seconds
  
  // Verbose output
  verbose: true
};
