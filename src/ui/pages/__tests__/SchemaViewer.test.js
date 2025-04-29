import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { rest } from 'msw';
import { server } from '../../../mocks/server';
import { renderWithProviders } from '../../utils/__tests__/test-utils';
import SchemaViewer from '../SchemaViewer';

/**
 * Integration tests for the Schema Viewer component
 * 
 * These tests verify that the SchemaViewer component:
 * - Renders a loading state initially
 * - Fetches and displays schemas from the API
 * - Displays schema details when a schema is clicked
 * - Displays relationships for the selected schema
 * - Displays an error message when the API request fails
 * - Allows filtering schemas by format
 */
describe('SchemaViewer', () => {
  beforeEach(() => {
    // Clear any previous mocks
    jest.clearAllMocks();
  });

  it('should render loading state initially', () => {
    renderWithProviders(<SchemaViewer />);
    
    // Check for loading indicator
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
  });

  it('should fetch and display schemas', async () => {
    renderWithProviders(<SchemaViewer />);
    
    // Wait for schemas to load
    const schema1 = await screen.findByText('Schema 1');
    const schema2 = await screen.findByText('Schema 2');
    
    // Verify schemas are displayed
    expect(schema1).toBeInTheDocument();
    expect(schema2).toBeInTheDocument();
    
    // Verify loading indicator is removed
    expect(screen.queryByTestId('loading-indicator')).not.toBeInTheDocument();
  });

  it('should display schema details when a schema is clicked', async () => {
    renderWithProviders(<SchemaViewer />);
    
    // Wait for schemas to load
    const schema1 = await screen.findByText('Schema 1');
    
    // Click on the first schema
    userEvent.click(schema1);
    
    // Wait for schema details to load
    const detailsHeading = await screen.findByText('Schema Details');
    expect(detailsHeading).toBeInTheDocument();
    
    // Check schema details are displayed
    expect(await screen.findByText('Schema 1')).toBeInTheDocument();
    expect(await screen.findByText(/Format:/i)).toBeInTheDocument();
    
    // Check for fields section
    expect(await screen.findByText(/Fields/i)).toBeInTheDocument();
  });

  it('should display relationships for the selected schema', async () => {
    renderWithProviders(<SchemaViewer />);
    
    // Wait for schemas to load
    const schema1 = await screen.findByText('Schema 1');
    
    // Click on the first schema
    userEvent.click(schema1);
    
    // Wait for schema details to load
    await screen.findByText('Schema Details');
    
    // Go to relationships tab
    const relationshipsTab = await screen.findByRole('tab', { name: /relationships/i });
    userEvent.click(relationshipsTab);
    
    // Check relationships are displayed
    await waitFor(() => {
      expect(screen.getByText(/Relationships/i)).toBeInTheDocument();
    });
    
    // Verify a relationship is displayed (specific text will depend on your component implementation)
    const relationshipItems = await screen.findAllByTestId('relationship-item');
    expect(relationshipItems.length).toBeGreaterThan(0);
  });

  it('should display error message when API request fails', async () => {
    // Override the default handler to return an error
    server.use(
      rest.get('/api/schemas', (req, res, ctx) => {
        return res(
          ctx.status(500),
          ctx.json({ error: 'Failed to fetch schemas' })
        );
      })
    );
    
    renderWithProviders(<SchemaViewer />);
    
    // Wait for error message to appear
    const errorMessage = await screen.findByText(/Failed to fetch schemas/i);
    expect(errorMessage).toBeInTheDocument();
    
    // Verify loading indicator is removed
    expect(screen.queryByTestId('loading-indicator')).not.toBeInTheDocument();
  });

  it('should filter schemas based on format selection', async () => {
    renderWithProviders(<SchemaViewer />);
    
    // Wait for schemas to load
    await screen.findByText('Schema 1');
    
    // Find and click format filter
    const formatFilter = screen.getByLabelText('Filter by format');
    userEvent.click(formatFilter);
    
    // Select 'JSON' format (match expected format from the first schema)
    const jsonOption = await screen.findByText('JSON');
    userEvent.click(jsonOption);
    
    // Verify filtering works
    await waitFor(() => {
      // This assumes Schema 1 is JSON format, adjust based on your mock data
      expect(screen.getByText('Schema 1')).toBeInTheDocument();
      // This assumes Schema 2 is not JSON format, adjust based on your mock data
      expect(screen.queryByText('Schema 2')).not.toBeInTheDocument();
    });
  });

  it('should display empty state when no schemas match filter', async () => {
    renderWithProviders(<SchemaViewer />);
    
    // Wait for schemas to load
    await screen.findByText('Schema 1');
    
    // Use search filter with non-matching text
    const searchInput = screen.getByPlaceholderText('Search schemas...');
    userEvent.type(searchInput, 'NonexistentSchema');
    
    // Verify empty state is displayed
    await waitFor(() => {
      expect(screen.getByText(/No schemas found/i)).toBeInTheDocument();
    });
  });

  it('should load schemas for a specific repository when repositoryId is provided', async () => {
    // Setup with a repository ID in the initial route
    renderWithProviders(<SchemaViewer />, {
      routePath: ['/schemas?repositoryId=repo-1']
    });
    
    // Wait for schemas to load
    await screen.findByText('Schema 1');
    
    // Verify filter chip for repository is shown
    expect(screen.getByText(/Repository/i)).toBeInTheDocument();
    
    // Verify that the correct API call was made (this is indirectly tested 
    // by checking if schemas are displayed)
    await waitFor(() => {
      expect(screen.queryByTestId('loading-indicator')).not.toBeInTheDocument();
    });
  });

  it('should clear format filter when clear button is clicked', async () => {
    renderWithProviders(<SchemaViewer />);
    
    // Wait for schemas to load
    await screen.findByText('Schema 1');
    await screen.findByText('Schema 2');
    
    // Find and click format filter
    const formatFilter = screen.getByLabelText('Filter by format');
    userEvent.click(formatFilter);
    
    // Select 'JSON' format
    const jsonOption = await screen.findByText('JSON');
    userEvent.click(jsonOption);
    
    // Wait for filter to apply
    await waitFor(() => {
      expect(screen.queryByText('Schema 2')).not.toBeInTheDocument();
    });
    
    // Find and click clear filter button
    const clearButton = screen.getByLabelText('Clear format filter');
    userEvent.click(clearButton);
    
    // Verify all schemas are displayed again
    await waitFor(() => {
      expect(screen.getByText('Schema 1')).toBeInTheDocument();
      expect(screen.getByText('Schema 2')).toBeInTheDocument();
    });
  });
});
