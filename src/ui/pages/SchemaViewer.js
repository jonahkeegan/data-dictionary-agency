import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
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
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  useColorModeValue,
  Divider,
  Spinner,
  Alert,
  AlertIcon,
  Code,
  Tag,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  SimpleGrid,
} from '@chakra-ui/react';
import { fetchSchemaById } from '../store/slices/schemasSlice';
import { fetchRelationshipsBySchema } from '../store/slices/relationshipsSlice';

/**
 * Schema Viewer Component
 * Displays detailed information about a specific schema
 */
const SchemaViewer = () => {
  const { schemaId } = useParams();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  
  // Redux state
  const { currentSchema, status: schemaStatus, error: schemaError } = useSelector(state => state.schemas);
  const { relationships, status: relStatus } = useSelector(state => state.relationships);
  
  // Color mode values
  const cardBg = useColorModeValue('white', 'gray.800');
  const codeBg = useColorModeValue('gray.50', 'gray.700');
  
  // Fetch schema details when schemaId changes
  useEffect(() => {
    if (schemaId) {
      dispatch(fetchSchemaById(schemaId));
      dispatch(fetchRelationshipsBySchema(schemaId));
    }
  }, [dispatch, schemaId]);
  
  // Loading state
  if (schemaStatus === 'loading') {
    return (
      <Flex justify="center" align="center" h="50vh">
        <Spinner size="xl" color="brand.500" />
      </Flex>
    );
  }
  
  // Error state
  if (schemaError) {
    return (
      <Box p={4}>
        <Alert status="error" borderRadius="md">
          <AlertIcon />
          {schemaError}
        </Alert>
        <Button mt={4} onClick={() => navigate(-1)}>
          Go Back
        </Button>
      </Box>
    );
  }
  
  // Empty state
  if (!currentSchema) {
    return (
      <Box p={4}>
        <Alert status="info" borderRadius="md">
          <AlertIcon />
          No schema found with ID: {schemaId}
        </Alert>
        <Button mt={4} as={RouterLink} to="/repositories">
          Browse Repositories
        </Button>
      </Box>
    );
  }
  
  return (
    <Box p={4}>
      {/* Header with navigation */}
      <Flex mb={6} align="center">
        <Button 
          variant="ghost" 
          onClick={() => navigate(-1)} 
          mr={2}
        >
          ←
        </Button>
        <VStack align="flex-start" spacing={0}>
          <Heading as="h1" size="xl">
            {currentSchema.name || 'Schema Details'}
          </Heading>
          {currentSchema.repository && (
            <Text color="gray.500">
              Repository:{' '}
              <RouterLink to={`/repositories/${currentSchema.repositoryId}`}>
                <Text as="span" color="brand.500">
                  {currentSchema.repository}
                </Text>
              </RouterLink>
            </Text>
          )}
        </VStack>
      </Flex>
      
      {/* Schema overview */}
      <Card bg={cardBg} mb={6} boxShadow="md">
        <CardBody>
          <VStack align="stretch" spacing={4}>
            <Flex justify="space-between" align="center">
              <HStack spacing={2}>
                <Badge 
                  colorScheme={
                    currentSchema.format === 'json' ? 'yellow' :
                    currentSchema.format === 'sql' ? 'blue' :
                    currentSchema.format === 'xml' ? 'green' :
                    currentSchema.format === 'graphql' ? 'pink' :
                    currentSchema.format === 'avro' ? 'purple' :
                    'gray'
                  }
                  fontSize="md"
                  px={2}
                  py={1}
                >
                  {currentSchema.format?.toUpperCase() || 'UNKNOWN'}
                </Badge>
                <Badge colorScheme="brand" fontSize="md" px={2} py={1}>
                  {currentSchema.fieldCount || 0} Fields
                </Badge>
              </HStack>
              
              <HStack>
                <Button size="sm" colorScheme="brand" as={RouterLink} to={`/visualization?schema=${schemaId}`}>
                  Visualize
                </Button>
                <Button size="sm" colorScheme="brand" variant="outline">
                  Export
                </Button>
              </HStack>
            </Flex>
            
            <Text>{currentSchema.description || 'No description provided.'}</Text>
            
            {currentSchema.path && (
              <Text fontSize="sm" color="gray.500">
                Path: {currentSchema.path}
              </Text>
            )}
            
            <Divider />
            
            <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
              <Box>
                <Text fontWeight="medium">Format</Text>
                <Text>{currentSchema.format?.toUpperCase() || 'Unknown'}</Text>
              </Box>
              <Box>
                <Text fontWeight="medium">Last Updated</Text>
                <Text>{currentSchema.updatedAt || 'Unknown'}</Text>
              </Box>
              <Box>
                <Text fontWeight="medium">Detected Relationships</Text>
                <Text>{relationships?.length || 0}</Text>
              </Box>
            </SimpleGrid>
          </VStack>
        </CardBody>
      </Card>
      
      {/* Schema content tabs */}
      <Tabs colorScheme="brand" isLazy>
        <TabList>
          <Tab>Fields</Tab>
          <Tab>Relationships</Tab>
          <Tab>Source</Tab>
          <Tab>Documentation</Tab>
        </TabList>
        
        <TabPanels>
          <TabPanel p={0} pt={4}>
            {/* Fields panel */}
            <Card bg={cardBg} boxShadow="md">
              <CardHeader pb={0}>
                <Heading size="md">Fields</Heading>
              </CardHeader>
              <CardBody>
                <Table variant="simple">
                  <Thead>
                    <Tr>
                      <Th>Name</Th>
                      <Th>Type</Th>
                      <Th>Constraints</Th>
                      <Th>Description</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {currentSchema.fields?.map((field, index) => (
                      <Tr key={index}>
                        <Td fontWeight={field.isPrimary ? 'bold' : 'normal'}>
                          <HStack>
                            <Text>{field.name}</Text>
                            {field.isPrimary && <Badge colorScheme="green">PK</Badge>}
                            {field.isForeign && <Badge colorScheme="purple">FK</Badge>}
                          </HStack>
                        </Td>
                        <Td>
                          <Tag colorScheme={
                            field.type?.toLowerCase().includes('string') ? 'green' :
                            field.type?.toLowerCase().includes('int') ? 'blue' :
                            field.type?.toLowerCase().includes('date') ? 'orange' :
                            field.type?.toLowerCase().includes('bool') ? 'purple' :
                            field.type?.toLowerCase().includes('float') ? 'cyan' :
                            'gray'
                          }>
                            {field.type || 'unknown'}
                          </Tag>
                        </Td>
                        <Td>
                          <HStack spacing={1}>
                            {field.nullable === false && <Badge colorScheme="red">Required</Badge>}
                            {field.unique && <Badge colorScheme="blue">Unique</Badge>}
                            {field.maxLength && <Badge colorScheme="teal">Max: {field.maxLength}</Badge>}
                          </HStack>
                        </Td>
                        <Td>{field.description || '-'}</Td>
                      </Tr>
                    ))}
                    
                    {/* Placeholder if no fields */}
                    {(!currentSchema.fields || currentSchema.fields.length === 0) && (
                      <Tr>
                        <Td colSpan={4} textAlign="center" py={4}>
                          No fields found in this schema.
                        </Td>
                      </Tr>
                    )}
                  </Tbody>
                </Table>
              </CardBody>
            </Card>
          </TabPanel>
          
          <TabPanel p={0} pt={4}>
            {/* Relationships panel */}
            <Card bg={cardBg} boxShadow="md">
              <CardHeader pb={0}>
                <Heading size="md">Relationships</Heading>
              </CardHeader>
              <CardBody>
                {relStatus === 'loading' ? (
                  <Flex justify="center" py={6}>
                    <Spinner color="brand.500" />
                  </Flex>
                ) : relationships && relationships.length > 0 ? (
                  <Table variant="simple">
                    <Thead>
                      <Tr>
                        <Th>Type</Th>
                        <Th>Related Schema</Th>
                        <Th>Fields</Th>
                        <Th>Confidence</Th>
                      </Tr>
                    </Thead>
                    <Tbody>
                      {relationships.map((rel, index) => (
                        <Tr key={index}>
                          <Td>
                            <Badge 
                              colorScheme={
                                rel.type === 'foreignKey' ? 'green' :
                                rel.type === 'reference' ? 'blue' :
                                rel.type === 'composition' ? 'purple' :
                                'gray'
                              }
                            >
                              {rel.type || 'Unknown'}
                            </Badge>
                          </Td>
                          <Td>
                            <RouterLink to={`/schemas/${rel.relatedSchemaId}`}>
                              <Text color="brand.500">{rel.relatedSchemaName}</Text>
                            </RouterLink>
                          </Td>
                          <Td>
                            <Text>{rel.sourceField} → {rel.targetField}</Text>
                          </Td>
                          <Td>
                            <Badge 
                              colorScheme={
                                (rel.confidence >= 0.8) ? 'green' :
                                (rel.confidence >= 0.5) ? 'yellow' :
                                'red'
                              }
                            >
                              {`${Math.round(rel.confidence * 100)}%`}
                            </Badge>
                          </Td>
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                ) : (
                  <Flex py={4} justify="center">
                    <Text>No relationships detected for this schema.</Text>
                  </Flex>
                )}
              </CardBody>
            </Card>
          </TabPanel>
          
          <TabPanel p={0} pt={4}>
            {/* Source panel */}
            <Card bg={cardBg} boxShadow="md">
              <CardHeader pb={0}>
                <Heading size="md">Source</Heading>
              </CardHeader>
              <CardBody>
                <Box 
                  bg={codeBg} 
                  p={4} 
                  borderRadius="md" 
                  fontFamily="mono"
                  overflowX="auto"
                  whiteSpace="pre"
                  fontSize="sm"
                >
                  {currentSchema.sourceContent || 'Source content not available'}
                </Box>
              </CardBody>
            </Card>
          </TabPanel>
          
          <TabPanel p={0} pt={4}>
            {/* Documentation panel */}
            <Card bg={cardBg} boxShadow="md">
              <CardHeader pb={0}>
                <HStack justify="space-between">
                  <Heading size="md">Documentation</Heading>
                  <Button size="sm" colorScheme="brand">
                    Export Documentation
                  </Button>
                </HStack>
              </CardHeader>
              <CardBody>
                <VStack align="stretch" spacing={6}>
                  <Box>
                    <Heading size="sm" mb={2}>Overview</Heading>
                    <Text>{currentSchema.description || 'No description provided.'}</Text>
                  </Box>
                  
                  <Box>
                    <Heading size="sm" mb={2}>Schema Information</Heading>
                    <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                      <Box>
                        <Text fontWeight="medium">Name</Text>
                        <Text>{currentSchema.name}</Text>
                      </Box>
                      <Box>
                        <Text fontWeight="medium">Format</Text>
                        <Text>{currentSchema.format?.toUpperCase() || 'Unknown'}</Text>
                      </Box>
                      <Box>
                        <Text fontWeight="medium">Path</Text>
                        <Text>{currentSchema.path || 'Unknown'}</Text>
                      </Box>
                      <Box>
                        <Text fontWeight="medium">Fields</Text>
                        <Text>{currentSchema.fieldCount || 0}</Text>
                      </Box>
                    </SimpleGrid>
                  </Box>
                  
                  <Box>
                    <Heading size="sm" mb={2}>Field Definitions</Heading>
                    <Accordion allowMultiple defaultIndex={[0]}>
                      {currentSchema.fields?.map((field, index) => (
                        <AccordionItem key={index}>
                          <h2>
                            <AccordionButton>
                              <Box flex="1" textAlign="left" fontWeight="medium">
                                {field.name}
                                {field.isPrimary && (
                                  <Badge ml={2} colorScheme="green">Primary Key</Badge>
                                )}
                              </Box>
                              <AccordionIcon />
                            </AccordionButton>
                          </h2>
                          <AccordionPanel pb={4}>
                            <VStack align="stretch" spacing={2}>
                              <Box>
                                <Text fontWeight="medium">Type</Text>
                                <Text>{field.type || 'Unknown'}</Text>
                              </Box>
                              
                              <Box>
                                <Text fontWeight="medium">Description</Text>
                                <Text>{field.description || 'No description available.'}</Text>
                              </Box>
                              
                              <Box>
                                <Text fontWeight="medium">Constraints</Text>
                                <HStack spacing={2} mt={1}>
                                  {field.nullable === false && <Badge colorScheme="red">Required</Badge>}
                                  {field.unique && <Badge colorScheme="blue">Unique</Badge>}
                                  {field.maxLength && <Badge colorScheme="teal">Max Length: {field.maxLength}</Badge>}
                                  {field.isPrimary && <Badge colorScheme="green">Primary Key</Badge>}
                                  {field.isForeign && <Badge colorScheme="purple">Foreign Key</Badge>}
                                  {!field.nullable === false && !field.unique && !field.maxLength && !field.isPrimary && !field.isForeign && 
                                    <Text>No constraints</Text>
                                  }
                                </HStack>
                              </Box>
                            </VStack>
                          </AccordionPanel>
                        </AccordionItem>
                      ))}
                      
                      {(!currentSchema.fields || currentSchema.fields.length === 0) && (
                        <Box py={4} textAlign="center">
                          <Text>No fields available for documentation.</Text>
                        </Box>
                      )}
                    </Accordion>
                  </Box>
                  
                  <Box>
                    <Heading size="sm" mb={2}>Relationships</Heading>
                    {relationships && relationships.length > 0 ? (
                      <Table variant="simple" size="sm">
                        <Thead>
                          <Tr>
                            <Th>Type</Th>
                            <Th>Related Schema</Th>
                            <Th>Description</Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          {relationships.map((rel, index) => (
                            <Tr key={index}>
                              <Td>{rel.type || 'Unknown'}</Td>
                              <Td>
                                <RouterLink to={`/schemas/${rel.relatedSchemaId}`}>
                                  <Text color="brand.500">{rel.relatedSchemaName}</Text>
                                </RouterLink>
                              </Td>
                              <Td>{rel.description || `${rel.sourceField} connects to ${rel.targetField}`}</Td>
                            </Tr>
                          ))}
                        </Tbody>
                      </Table>
                    ) : (
                      <Text>No relationships documented.</Text>
                    )}
                  </Box>
                </VStack>
              </CardBody>
            </Card>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  );
};

export default SchemaViewer;
