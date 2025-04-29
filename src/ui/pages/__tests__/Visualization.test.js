import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { rest } from 'msw';
import { server } from '../../../mocks/server';
import { renderWithProviders } from '../../utils/__tests__/test-utils';
import Visualization from '../Visualization';

// Mock the visualization renderer component
jest.mock('../../components/visualization/Renderer', () => {
  return function MockRenderer({ schemas, relationships, options }) {
    return (
      <div data-testid="visualization-renderer">
        <div>Schemas: {schemas.length}</div>
        <div>Relationships: {relationships.length}</div>
        <div>Layout: {options.layout}</div>
        <div>Show Field Types: {options.showFieldTypes ? 'Yes' : 'No'}</div>
        <div>Show Relationship Labels: {options.showRelationshipLabels ? 'Yes' : 'No'}</div>
        <div>Zoom Level: {options.zoomLevel}</div>
      </div>
    );
  };
});

/**
 * Integration tests for the Visualization component
 * 
 * These tests verify that the Visualization component:
 * - Renders a loading state initially
 * - Fetches schemas and relationships from the API
 * - Displays the visualization with the fetched data
 * - Allows changing layout options
 * - Toggles display settings like field types and relationship labels
 * - Displays an error message when API requests fail
 */
describe('Visualization', () => {
  beforeEach(() => {
    // Clear any previous mocks
    jest.clearAllMocks();
  });

  it('should render loading state initially', () => {
    renderWithProviders(<Visualization />);
    
    // Check for loading indicator
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
  });

  it('should fetch data and display visualization', async () => {
    renderWithProviders(<Visualization />);
    
    // Wait for visualization to render
    const renderer = await screen.findByTestId('visualization-renderer');
    expect(renderer).toBeInTheDocument();
    
    // Check schemas and relationships are passed to renderer
    expect(screen.getByText(/Schemas: [1-9]/)).toBeInTheDocument(); // At least 1 schema
    expect(screen.getByText(/Relationships: [1-9]/)).toBeInTheDocument(); // At least 1 relationship
  });

  it('should update layout when layout option is changed', async () => {
    renderWithProviders(<Visualization />);
    
    // Wait for visualization to render
    await screen.findByTestId('visualization-renderer');
    
    // Find default layout text
    expect(screen.getByText('Layout: force-directed')).toBeInTheDocument();
    
    // Find and click layout dropdown
    const layoutSelector = screen.getByLabelText('Select layout');
    userEvent.click(layoutSelector);
    
    // Select hierarchical layout
    const hierarchicalOption = await screen.findByText('Hierarchical');
    userEvent.click(hierarchicalOption);
    
    // Check layout is updated
    expect(screen.getByText('Layout: hierarchical')).toBeInTheDocument();
  });

  it('should toggle field types when toggle button is clicked', async () => {
    // Set initial state with showFieldTypes true
    const initialState = {
      ui: {
        visualizationOptions: {
          showFieldTypes: true
        }
      }
    };
    
    const { store } = renderWithProviders(<Visualization />, {
      preloadedState: initialState
    });
    
    // Wait for visualization to render
    await screen.findByTestId('visualization-renderer');
    
    // Check initial state
    expect(screen.getByText('Show Field Types: Yes')).toBeInTheDocument();
    
    // Find and click field types toggle
    const fieldTypesToggle = screen.getByLabelText('Show field types');
    userEvent.click(fieldTypesToggle);
    
    // Check state was updated
    await waitFor(() => {
      expect(screen.getByText('Show Field Types: No')).toBeInTheDocument();
    });
    
    // Check store was updated
    const state = store.getState();
    expect(state.ui.visualizationOptions.showFieldTypes).toBe(false);
  });

  it('should toggle relationship labels when toggle button is clicked', async () => {
    // Set initial state with showRelationshipLabels true
    const initialState = {
      ui: {
        visualizationOptions: {
          showRelationshipLabels: true
        }
      }
    };
    
    const { store } = renderWithProviders(<Visualization />, {
      preloadedState: initialState
    });
    
    // Wait for visualization to render
    await screen.findByTestId('visualization-renderer');
    
    // Check initial state
    expect(screen.getByText('Show Relationship Labels: Yes')).toBeInTheDocument();
    
    // Find and click relationship labels toggle
    const labelsToggle = screen.getByLabelText('Show relationship labels');
    userEvent.click(labelsToggle);
    
    // Check state was updated
    await waitFor(() => {
      expect(screen.getByText('Show Relationship Labels: No')).toBeInTheDocument();
    });
    
    // Check store was updated
    const state = store.getState();
    expect(state.ui.visualizationOptions.showRelationshipLabels).toBe(false);
  });

  it('should update zoom level when zoom controls are used', async () => {
    // Set initial state with zoomLevel 1
    const initialState = {
      ui: {
        visualizationOptions: {
          zoomLevel: 1
        }
      }
    };
    
    const { store } = renderWithProviders(<Visualization />, {
      preloadedState: initialState
    });
    
    // Wait for visualization to render
    await screen.findByTestId('visualization-renderer');
    
    // Check initial state
    expect(screen.getByText('Zoom Level: 1')).toBeInTheDocument();
    
    // Find and click zoom in button
    const zoomInButton = screen.getByLabelText('Zoom in');
    userEvent.click(zoomInButton);
    
    // Check state was updated
    await waitFor(() => {
      expect(screen.getByText('Zoom Level: 1.1')).toBeInTheDocument();
    });
    
    // Check store was updated
    let state = store.getState();
    expect(state.ui.visualizationOptions.zoomLevel).toBe(1.1);
    
    // Find and click zoom out button
    const zoomOutButton = screen.getByLabelText('Zoom out');
    userEvent.click(zoomOutButton);
    
    // Check state was updated back to 1
    await waitFor(() => {
      expect(screen.getByText('Zoom Level: 1')).toBeInTheDocument();
    });
    
    // Check store was updated
    state = store.getState();
    expect(state.ui.visualizationOptions.zoomLevel).toBe(1);
  });

  it('should reset visualization options when reset button is clicked', async () => {
    // Set initial state with custom options
    const initialState = {
      ui: {
        visualizationOptions: {
          layout: 'hierarchical',
          showFieldTypes: false,
          showRelationshipLabels: false,
          zoomLevel: 1.5
        }
      }
    };
    
    const { store } = renderWithProviders(<Visualization />, {
      preloadedState: initialState
    });
    
    // Wait for visualization to render
    await screen.findByTestId('visualization-renderer');
    
    // Check initial custom state
    expect(screen.getByText('Layout: hierarchical')).toBeInTheDocument();
    expect(screen.getByText('Show Field Types: No')).toBeInTheDocument();
    
    // Find and click reset button
    const resetButton = screen.getByLabelText('Reset visualization');
    userEvent.click(resetButton);
    
    // Check state was reset to defaults
    await waitFor(() => {
      expect(screen.getByText('Layout: force-directed')).toBeInTheDocument();
      expect(screen.getByText('Show Field Types: Yes')).toBeInTheDocument();
      expect(screen.getByText('Show Relationship Labels: Yes')).toBeInTheDocument();
      expect(screen.getByText('Zoom Level: 1')).toBeInTheDocument();
    });
    
    // Check store was updated
    const state = store.getState();
    expect(state.ui.visualizationOptions.layout).toBe('force-directed');
    expect(state.ui.visualizationOptions.showFieldTypes).toBe(true);
    expect(state.ui.visualizationOptions.showRelationshipLabels).toBe(true);
    expect(state.ui.visualizationOptions.zoomLevel).toBe(1);
  });

  it('should display error message when schemas API request fails', async () => {
    // Override the default handler to return an error
    server.use(
      rest.get('/api/schemas', (req, res, ctx) => {
        return res(
          ctx.status(500),
          ctx.json({ error: 'Failed to fetch schemas' })
        );
      })
    );
    
    renderWithProviders(<Visualization />);
    
    // Wait for error message to appear
    const errorMessage = await screen.findByText(/Failed to fetch schemas/i);
    expect(errorMessage).toBeInTheDocument();
    
    // Verify loading indicator is removed
    expect(screen.queryByTestId('loading-indicator')).not.toBeInTheDocument();
    
    // Verify visualization is not rendered
    expect(screen.queryByTestId('visualization-renderer')).not.toBeInTheDocument();
  });

  it('should display error message when relationships API request fails', async () => {
    // Override the default handler to return an error for relationships
    server.use(
      rest.get('/api/relationships', (req, res, ctx) => {
        return res(
          ctx.status(500),
          ctx.json({ error: 'Failed to fetch relationships' })
        );
      })
    );
    
    renderWithProviders(<Visualization />);
    
    // Wait for error message to appear
    const errorMessage = await screen.findByText(/Failed to fetch relationships/i);
    expect(errorMessage).toBeInTheDocument();
    
    // Verify loading indicator is removed
    expect(screen.queryByTestId('loading-indicator')).not.toBeInTheDocument();
    
    // Verify visualization is not rendered
    expect(screen.queryByTestId('visualization-renderer')).not.toBeInTheDocument();
  });
});
