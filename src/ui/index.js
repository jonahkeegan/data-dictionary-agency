import React from 'react';
import { createRoot } from 'react-dom/client';
import { Provider } from 'react-redux';
import { ChakraProvider } from '@chakra-ui/react';
import { BrowserRouter as Router } from 'react-router-dom';
import { store } from './store';
import { theme } from './theme';
import App from './App';

// Create root for React 18
const container = document.getElementById('root');
const root = createRoot(container);

// Render the application
root.render(
  <React.StrictMode>
    <Provider store={store}>
      <ChakraProvider theme={theme}>
        <Router>
          <App />
        </Router>
      </ChakraProvider>
    </Provider>
  </React.StrictMode>
);
