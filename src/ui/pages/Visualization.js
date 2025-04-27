import React, { useEffect, useState, useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useParams, useNavigate, useSearchParams, Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Heading,
  Flex,
  Button,
  Card,
  CardHeader,
  CardBody,
  Text,
  Badge,
  VStack,
  HStack,
  SimpleGrid,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Select,
  Checkbox,
  Divider,
  Spinner,
  Tooltip,
  useColorModeValue,
  IconButton,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Drawer,
  DrawerBody,
  DrawerFooter,
  DrawerHeader,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton,
  useDisclosure,
} from '@chakra-ui/react';
import {
  fetchRepositoryById,
  selectRepositories,
} from '../store/slices/repositoriesSlice';
import {
  fetchSchemasByRepository,
  fetchSchemaById,
  selectSchemas,
} from '../store/slices/schemasSlice';
import {
  fetchRelationshipsByRepository,
  fetchRelationshipsBySchema,
  selectRelationships,
} from '../store/slices/relationshipsSlice';
import {
  setVisualizationLayout,
  toggleFieldTypes,
  toggleRelationshipLabels,
  setZoomLevel,
  highlightEntities,
  clearHighlightedEntities,
  hideEntity,
  showEntity,
  resetVisualizationOptions,
  selectUi,
} from '../store/slices/uiSlice';

/**
 * Visualization Page Component
 * Integrates with the visualization modules to render schema relationships
 */
