import React from 'react';
import { render, screen } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import LoadingIndicator from '../LoadingIndicator';

/**
 * Unit tests for the LoadingIndicator component
 * 
 * These tests verify that the LoadingIndicator component:
 * - Renders correctly with default props
 * - Displays a custom message when provided
 * - Applies different sizes and variants properly
 * - Can be customized with additional styling props
 */
describe('LoadingIndicator', () => {
  // Helper function to render with ChakraProvider
  const renderWithChakra = (ui) => {
    return render(
      <ChakraProvider>{ui}</ChakraProvider>
    );
  };

  it('should render with default props', () => {
    renderWithChakra(<LoadingIndicator />);
    
    // Check if spinner is displayed
    const spinner = screen.getByTestId('loading-indicator');
    expect(spinner).toBeInTheDocument();
    
    // Check if default text is displayed
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('should render with custom message', () => {
    renderWithChakra(<LoadingIndicator message="Custom loading message" />);
    
    // Check if custom message is displayed
    expect(screen.getByText('Custom loading message')).toBeInTheDocument();
  });

  it('should not display text when showText is false', () => {
    renderWithChakra(<LoadingIndicator showText={false} />);
    
    // Check that no loading text is displayed
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    
    // But spinner should still be present
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
  });

  it('should render with small size', () => {
    renderWithChakra(<LoadingIndicator size="sm" />);
    
    // Check that the spinner has the small size class
    const spinner = screen.getByTestId('loading-indicator');
    expect(spinner).toHaveAttribute('data-size', 'sm');
  });

  it('should render with large size', () => {
    renderWithChakra(<LoadingIndicator size="lg" />);
    
    // Check that the spinner has the large size class
    const spinner = screen.getByTestId('loading-indicator');
    expect(spinner).toHaveAttribute('data-size', 'lg');
  });

  it('should render with full page overlay', () => {
    renderWithChakra(<LoadingIndicator fullPage />);
    
    // Check if the full-page container is present
    const overlay = screen.getByTestId('loading-overlay');
    expect(overlay).toBeInTheDocument();
    
    // Check that the spinner is inside the overlay
    const spinner = screen.getByTestId('loading-indicator');
    expect(overlay).toContainElement(spinner);
  });

  it('should apply custom color when provided', () => {
    renderWithChakra(<LoadingIndicator color="blue.500" />);
    
    // Check that the spinner has the custom color attribute
    const spinner = screen.getByTestId('loading-indicator');
    expect(spinner).toHaveAttribute('data-color', 'blue.500');
  });

  it('should apply custom thickness when provided', () => {
    renderWithChakra(<LoadingIndicator thickness="5px" />);
    
    // Check that the spinner has the custom thickness
    const spinner = screen.getByTestId('loading-indicator');
    expect(spinner).toHaveAttribute('data-thickness', '5px');
  });

  it('should apply custom speed when provided', () => {
    renderWithChakra(<LoadingIndicator speed="2s" />);
    
    // Check that the spinner has the custom speed
    const spinner = screen.getByTestId('loading-indicator');
    expect(spinner).toHaveAttribute('data-speed', '2s');
  });

  it('should display centered content', () => {
    renderWithChakra(<LoadingIndicator centered />);
    
    // Check that the centered container is present
    const container = screen.getByTestId('loading-centered-container');
    expect(container).toBeInTheDocument();
  });

  it('should render with custom test ID when provided', () => {
    renderWithChakra(<LoadingIndicator data-testid="custom-loader" />);
    
    // Check that custom test ID is applied
    expect(screen.getByTestId('custom-loader')).toBeInTheDocument();
  });
});
