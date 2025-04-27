import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Heading,
  Text,
  Button,
  VStack,
  Flex,
  Image,
  useColorModeValue,
} from '@chakra-ui/react';

/**
 * NotFound (404) Page Component
 * Displayed when a user navigates to a route that doesn't exist
 */
const NotFound = () => {
  // Color mode values
  const textColor = useColorModeValue('gray.600', 'gray.400');
  const headingColor = useColorModeValue('gray.800', 'white');
  
  return (
    <Flex
      minH="calc(100vh - 64px)"
      align="center"
      justify="center"
      py={10}
      px={6}
    >
      <VStack spacing={8} textAlign="center">
        <Heading
          as="h1"
          fontSize={{ base: '6xl', md: '8xl' }}
          fontWeight="bold"
          color={headingColor}
          lineHeight="none"
        >
          404
        </Heading>
        
        <VStack spacing={3}>
          <Heading as="h2" size="xl" color={headingColor}>
            Page Not Found
          </Heading>
          
          <Text fontSize="lg" color={textColor} maxW="md">
            The page you're looking for doesn't exist or has been moved.
          </Text>
        </VStack>
        
        <Box>
          <Text fontWeight="semibold" mb={2} color={textColor}>
            You might want to check out:
          </Text>
          
          <VStack spacing={2}>
            <Button as={RouterLink} to="/" colorScheme="brand" size="md" width="200px">
              Dashboard
            </Button>
            <Button as={RouterLink} to="/repositories" variant="outline" colorScheme="brand" size="md" width="200px">
              Repositories
            </Button>
            <Button as={RouterLink} to="/visualization" variant="outline" colorScheme="brand" size="md" width="200px">
              Visualization
            </Button>
          </VStack>
        </Box>
        
        <Text fontSize="sm" color={textColor} pt={6}>
          If you believe this is an error, please contact the administrator.
        </Text>
      </VStack>
    </Flex>
  );
};

export default NotFound;