const Visualization = () => {
  // Router hooks
  const { repoId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const schemaId = searchParams.get('schema');
  
  // Redux
  const dispatch = useDispatch();
  const { currentRepository } = useSelector(selectRepositories);
  const { schemas, currentSchema } = useSelector(selectSchemas);
  const { relationships } = useSelector(selectRelationships);
  const { visualizationOptions } = useSelector(selectUi);
  
  // Local state
  const [isLoading, setIsLoading] = useState(true);
  const [selectedSchemas, setSelectedSchemas] = useState([]);
  const [selectedRelationships, setSelectedRelationships] = useState([]);
  const [error, setError] = useState(null);
  
  // Refs
  const visualizationContainerRef = useRef(null);
  
  // UI state
  const { isOpen, onOpen, onClose } = useDisclosure();
  
  // Color mode values
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  // Effects
  
  // Fetch repository data
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        if (repoId) {
          await dispatch(fetchRepositoryById(repoId)).unwrap();
          await dispatch(fetchSchemasByRepository(repoId)).unwrap();
          await dispatch(fetchRelationshipsByRepository(repoId)).unwrap();
        } else if (schemaId) {
          await dispatch(fetchSchemaById(schemaId)).unwrap();
          await dispatch(fetchRelationshipsBySchema(schemaId)).unwrap();
        } else {
          setError('No repository or schema specified');
        }
      } catch (err) {
        setError(err.message || 'Failed to load data');
      } finally {
        setIsLoading(false);
      }
    };
    
    loadData();
  }, [dispatch, repoId, schemaId]);
  
  // Initialize selected schemas
  useEffect(() => {
    if (schemas && schemas.length > 0) {
      if (schemaId && currentSchema) {
        setSelectedSchemas([currentSchema.id]);
      } else {
        // Select the first few schemas by default (limit to 5 for performance)
        setSelectedSchemas(schemas.slice(0, 5).map(schema => schema.id));
      }
    }
  }, [schemas, schemaId, currentSchema]);
  
  // Update selected relationships when schemas change
  useEffect(() => {
    if (relationships && relationships.length > 0 && selectedSchemas.length > 0) {
      // Select relationships where both source and target schemas are selected
      const relevantRelationships = relationships.filter(rel => 
        selectedSchemas.includes(rel.sourceSchemaId) && 
        selectedSchemas.includes(rel.targetSchemaId)
      );
      setSelectedRelationships(relevantRelationships.map(rel => rel.id));
    }
  }, [relationships, selectedSchemas]);
  
  // Initialize visualization when data is loaded
  useEffect(() => {
    if (!isLoading && schemas.length > 0 && relationships.length > 0 && selectedSchemas.length > 0) {
      // Here we would initialize the visualization using the actual visualization library
      // For now, we'll just simulate a delay
      const timer = setTimeout(() => {
        console.log('Visualization initialized');
      }, 500);
      
      return () => clearTimeout(timer);
    }
  }, [isLoading, schemas, relationships, selectedSchemas]);
  
  // Handlers
  
  // Toggle schema selection
  const handleSchemaToggle = (schemaId) => {
    setSelectedSchemas(prev => {
      if (prev.includes(schemaId)) {
        return prev.filter(id => id !== schemaId);
      } else {
        return [...prev, schemaId];
      }
    });
  };
  
  // Change visualization layout
  const handleLayoutChange = (layout) => {
    dispatch(setVisualizationLayout(layout));
  };
  
  // Toggle field types visibility
  const handleToggleFieldTypes = () => {
    dispatch(toggleFieldTypes());
  };
  
  // Toggle relationship labels visibility
  const handleToggleRelationshipLabels = () => {
    dispatch(toggleRelationshipLabels());
  };
  
  // Change zoom level
  const handleZoomChange = (value) => {
    dispatch(setZoomLevel(value));
  };
  
  // Highlight a schema
  const handleHighlightSchema = (schemaId) => {
    dispatch(highlightEntities(schemaId));
  };
  
  // Reset visualization options
  const handleResetVisualization = () => {
    dispatch(resetVisualizationOptions());
  };
  
  // Download visualization
  const handleDownload = (format) => {
    // This would be implemented with the actual visualization library
    console.log(`Downloading visualization as ${format}`);
    // Simulated download
    alert(`Visualization would be downloaded as ${format}`);
  };
  
  // Loading state
  if (isLoading) {
    return (
      <Flex justify="center" align="center" h="50vh">
        <Spinner size="xl" color="brand.500" />
      </Flex>
    );
  }
  
  // Error state
  if (error) {
    return (
      <Box p={4}>
        <Text color="red.500" mb={4}>{error}</Text>
        <Button onClick={() => navigate('/repositories')}>
          Browse Repositories
        </Button>
      </Box>
    );
  }
  
  return (
    <Box p={4}>
      {/* Header */}
      <Flex mb={6} justify="space-between" align="center" wrap="wrap" gap={2}>
        <VStack align="flex-start" spacing={0}>
          <Heading as="h1" size="xl">
            {currentRepository ? `${currentRepository.name} Visualization` : 
             currentSchema ? `${currentSchema.name} Visualization` : 
             'Data Visualization'}
          </Heading>
          <Text color="gray.500">
            {selectedSchemas.length} schemas and {selectedRelationships.length} relationships
          </Text>
        </VStack>
        
        <HStack spacing={3}>
          <Button colorScheme="brand" onClick={onOpen}>
            Settings
          </Button>
          
          <Menu>
            <MenuButton as={Button} variant="outline">
              Download
            </MenuButton>
            <MenuList>
              <MenuItem onClick={() => handleDownload('svg')}>SVG</MenuItem>
              <MenuItem onClick={() => handleDownload('png')}>PNG</MenuItem>
              <MenuItem onClick={() => handleDownload('pdf')}>PDF</MenuItem>
              <MenuItem onClick={() => handleDownload('json')}>JSON</MenuItem>
            </MenuList>
          </Menu>
          
          <Tooltip label="Reset Visualization">
            <IconButton
              aria-label="Reset Visualization"
              icon={<Text fontSize="xl">↺</Text>}
              onClick={handleResetVisualization}
            />
          </Tooltip>
        </HStack>
      </Flex>
      
      {/* Main content */}
      <Flex h="calc(100vh - 200px)" gap={4}>
        {/* Left panel - Schema selection */}
        <Card bg={cardBg} boxShadow="md" width="250px" flexShrink={0} overflowY="auto">
          <CardHeader pb={0}>
            <Heading size="md">Schemas</Heading>
          </CardHeader>
          <CardBody>
            <VStack align="stretch" spacing={2}>
              {schemas.map(schema => (
                <Flex 
                  key={schema.id}
                  py={2}
                  px={3}
                  borderRadius="md"
                  justify="space-between"
                  align="center"
                  bg={selectedSchemas.includes(schema.id) ? 'brand.50' : 'transparent'}
                  borderWidth={selectedSchemas.includes(schema.id) ? '1px' : '0'}
                  borderColor="brand.200"
                  _hover={{ bg: 'brand.50' }}
                  onClick={() => handleSchemaToggle(schema.id)}
                  cursor="pointer"
                >
                  <HStack>
                    <Checkbox 
                      isChecked={selectedSchemas.includes(schema.id)}
                      onChange={(e) => {
                        e.stopPropagation();
                        handleSchemaToggle(schema.id);
                      }}
                    />
                    <Text noOfLines={1} fontWeight={selectedSchemas.includes(schema.id) ? 'medium' : 'normal'}>
                      {schema.name}
                    </Text>
                  </HStack>
                  <Badge 
                    colorScheme={
                      schema.format === 'json' ? 'yellow' :
                      schema.format === 'sql' ? 'blue' :
                      schema.format === 'xml' ? 'green' :
                      schema.format === 'graphql' ? 'pink' :
                      schema.format === 'avro' ? 'purple' :
                      'gray'
                    }
                    fontSize="xs"
                  >
                    {schema.format?.toUpperCase() || 'UNKNOWN'}
                  </Badge>
                </Flex>
              ))}
              
              {schemas.length === 0 && (
                <Text textAlign="center" py={4}>
                  No schemas available
                </Text>
              )}
            </VStack>
          </CardBody>
        </Card>
        
        {/* Center panel - Visualization */}
        <Card bg={cardBg} boxShadow="md" flexGrow={1} position="relative">
          <CardBody p={0}>
            {/* Visualization tools overlay */}
            <Flex 
              position="absolute" 
              top={4} 
              right={4} 
              zIndex={1} 
              bg={cardBg} 
              boxShadow="md" 
              borderRadius="md" 
              p={2}
            >
              <HStack spacing={2}>
                <Tooltip label="Zoom In">
                  <IconButton
                    size="sm"
                    icon={<Text fontSize="md">+</Text>}
                    onClick={() => handleZoomChange(visualizationOptions.zoomLevel + 0.1)}
                  />
                </Tooltip>
                <Tooltip label="Zoom Out">
                  <IconButton
                    size="sm"
                    icon={<Text fontSize="md">-</Text>}
                    onClick={() => handleZoomChange(visualizationOptions.zoomLevel - 0.1)}
                  />
                </Tooltip>
                <Tooltip label="Reset View">
                  <IconButton
                    size="sm"
                    icon={<Text fontSize="md">⟲</Text>}
                    onClick={() => handleZoomChange(1)}
                  />
                </Tooltip>
              </HStack>
            </Flex>
            
            {/* Visualization canvas */}
            <Box 
              ref={visualizationContainerRef}
              width="100%" 
              height="100%" 
              bg={useColorModeValue('gray.50', 'gray.900')}
              borderRadius="md"
              overflow="hidden"
              position="relative"
            >
              {selectedSchemas.length === 0 ? (
                <Flex justify="center" align="center" height="100%">
                  <Text>Select schemas to visualize</Text>
                </Flex>
              ) : (
                <Flex justify="center" align="center" height="100%">
                  <Text>Visualization will be rendered here</Text>
                  {/* This is where the actual visualization would be rendered */}
                  {/* For now, let's just show a placeholder */}
                </Flex>
              )}
            </Box>
          </CardBody>
        </Card>
      </Flex>
      
      {/* Visualization settings drawer */}
      <Drawer isOpen={isOpen} placement="right" onClose={onClose} size="md">
        <DrawerOverlay />
        <DrawerContent>
          <DrawerCloseButton />
          <DrawerHeader borderBottomWidth="1px">
            Visualization Settings
          </DrawerHeader>
          
          <DrawerBody>
            <VStack spacing={6} align="stretch">
              <Box>
                <Heading size="sm" mb={2}>Layout</Heading>
                <Select 
                  value={visualizationOptions.layout}
                  onChange={(e) => handleLayoutChange(e.target.value)}
                >
                  <option value="force-directed">Force-Directed</option>
                  <option value="hierarchical">Hierarchical</option>
                  <option value="circular">Circular</option>
                  <option value="grid">Grid</option>
                </Select>
              </Box>
              
              <Box>
                <Heading size="sm" mb={2}>Display Options</Heading>
                <VStack align="start">
                  <Checkbox 
                    isChecked={visualizationOptions.showFieldTypes}
                    onChange={handleToggleFieldTypes}
                  >
                    Show Field Types
                  </Checkbox>
                  <Checkbox 
                    isChecked={visualizationOptions.showRelationshipLabels}
                    onChange={handleToggleRelationshipLabels}
                  >
                    Show Relationship Labels
                  </Checkbox>
                </VStack>
              </Box>
              
              <Box>
                <Heading size="sm" mb={2}>Zoom Level</Heading>
                <Slider 
                  value={visualizationOptions.zoomLevel} 
                  min={0.5} 
                  max={2} 
                  step={0.1}
                  onChange={handleZoomChange}
                >
                  <SliderTrack>
                    <SliderFilledTrack bg="brand.500" />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
                <Text textAlign="center" mt={1}>
                  {Math.round(visualizationOptions.zoomLevel * 100)}%
                </Text>
              </Box>
              
              <Divider />
              
              <Box>
                <Heading size="sm" mb={2}>Schema Visibility</Heading>
                <VStack align="stretch" maxH="200px" overflowY="auto">
                  {schemas.map(schema => (
                    <Checkbox 
                      key={schema.id}
                      isChecked={selectedSchemas.includes(schema.id)}
                      onChange={() => handleSchemaToggle(schema.id)}
                    >
                      {schema.name}
                    </Checkbox>
                  ))}
                </VStack>
              </Box>
              
              <Box>
                <Heading size="sm" mb={2}>Filters</Heading>
                <Tabs variant="enclosed" size="sm">
                  <TabList>
                    <Tab>Schema Types</Tab>
                    <Tab>Relationships</Tab>
                  </TabList>
                  <TabPanels>
                    <TabPanel>
                      <VStack align="start">
                        <Checkbox defaultChecked>JSON</Checkbox>
                        <Checkbox defaultChecked>SQL</Checkbox>
                        <Checkbox defaultChecked>XML</Checkbox>
                        <Checkbox defaultChecked>GraphQL</Checkbox>
                        <Checkbox defaultChecked>Avro</Checkbox>
                      </VStack>
                    </TabPanel>
                    <TabPanel>
                      <VStack align="start">
                        <Checkbox defaultChecked>Foreign Keys</Checkbox>
                        <Checkbox defaultChecked>References</Checkbox>
                        <Checkbox defaultChecked>Compositions</Checkbox>
                        <Checkbox defaultChecked>Inheritance</Checkbox>
                      </VStack>
                    </TabPanel>
                  </TabPanels>
                </Tabs>
              </Box>
            </VStack>
          </DrawerBody>
          
          <DrawerFooter borderTopWidth="1px">
            <Button variant="outline" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button colorScheme="brand" onClick={onClose}>
              Apply
            </Button>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>
    </Box>
  );
};

export default Visualization;
