import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { rest } from 'msw';
import { server } from '../../../mocks/server';
import { renderWithProviders } from '../../utils/__tests__/test-utils';
import RepositoryBrowser from '../RepositoryBrowser';

/**
 * Integration tests for the Repository Browser component
 * 
 * These tests verify that the RepositoryBrowser component:
 * - Renders a loading state initially
 * - Fetches and displays repositories from the API
 * - Displays repository details when a repository is clicked
 * - Displays an error message when the API request fails
 * - Allows filtering repositories by search term
 */
describe('RepositoryBrowser', () => {
  beforeEach(() => {
    // Clear any previous mocks
    jest.clearAllMocks();
  });

  it('should render loading state initially', () => {
    renderWithProviders(<RepositoryBrowser />);
    
    // Check for loading indicator
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
  });

  it('should fetch and display repositories', async () => {
    renderWithProviders(<RepositoryBrowser />);
    
    // Wait for repositories to load
    const repo1 = await screen.findByText('Repository 1');
    const repo2 = await screen.findByText('Repository 2');
    
    // Verify repositories are displayed
    expect(repo1).toBeInTheDocument();
    expect(repo2).toBeInTheDocument();
    
    // Verify loading indicator is removed
    expect(screen.queryByTestId('loading-indicator')).not.toBeInTheDocument();
  });

  it('should display repository details when a repository is clicked', async () => {
    renderWithProviders(<RepositoryBrowser />);
    
    // Wait for repositories to load
    const repo1 = await screen.findByText('Repository 1');
    
    // Click on the first repository
    userEvent.click(repo1);
    
    // Wait for repository details to load
    const detailsHeading = await screen.findByText('Repository Details');
    expect(detailsHeading).toBeInTheDocument();
    
    // Check repository details are displayed
    expect(await screen.findByText('Repository 1')).toBeInTheDocument();
    expect(await screen.findByText(/Test repository 1 description/i)).toBeInTheDocument();
    
    // Check for schemas related to this repository
    expect(await screen.findByText(/Schemas:/i)).toBeInTheDocument();
  });

  it('should display error message when API request fails', async () => {
    // Override the default handler to return an error
    server.use(
      rest.get('/api/repositories', (req, res, ctx) => {
        return res(
          ctx.status(500),
          ctx.json({ error: 'Failed to fetch repositories' })
        );
      })
    );
    
    renderWithProviders(<RepositoryBrowser />);
    
    // Wait for error message to appear
    const errorMessage = await screen.findByText(/Failed to fetch repositories/i);
    expect(errorMessage).toBeInTheDocument();
    
    // Verify loading indicator is removed
    expect(screen.queryByTestId('loading-indicator')).not.toBeInTheDocument();
  });

  it('should filter repositories based on search input', async () => {
    renderWithProviders(<RepositoryBrowser />);
    
    // Wait for repositories to load
    await screen.findByText('Repository 1');
    await screen.findByText('Repository 2');
    
    // Find search input and type in it
    const searchInput = screen.getByPlaceholderText('Search repositories...');
    userEvent.type(searchInput, 'Repository 2');
    
    // Verify filtering works
    await waitFor(() => {
      expect(screen.queryByText('Repository 1')).not.toBeInTheDocument();
      expect(screen.getByText('Repository 2')).toBeInTheDocument();
    });
  });

  it('should clear search when clear button is clicked', async () => {
    renderWithProviders(<RepositoryBrowser />);
    
    // Wait for repositories to load
    await screen.findByText('Repository 1');
    await screen.findByText('Repository 2');
    
    // Find search input and type in it
    const searchInput = screen.getByPlaceholderText('Search repositories...');
    userEvent.type(searchInput, 'Repository 2');
    
    // Verify filtering works
    await waitFor(() => {
      expect(screen.queryByText('Repository 1')).not.toBeInTheDocument();
      expect(screen.getByText('Repository 2')).toBeInTheDocument();
    });
    
    // Find and click clear button
    const clearButton = screen.getByLabelText('Clear search');
    userEvent.click(clearButton);
    
    // Verify all repositories are displayed again
    await waitFor(() => {
      expect(screen.getByText('Repository 1')).toBeInTheDocument();
      expect(screen.getByText('Repository 2')).toBeInTheDocument();
    });
    
    // Verify search input is cleared
    expect(searchInput.value).toBe('');
  });

  it('should display empty state when no repositories match search', async () => {
    renderWithProviders(<RepositoryBrowser />);
    
    // Wait for repositories to load
    await screen.findByText('Repository 1');
    
    // Find search input and type non-matching search
    const searchInput = screen.getByPlaceholderText('Search repositories...');
    userEvent.type(searchInput, 'NonexistentRepo');
    
    // Verify empty state is displayed
    await waitFor(() => {
      expect(screen.getByText(/No repositories found/i)).toBeInTheDocument();
    });
  });

  it('should handle status filter selection', async () => {
    renderWithProviders(<RepositoryBrowser />);
    
    // Wait for repositories to load
    await screen.findByText('Repository 1');
    await screen.findByText('Repository 2');
    
    // Find and click status filter
    const statusFilter = screen.getByLabelText('Filter by status');
    userEvent.click(statusFilter);
    
    // Select 'Active' status
    const activeOption = await screen.findByText('Active');
    userEvent.click(activeOption);
    
    // Verify filtering works (Repository 1 is active)
    await waitFor(() => {
      expect(screen.getByText('Repository 1')).toBeInTheDocument();
      expect(screen.queryByText('Repository 2')).not.toBeInTheDocument();
    });
  });
});
