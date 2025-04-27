import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  SimpleGrid,
  Heading,
  Text,
  Card,
  CardHeader,
  CardBody,
  CardFooter,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  HStack,
  VStack,
  Badge,
  Button,
  Icon,
  Flex,
  Progress,
  useColorModeValue,
} from '@chakra-ui/react';
import { fetchRepositories } from '../store/slices/repositoriesSlice';

/**
 * Dashboard Page Component
 * Displays an overview of the application's data and status
 */
const Dashboard = () => {
  const dispatch = useDispatch();
  const { repositories, status: repoStatus } = useSelector((state) => state.repositories);
  
  // Color mode values
  const cardBg = useColorModeValue('white', 'gray.800');
  
  // Fetch repositories on component mount
  useEffect(() => {
    if (repoStatus === 'idle') {
      dispatch(fetchRepositories());
    }
  }, [dispatch, repoStatus]);
  
  return (
    <Box p={4}>
      <Heading as="h1" size="xl" mb={6}>
        Dashboard
      </Heading>
      
      {/* Stats Overview */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={5} mb={8}>
        <Card bg={cardBg} boxShadow="md">
          <CardBody>
            <Stat>
              <StatLabel>Repositories</StatLabel>
              <StatNumber>{repositories?.length || 0}</StatNumber>
              <StatHelpText>
                <Badge colorScheme="green">Active</Badge>
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>
        
        <Card bg={cardBg} boxShadow="md">
          <CardBody>
            <Stat>
              <StatLabel>Total Schemas</StatLabel>
              <StatNumber>42</StatNumber>
              <StatHelpText>
                Across 6 formats
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>
        
        <Card bg={cardBg} boxShadow="md">
          <CardBody>
            <Stat>
              <StatLabel>Detected Relationships</StatLabel>
              <StatNumber>18</StatNumber>
              <StatHelpText>
                <Badge colorScheme="blue">85% confidence</Badge>
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>
        
        <Card bg={cardBg} boxShadow="md">
          <CardBody>
            <Stat>
              <StatLabel>Schema Formats</StatLabel>
              <StatNumber>6</StatNumber>
              <StatHelpText>
                XML, JSON, SQL, etc.
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>
      
      {/* Recent Activity and Quick Actions */}
      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={8}>
        <Card bg={cardBg} boxShadow="md">
          <CardHeader>
            <Heading size="md">Recent Activity</Heading>
          </CardHeader>
          <CardBody>
            <VStack spacing={4} align="stretch">
              <HStack justify="space-between">
                <VStack align="start" spacing={0}>
                  <Text fontWeight="medium">Schema Parsed</Text>
                  <Text fontSize="sm" color="gray.500">users_schema.json</Text>
                </VStack>
                <Text fontSize="sm" color="gray.500">10 min ago</Text>
              </HStack>
              
              <HStack justify="space-between">
                <VStack align="start" spacing={0}>
                  <Text fontWeight="medium">Repository Added</Text>
                  <Text fontSize="sm" color="gray.500">user-service</Text>
                </VStack>
                <Text fontSize="sm" color="gray.500">2 hours ago</Text>
              </HStack>
              
              <HStack justify="space-between">
                <VStack align="start" spacing={0}>
                  <Text fontWeight="medium">Relationship Detected</Text>
                  <Text fontSize="sm" color="gray.500">users ↔ orders</Text>
                </VStack>
                <Text fontSize="sm" color="gray.500">3 hours ago</Text>
              </HStack>
              
              <HStack justify="space-between">
                <VStack align="start" spacing={0}>
                  <Text fontWeight="medium">Schema Updated</Text>
                  <Text fontSize="sm" color="gray.500">products_schema.json</Text>
                </VStack>
                <Text fontSize="sm" color="gray.500">Yesterday</Text>
              </HStack>
            </VStack>
          </CardBody>
          <CardFooter>
            <Button variant="ghost" size="sm" colorScheme="brand" as={RouterLink} to="/activity">
              View All Activity
            </Button>
          </CardFooter>
        </Card>
        
        <Card bg={cardBg} boxShadow="md">
          <CardHeader>
            <Heading size="md">Quick Actions</Heading>
          </CardHeader>
          <CardBody>
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
              <Button colorScheme="brand" variant="solid" size="md" as={RouterLink} to="/repositories/add">
                Add Repository
              </Button>
              
              <Button colorScheme="brand" variant="outline" size="md" as={RouterLink} to="/schemas/upload">
                Upload Schema
              </Button>
              
              <Button colorScheme="brand" variant="outline" size="md" as={RouterLink} to="/visualization">
                View Visualizations
              </Button>
              
              <Button colorScheme="brand" variant="outline" size="md" as={RouterLink} to="/documentation/generate">
                Generate Documentation
              </Button>
            </SimpleGrid>
          </CardBody>
        </Card>
      </SimpleGrid>
      
      {/* Recent Repositories */}
      <Box mt={8}>
        <Heading size="md" mb={4}>
          Recent Repositories
        </Heading>
        
        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={5}>
          {repositories?.slice(0, 3).map((repo) => (
            <Card key={repo?.id || Math.random()} bg={cardBg} boxShadow="md">
              <CardHeader pb={0}>
                <Heading size="sm">{repo?.name || 'Repository Name'}</Heading>
              </CardHeader>
              <CardBody>
                <Text fontSize="sm" noOfLines={2}>
                  {repo?.description || 'Repository description would go here with details about what this repository contains.'}
                </Text>
                
                <Box mt={3}>
                  <Text fontSize="xs" mb={1}>Schema Detection</Text>
                  <Progress value={repo?.progress || 75} size="sm" colorScheme="brand" borderRadius="full" />
                </Box>
                
                <HStack mt={3} spacing={2}>
                  <Badge colorScheme="green">
                    {repo?.schemaCount || 12} schemas
                  </Badge>
                  <Badge colorScheme="purple">
                    {repo?.formatCount || 3} formats
                  </Badge>
                </HStack>
              </CardBody>
              <CardFooter pt={0}>
                <Button size="sm" variant="link" colorScheme="brand" as={RouterLink} to={`/repositories/${repo?.id || 1}`}>
                  View Details
                </Button>
              </CardFooter>
            </Card>
          ))}
          
          {/* Placeholder cards if no repositories */}
          {(!repositories || repositories.length === 0) && repoStatus !== 'loading' && (
            <>
              <Card bg={cardBg} boxShadow="md">
                <CardHeader pb={0}>
                  <Heading size="sm">User Service</Heading>
                </CardHeader>
                <CardBody>
                  <Text fontSize="sm" noOfLines={2}>
                    Central user management service with authentication and profile data.
                  </Text>
                  
                  <Box mt={3}>
                    <Text fontSize="xs" mb={1}>Schema Detection</Text>
                    <Progress value={75} size="sm" colorScheme="brand" borderRadius="full" />
                  </Box>
                  
                  <HStack mt={3} spacing={2}>
                    <Badge colorScheme="green">12 schemas</Badge>
                    <Badge colorScheme="purple">3 formats</Badge>
                  </HStack>
                </CardBody>
                <CardFooter pt={0}>
                  <Button size="sm" variant="link" colorScheme="brand" as={RouterLink} to="/repositories/1">
                    View Details
                  </Button>
                </CardFooter>
              </Card>
              
              <Card bg={cardBg} boxShadow="md">
                <CardHeader pb={0}>
                  <Heading size="sm">Product Catalog</Heading>
                </CardHeader>
                <CardBody>
                  <Text fontSize="sm" noOfLines={2}>
                    Product catalog and inventory management system.
                  </Text>
                  
                  <Box mt={3}>
                    <Text fontSize="xs" mb={1}>Schema Detection</Text>
                    <Progress value={90} size="sm" colorScheme="brand" borderRadius="full" />
                  </Box>
                  
                  <HStack mt={3} spacing={2}>
                    <Badge colorScheme="green">18 schemas</Badge>
                    <Badge colorScheme="purple">4 formats</Badge>
                  </HStack>
                </CardBody>
                <CardFooter pt={0}>
                  <Button size="sm" variant="link" colorScheme="brand" as={RouterLink} to="/repositories/2">
                    View Details
                  </Button>
                </CardFooter>
              </Card>
              
              <Card bg={cardBg} boxShadow="md">
                <CardHeader pb={0}>
                  <Heading size="sm">Order Processing</Heading>
                </CardHeader>
                <CardBody>
                  <Text fontSize="sm" noOfLines={2}>
                    Order management and processing system integrated with payment providers.
                  </Text>
                  
                  <Box mt={3}>
                    <Text fontSize="xs" mb={1}>Schema Detection</Text>
                    <Progress value={60} size="sm" colorScheme="brand" borderRadius="full" />
                  </Box>
                  
                  <HStack mt={3} spacing={2}>
                    <Badge colorScheme="green">8 schemas</Badge>
                    <Badge colorScheme="purple">2 formats</Badge>
                  </HStack>
                </CardBody>
                <CardFooter pt={0}>
                  <Button size="sm" variant="link" colorScheme="brand" as={RouterLink} to="/repositories/3">
                    View Details
                  </Button>
                </CardFooter>
              </Card>
            </>
          )}
        </SimpleGrid>
        
        {repoStatus === 'loading' && (
          <Flex justify="center" mt={4}>
            <Text>Loading repositories...</Text>
          </Flex>
        )}
        
        <Flex justify="center" mt={6}>
          <Button as={RouterLink} to="/repositories" colorScheme="brand">
            View All Repositories
          </Button>
        </Flex>
      </Box>
    </Box>
  );
};

export default Dashboard;
