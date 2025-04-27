import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, Flex } from '@chakra-ui/react';

// Layout components
import Header from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';

// Pages
import Dashboard from './pages/Dashboard';
import RepositoryBrowser from './pages/RepositoryBrowser';
import SchemaViewer from './pages/SchemaViewer';
import Visualization from './pages/Visualization';
import Settings from './pages/Settings';
import NotFound from './pages/NotFound';

/**
 * Main Application Component
 * Handles routing and layout structure
 */
const App = () => {
  return (
    <Flex direction="column" h="100vh">
      <Header />
      <Flex flex="1" overflow="hidden">
        <Sidebar />
        <Box flex="1" p={4} overflow="auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/repositories" element={<RepositoryBrowser />} />
            <Route path="/repositories/:repoId" element={<RepositoryBrowser />} />
            <Route path="/schemas/:schemaId" element={<SchemaViewer />} />
            <Route path="/visualization" element={<Visualization />} />
            <Route path="/visualization/:repoId" element={<Visualization />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/404" element={<NotFound />} />
            <Route path="*" element={<Navigate to="/404" replace />} />
          </Routes>
        </Box>
      </Flex>
    </Flex>
  );
};

export default App;
