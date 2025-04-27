import React, { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Heading,
  SimpleGrid,
  Flex,
  Button,
  Card,
  CardHeader,
  CardBody,
  CardFooter,
  Input,
  InputGroup,
  InputLeftElement,
  Text,
  Badge,
  Progress,
  VStack,
  HStack,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  useColorModeValue,
  Divider,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  IconButton,
  Spinner,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import { 
  fetchRepositories, 
  fetchRepositoryById 
} from '../store/slices/repositoriesSlice';
import { 
  fetchSchemasByRepository 
} from '../store/slices/schemasSlice';

/**
 * Repository Browser Component
 * Lists all repositories and displays details for the selected repository
 */
const RepositoryBrowser = () => {
  const { repoId } = useParams();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  
  // Redux state
  const { repositories, currentRepository, status: repoStatus, error: repoError } = useSelector(state => state.repositories);
  const { schemas, status: schemaStatus } = useSelector(state => state.schemas);
  
  // Local state
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredRepos, setFilteredRepos] = useState([]);
  
  // Color mode values
  const cardBg = useColorModeValue('white', 'gray.800');
  
  // Filter repositories based on search query
  useEffect(() => {
    if (repositories) {
      if (!searchQuery) {
        setFilteredRepos(repositories);
      } else {
        const query = searchQuery.toLowerCase();
        setFilteredRepos(
          repositories.filter(repo => 
            repo.name?.toLowerCase().includes(query) || 
            repo.description?.toLowerCase().includes(query)
          )
        );
      }
    }
  }, [searchQuery, repositories]);
  
  // Fetch repositories on component mount
  useEffect(() => {
    if (repoStatus === 'idle') {
      dispatch(fetchRepositories());
    }
  }, [dispatch, repoStatus]);
  
  // Fetch repository details when repoId changes
  useEffect(() => {
    if (repoId) {
      dispatch(fetchRepositoryById(repoId));
      dispatch(fetchSchemasByRepository(repoId));
    }
  }, [dispatch, repoId]);
  
  // Handle repository selection
  const selectRepository = (id) => {
    navigate(`/repositories/${id}`);
  };
  
  // Display repository list if no repository is selected
  if (!repoId) {
    return (
      <Box p={4}>
        <Flex justify="space-between" align="center" mb={6}>
          <Heading as="h1" size="xl">
            Repositories
          </Heading>
          <Button 
            colorScheme="brand" 
            as={RouterLink} 
            to="/repositories/add"
          >
            Add Repository
          </Button>
        </Flex>
        
        {/* Search and filters */}
        <Flex mb={6} gap={4} flexWrap="wrap">
          <InputGroup maxW="400px">
            <InputLeftElement pointerEvents="none">
              🔍
            </InputLeftElement>
            <Input 
              placeholder="Search repositories..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </InputGroup>
          
          <Menu>
            <MenuButton as={Button} variant="outline">
              Filter
            </MenuButton>
            <MenuList>
              <MenuItem>All Repositories</MenuItem>
              <MenuItem>Recently Added</MenuItem>
              <MenuItem>Most Schemas</MenuItem>
              <MenuItem>Format Type</MenuItem>
            </MenuList>
          </Menu>
        </Flex>
        
        {/* Repository list */}
        {repoStatus === 'loading' ? (
          <Flex justify="center" py={10}>
            <Spinner size="xl" color="brand.500" />
          </Flex>
        ) : repoError ? (
          <Alert status="error" borderRadius="md">
            <AlertIcon />
            {repoError}
          </Alert>
        ) : (
          <>
            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
              {filteredRepos?.map(repo => (
                <Card 
                  key={repo.id} 
                  bg={cardBg} 
                  boxShadow="md" 
                  cursor="pointer"
                  onClick={() => selectRepository(repo.id)}
                  transition="transform 0.2s, box-shadow 0.2s"
                  _hover={{ transform: 'translateY(-4px)', boxShadow: 'lg' }}
                >
                  <CardHeader pb={2}>
                    <Heading size="md">{repo.name}</Heading>
                  </CardHeader>
                  <CardBody py={2}>
                    <Text fontSize="sm" color="gray.500" noOfLines={2}>
                      {repo.description || 'No description provided.'}
                    </Text>
                    
                    <Box mt={3}>
                      <Text fontSize="xs" mb={1}>Schema Detection</Text>
                      <Progress value={repo.progress || 75} size="sm" colorScheme="brand" borderRadius="full" />
                    </Box>
                    
                    <HStack mt={3} spacing={2}>
                      <Badge colorScheme="green">
                        {repo.schemaCount || 0} schemas
                      </Badge>
                      <Badge colorScheme="purple">
                        {repo.formatCount || 0} formats
                      </Badge>
                    </HStack>
                  </CardBody>
                  <CardFooter pt={0}>
                    <Button size="sm" variant="ghost" colorScheme="brand">
                      View Details
                    </Button>
                  </CardFooter>
                </Card>
              ))}
              
              {/* Placeholder items if no repositories */}
              {(!filteredRepos || filteredRepos.length === 0) && (
                <Card bg={cardBg} boxShadow="md" p={6}>
                  <VStack spacing={4} align="center">
                    <Text>No repositories found.</Text>
                    <Button colorScheme="brand" as={RouterLink} to="/repositories/add">
                      Add Repository
                    </Button>
                  </VStack>
                </Card>
              )}
            </SimpleGrid>
          </>
        )}
      </Box>
    );
  }
  
  // Display repository details
  return (
    <Box p={4}>
      {/* Header with navigation */}
      <Flex mb={6} align="center">
        <Button 
          variant="ghost" 
          onClick={() => navigate('/repositories')} 
          mr={2}
        >
          ←
        </Button>
        <Heading as="h1" size="xl">
          {currentRepository?.name || 'Repository Details'}
        </Heading>
      </Flex>
      
      {repoStatus === 'loading' ? (
        <Flex justify="center" py={10}>
          <Spinner size="xl" color="brand.500" />
        </Flex>
      ) : (
        <>
          {/* Repository overview */}
          <Card bg={cardBg} mb={6} boxShadow="md">
            <CardBody>
              <VStack align="stretch" spacing={4}>
                <Text>{currentRepository?.description || 'No description provided.'}</Text>
                
                <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
                  <Box>
                    <Text fontWeight="medium">Schemas</Text>
                    <Text fontSize="2xl">{currentRepository?.schemaCount || schemas?.length || 0}</Text>
                  </Box>
                  <Box>
                    <Text fontWeight="medium">Formats</Text>
                    <Text fontSize="2xl">{currentRepository?.formatCount || 0}</Text>
                  </Box>
                  <Box>
                    <Text fontWeight="medium">Detected Relationships</Text>
                    <Text fontSize="2xl">{currentRepository?.relationshipCount || 0}</Text>
                  </Box>
                </SimpleGrid>
                
                <Box>
                  <Text fontWeight="medium" mb={1}>Processing Status</Text>
                  <Progress 
                    value={currentRepository?.progress || 75} 
                    size="sm" 
                    colorScheme="brand" 
                    borderRadius="full" 
                  />
                  <Text fontSize="sm" mt={1}>
                    {currentRepository?.progress === 100 
                      ? 'Processing complete' 
                      : 'Processing in progress...'}
                  </Text>
                </Box>
                
                <Divider />
                
                <HStack>
                  <Button colorScheme="brand" size="sm">
                    Refresh Schemas
                  </Button>
                  <Button colorScheme="brand" variant="outline" size="sm">
                    View Repository Source
                  </Button>
                </HStack>
              </VStack>
            </CardBody>
          </Card>
          
          {/* Repository content tabs */}
          <Tabs colorScheme="brand" isLazy>
            <TabList>
              <Tab>Schemas</Tab>
              <Tab>Relationships</Tab>
              <Tab>Visualizations</Tab>
              <Tab>Settings</Tab>
            </TabList>
            
            <TabPanels>
              <TabPanel p={0} pt={4}>
                {/* Schemas panel */}
                <Flex mb={4} justify="space-between" align="center">
                  <InputGroup maxW="400px">
                    <InputLeftElement pointerEvents="none">
                      🔍
                    </InputLeftElement>
                    <Input placeholder="Search schemas..." />
                  </InputGroup>
                  
                  <HStack>
                    <Menu>
                      <MenuButton as={Button} variant="outline" size="sm">
                        Filter by Format
                      </MenuButton>
                      <MenuList>
                        <MenuItem>All Formats</MenuItem>
                        <MenuItem>JSON</MenuItem>
                        <MenuItem>XML</MenuItem>
                        <MenuItem>SQL</MenuItem>
                        <MenuItem>GraphQL</MenuItem>
                        <MenuItem>Avro</MenuItem>
                      </MenuList>
                    </Menu>
                    
                    <Button colorScheme="brand" size="sm">
                      Upload Schema
                    </Button>
                  </HStack>
                </Flex>
                
                {schemaStatus === 'loading' ? (
                  <Flex justify="center" py={6}>
                    <Spinner color="brand.500" />
                  </Flex>
                ) : (
                  <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
                    {schemas?.map(schema => (
                      <Card 
                        key={schema.id} 
                        bg={cardBg} 
                        boxShadow="sm"
                        as={RouterLink}
                        to={`/schemas/${schema.id}`}
                        _hover={{ transform: 'translateY(-2px)', boxShadow: 'md' }}
                        transition="transform 0.2s, box-shadow 0.2s"
                      >
                        <CardBody>
                          <HStack mb={2}>
                            <Text fontSize="lg" fontWeight="medium" noOfLines={1}>
                              {schema.name}
                            </Text>
                            <Badge 
                              colorScheme={
                                schema.format === 'json' ? 'yellow' :
                                schema.format === 'sql' ? 'blue' :
                                schema.format === 'xml' ? 'green' :
                                schema.format === 'graphql' ? 'pink' :
                                schema.format === 'avro' ? 'purple' :
                                'gray'
                              }
                            >
                              {schema.format?.toUpperCase() || 'UNKNOWN'}
                            </Badge>
                          </HStack>
                          
                          <Text fontSize="sm" color="gray.500" noOfLines={2}>
                            {schema.description || 'No description available.'}
                          </Text>
                          
                          <HStack mt={3} spacing={2} wrap="wrap">
                            <Badge colorScheme="blue">
                              {schema.fieldCount || 0} fields
                            </Badge>
                            {schema.hasPrimaryKey && (
                              <Badge colorScheme="green">Has Primary Key</Badge>
                            )}
                            {schema.relationshipCount > 0 && (
                              <Badge colorScheme="purple">
                                {schema.relationshipCount} relationships
                              </Badge>
                            )}
                          </HStack>
                        </CardBody>
                      </Card>
                    ))}
                    
                    {/* Placeholder if no schemas */}
                    {(!schemas || schemas.length === 0) && !schemaStatus === 'loading' && (
                      <Card p={6} textAlign="center">
                        <Text mb={4}>No schemas found in this repository.</Text>
                        <Button colorScheme="brand" size="sm">
                          Upload Schema
                        </Button>
                      </Card>
                    )}
                  </SimpleGrid>
                )}
              </TabPanel>
              
              <TabPanel>
                {/* Relationships panel */}
                <Text>Relationship data will be displayed here.</Text>
              </TabPanel>
              
              <TabPanel>
                {/* Visualizations panel */}
                <Flex direction="column" align="center" justify="center" py={8}>
                  <Text mb={4}>
                    View interactive visualizations of your repository's schema relationships.
                  </Text>
                  <Button 
                    colorScheme="brand"
                    as={RouterLink}
                    to={`/visualization/${repoId}`}
                    size="lg"
                  >
                    Open Visualization
                  </Button>
                </Flex>
              </TabPanel>
              
              <TabPanel>
                {/* Settings panel */}
                <Card bg={cardBg}>
                  <CardHeader>
                    <Heading size="md">Repository Settings</Heading>
                  </CardHeader>
                  <CardBody>
                    <VStack spacing={4} align="start">
                      <Box width="100%">
                        <Text mb={2}>Repository Name</Text>
                        <Input defaultValue={currentRepository?.name} />
                      </Box>
                      
                      <Box width="100%">
                        <Text mb={2}>Description</Text>
                        <Input defaultValue={currentRepository?.description} />
                      </Box>
                      
                      <Box width="100%">
                        <Text mb={2}>URL</Text>
                        <Input defaultValue={currentRepository?.url} />
                      </Box>
                      
                      <HStack width="100%" pt={2}>
                        <Button colorScheme="brand">Save Changes</Button>
                        <Button variant="outline" colorScheme="red">
                          Delete Repository
                        </Button>
                      </HStack>
                    </VStack>
                  </CardBody>
                </Card>
              </TabPanel>
            </TabPanels>
          </Tabs>
        </>
      )}
    </Box>
  );
};

export default RepositoryBrowser;
