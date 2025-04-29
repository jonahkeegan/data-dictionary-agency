import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChakraProvider } from '@chakra-ui/react';
import ErrorMessage from '../ErrorMessage';

/**
 * Unit tests for the ErrorMessage component
 * 
 * These tests verify that the ErrorMessage component:
 * - Renders the error message correctly
 * - Displays a retry button when onRetry is provided
 * - Calls the onRetry function when the retry button is clicked
 * - Displays a custom title when provided
 */
describe('ErrorMessage', () => {
  // Helper function to render with ChakraProvider
  const renderWithChakra = (ui) => {
    return render(
      <ChakraProvider>{ui}</ChakraProvider>
    );
  };

  it('should render error message', () => {
    renderWithChakra(<ErrorMessage message="Test error message" />);
    
    // Check if error message is displayed
    expect(screen.getByText('Test error message')).toBeInTheDocument();
    
    // Check if the default title is displayed
    expect(screen.getByText('Error')).toBeInTheDocument();
  });

  it('should render with custom title', () => {
    renderWithChakra(<ErrorMessage title="Custom Error Title" message="Test error message" />);
    
    // Check if custom title is displayed
    expect(screen.getByText('Custom Error Title')).toBeInTheDocument();
    expect(screen.getByText('Test error message')).toBeInTheDocument();
  });

  it('should render with retry button when onRetry is provided', () => {
    const handleRetry = jest.fn();
    renderWithChakra(<ErrorMessage message="Test error" onRetry={handleRetry} />);
    
    // Check if retry button is displayed
    const retryButton = screen.getByRole('button', { name: /retry/i });
    expect(retryButton).toBeInTheDocument();
  });

  it('should call onRetry when retry button is clicked', () => {
    const handleRetry = jest.fn();
    renderWithChakra(<ErrorMessage message="Test error" onRetry={handleRetry} />);
    
    // Click retry button
    const retryButton = screen.getByRole('button', { name: /retry/i });
    userEvent.click(retryButton);
    
    // Check if onRetry was called
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });

  it('should not display retry button when onRetry is not provided', () => {
    renderWithChakra(<ErrorMessage message="Test error message" />);
    
    // Check that retry button is not present
    expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument();
  });

  it('should render with icon by default', () => {
    renderWithChakra(<ErrorMessage message="Test error message" />);
    
    // Check that an error icon is present
    const icon = screen.getByTestId('error-icon');
    expect(icon).toBeInTheDocument();
  });

  it('should not render icon when showIcon is false', () => {
    renderWithChakra(
      <ErrorMessage 
        message="Test error message" 
        showIcon={false} 
      />
    );
    
    // Check that no error icon is present
    expect(screen.queryByTestId('error-icon')).not.toBeInTheDocument();
  });

  it('should apply custom styles when provided', () => {
    // This is a limited test since we can't easily check computed styles
    // But we can check that the component renders with custom styling props
    renderWithChakra(
      <ErrorMessage 
        message="Test error message"
        bg="red.100"
        color="red.800"
        data-testid="custom-styled-error"
      />
    );
    
    // Check that the component renders with the test ID
    expect(screen.getByTestId('custom-styled-error')).toBeInTheDocument();
  });
});
