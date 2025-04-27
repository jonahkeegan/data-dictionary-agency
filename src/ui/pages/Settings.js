import React, { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  Box,
  Heading,
  VStack,
  Card,
  CardHeader,
  CardBody,
  FormControl,
  FormLabel,
  Switch,
  Select,
  Input,
  Button,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Text,
  HStack,
  Divider,
  useColorModeValue,
  useToast,
  SimpleGrid,
  Alert,
  AlertIcon,
  Badge,
  Checkbox,
} from '@chakra-ui/react';
import { setColorMode, toggleColorMode } from '../store/slices/uiSlice';

/**
 * Settings Page Component
 * Provides system-wide configuration options for the application
 */
const Settings = () => {
  const dispatch = useDispatch();
  const toast = useToast();
  const { colorMode } = useSelector(state => state.ui.theme);
  
  // Local state for form values
  const [apiSettings, setApiSettings] = useState({
    apiUrl: '/api',
    timeout: 30000,
    retryCount: 3,
    logLevel: 'error',
  });
  
  const [visualizationSettings, setVisualizationSettings] = useState({
    defaultLayout: 'force-directed',
    animationDuration: 500,
    defaultNodeSize: 'medium',
    showLabels: true,
    labelSize: 'medium',
  });
  
  const [userSettings, setUserSettings] = useState({
    username: 'admin',
    email: 'admin@example.com',
    language: 'en',
    dateFormat: 'MM/DD/YYYY',
    timeFormat: '12h',
  });
  
  // Color mode values
  const cardBg = useColorModeValue('white', 'gray.800');
  
  // Handle form changes
  const handleApiChange = (e) => {
    const { name, value } = e.target;
    setApiSettings(prev => ({ ...prev, [name]: value }));
  };
  
  const handleVisualizationChange = (e) => {
    const { name, value, checked, type } = e.target;
    setVisualizationSettings(prev => ({ 
      ...prev, 
      [name]: type === 'checkbox' ? checked : value
    }));
  };
  
  const handleUserChange = (e) => {
    const { name, value } = e.target;
    setUserSettings(prev => ({ ...prev, [name]: value }));
  };
  
  // Handle form submission
  const handleApiSubmit = (e) => {
    e.preventDefault();
    toast({
      title: 'API Settings saved.',
      status: 'success',
      duration: 2000,
      isClosable: true,
    });
  };
  
  const handleVisualizationSubmit = (e) => {
    e.preventDefault();
    toast({
      title: 'Visualization Settings saved.',
      status: 'success',
      duration: 2000,
      isClosable: true,
    });
  };
  
  const handleUserSubmit = (e) => {
    e.preventDefault();
    toast({
      title: 'User Settings saved.',
      status: 'success',
      duration: 2000,
      isClosable: true,
    });
  };
  
  // Handle theme toggle
  const handleThemeToggle = () => {
    dispatch(toggleColorMode());
  };
  
  // Handle theme setting
  const handleThemeChange = (e) => {
    dispatch(setColorMode(e.target.value));
  };
  
  return (
    <Box p={4}>
      <Heading as="h1" size="xl" mb={6}>
        Settings
      </Heading>
      
      <Tabs colorScheme="brand" isLazy>
        <TabList>
          <Tab>General</Tab>
          <Tab>Theme</Tab>
          <Tab>API</Tab>
          <Tab>Visualization</Tab>
          <Tab>User</Tab>
        </TabList>
        
        <TabPanels>
          <TabPanel>
            {/* General Settings */}
            <Card bg={cardBg} boxShadow="md">
              <CardHeader>
                <Heading size="md">General Settings</Heading>
              </CardHeader>
              <CardBody>
                <VStack spacing={6} align="stretch">
                  <FormControl display="flex" alignItems="center">
                    <FormLabel htmlFor="auto-refresh" mb="0">
                      Auto Refresh Data
                    </FormLabel>
                    <Switch id="auto-refresh" colorScheme="brand" defaultChecked />
                  </FormControl>
                  
                  <FormControl>
                    <FormLabel htmlFor="refresh-interval">Refresh Interval (seconds)</FormLabel>
                    <Select id="refresh-interval" defaultValue="30">
                      <option value="15">15 seconds</option>
                      <option value="30">30 seconds</option>
                      <option value="60">1 minute</option>
                      <option value="300">5 minutes</option>
                      <option value="600">10 minutes</option>
                    </Select>
                  </FormControl>
                  
                  <FormControl display="flex" alignItems="center">
                    <FormLabel htmlFor="notifications" mb="0">
                      Enable Notifications
                    </FormLabel>
                    <Switch id="notifications" colorScheme="brand" defaultChecked />
                  </FormControl>
                  
                  <FormControl>
                    <FormLabel htmlFor="language">Language</FormLabel>
                    <Select id="language" defaultValue="en">
                      <option value="en">English</option>
                      <option value="es">Spanish</option>
                      <option value="fr">French</option>
                      <option value="de">German</option>
                      <option value="zh">Chinese</option>
                    </Select>
                  </FormControl>
                  
                  <Divider />
                  
                  <HStack justify="flex-end">
                    <Button variant="outline">Reset</Button>
                    <Button colorScheme="brand">Save</Button>
                  </HStack>
                </VStack>
              </CardBody>
            </Card>
          </TabPanel>
          
          <TabPanel>
            {/* Theme Settings */}
            <Card bg={cardBg} boxShadow="md">
              <CardHeader>
                <Heading size="md">Theme Settings</Heading>
              </CardHeader>
              <CardBody>
                <VStack spacing={6} align="stretch">
                  <FormControl display="flex" alignItems="center">
                    <FormLabel htmlFor="dark-mode" mb="0">
                      Dark Mode
                    </FormLabel>
                    <Switch 
                      id="dark-mode" 
                      colorScheme="brand" 
                      isChecked={colorMode === 'dark'}
                      onChange={handleThemeToggle}
                    />
                  </FormControl>
                  
                  <FormControl>
                    <FormLabel htmlFor="theme-choice">Theme</FormLabel>
                    <Select 
                      id="theme-choice" 
                      value={colorMode} 
                      onChange={handleThemeChange}
                    >
                      <option value="light">Light</option>
                      <option value="dark">Dark</option>
                    </Select>
                  </FormControl>
                  
                  <FormControl>
                    <FormLabel htmlFor="accent-color">Accent Color</FormLabel>
                    <SimpleGrid columns={4} spacing={3}>
                      <Button h="40px" w="40px" bg="brand.500" _hover={{ bg: 'brand.600' }} />
                      <Button h="40px" w="40px" bg="blue.500" _hover={{ bg: 'blue.600' }} />
                      <Button h="40px" w="40px" bg="purple.500" _hover={{ bg: 'purple.600' }} />
                      <Button h="40px" w="40px" bg="green.500" _hover={{ bg: 'green.600' }} />
                      <Button h="40px" w="40px" bg="red.500" _hover={{ bg: 'red.600' }} />
                      <Button h="40px" w="40px" bg="orange.500" _hover={{ bg: 'orange.600' }} />
                      <Button h="40px" w="40px" bg="cyan.500" _hover={{ bg: 'cyan.600' }} />
                      <Button h="40px" w="40px" bg="pink.500" _hover={{ bg: 'pink.600' }} />
                    </SimpleGrid>
                  </FormControl>
                  
                  <FormControl>
                    <FormLabel htmlFor="font-size">Font Size</FormLabel>
                    <Select id="font-size" defaultValue="md">
                      <option value="sm">Small</option>
                      <option value="md">Medium</option>
                      <option value="lg">Large</option>
                    </Select>
                  </FormControl>
                  
                  <Alert status="info" borderRadius="md">
                    <AlertIcon />
                    Theme changes apply immediately and are saved for your next visit.
                  </Alert>
                  
                  <Divider />
                  
                  <HStack justify="flex-end">
                    <Button variant="outline">Reset to Default</Button>
                    <Button colorScheme="brand">Save Preferences</Button>
                  </HStack>
                </VStack>
              </CardBody>
            </Card>
          </TabPanel>
          
          <TabPanel>
            {/* API Settings */}
            <Card bg={cardBg} boxShadow="md">
              <CardHeader>
                <Heading size="md">API Configuration</Heading>
              </CardHeader>
              <CardBody>
                <form onSubmit={handleApiSubmit}>
                  <VStack spacing={6} align="stretch">
                    <FormControl>
                      <FormLabel htmlFor="apiUrl">API Endpoint URL</FormLabel>
                      <Input 
                        id="apiUrl" 
                        name="apiUrl" 
                        value={apiSettings.apiUrl} 
                        onChange={handleApiChange}
                      />
                    </FormControl>
                    
                    <FormControl>
                      <FormLabel htmlFor="timeout">Request Timeout (ms)</FormLabel>
                      <Input 
                        id="timeout" 
                        name="timeout" 
                        type="number" 
                        value={apiSettings.timeout} 
                        onChange={handleApiChange}
                      />
                    </FormControl>
                    
                    <FormControl>
                      <FormLabel htmlFor="retryCount">Retry Count</FormLabel>
                      <Select 
                        id="retryCount" 
                        name="retryCount" 
                        value={apiSettings.retryCount} 
                        onChange={handleApiChange}
                      >
                        <option value="0">0 (No retries)</option>
                        <option value="1">1</option>
                        <option value="2">2</option>
                        <option value="3">3</option>
                        <option value="5">5</option>
                      </Select>
                    </FormControl>
                    
                    <FormControl>
                      <FormLabel htmlFor="logLevel">Log Level</FormLabel>
                      <Select 
                        id="logLevel" 
                        name="logLevel" 
                        value={apiSettings.logLevel} 
                        onChange={handleApiChange}
                      >
                        <option value="error">Error</option>
                        <option value="warn">Warning</option>
                        <option value="info">Info</option>
                        <option value="debug">Debug</option>
                      </Select>
                    </FormControl>
                    
                    <Alert status="warning" borderRadius="md">
                      <AlertIcon />
                      Changes to API settings require an application restart to take full effect.
                    </Alert>
                    
                    <Divider />
                    
                    <HStack justify="flex-end">
                      <Button variant="outline" type="reset">Reset</Button>
                      <Button colorScheme="brand" type="submit">Save</Button>
                    </HStack>
                  </VStack>
                </form>
              </CardBody>
            </Card>
          </TabPanel>
          
          <TabPanel>
            {/* Visualization Settings */}
            <Card bg={cardBg} boxShadow="md">
              <CardHeader>
                <Heading size="md">Visualization Preferences</Heading>
              </CardHeader>
              <CardBody>
                <form onSubmit={handleVisualizationSubmit}>
                  <VStack spacing={6} align="stretch">
                    <FormControl>
                      <FormLabel htmlFor="defaultLayout">Default Layout</FormLabel>
                      <Select 
                        id="defaultLayout" 
                        name="defaultLayout" 
                        value={visualizationSettings.defaultLayout} 
                        onChange={handleVisualizationChange}
                      >
                        <option value="force-directed">Force-Directed</option>
                        <option value="hierarchical">Hierarchical</option>
                        <option value="circular">Circular</option>
                        <option value="grid">Grid</option>
                      </Select>
                    </FormControl>
                    
                    <FormControl>
                      <FormLabel htmlFor="animationDuration">Animation Duration (ms)</FormLabel>
                      <Input 
                        id="animationDuration" 
                        name="animationDuration" 
                        type="number" 
                        value={visualizationSettings.animationDuration} 
                        onChange={handleVisualizationChange}
                      />
                    </FormControl>
                    
                    <FormControl>
                      <FormLabel htmlFor="defaultNodeSize">Default Node Size</FormLabel>
                      <Select 
                        id="defaultNodeSize" 
                        name="defaultNodeSize" 
                        value={visualizationSettings.defaultNodeSize} 
                        onChange={handleVisualizationChange}
                      >
                        <option value="small">Small</option>
                        <option value="medium">Medium</option>
                        <option value="large">Large</option>
                      </Select>
                    </FormControl>
                    
                    <FormControl display="flex" alignItems="center">
                      <FormLabel htmlFor="showLabels" mb="0">
                        Show Labels
                      </FormLabel>
                      <Switch 
                        id="showLabels" 
                        name="showLabels" 
                        colorScheme="brand" 
                        isChecked={visualizationSettings.showLabels} 
                        onChange={handleVisualizationChange}
                      />
                    </FormControl>
                    
                    <FormControl>
                      <FormLabel htmlFor="labelSize">Label Size</FormLabel>
                      <Select 
                        id="labelSize" 
                        name="labelSize" 
                        value={visualizationSettings.labelSize} 
                        onChange={handleVisualizationChange}
                        isDisabled={!visualizationSettings.showLabels}
                      >
                        <option value="small">Small</option>
                        <option value="medium">Medium</option>
                        <option value="large">Large</option>
                      </Select>
                    </FormControl>
                    
                    <Divider />
                    
                    <HStack justify="flex-end">
                      <Button variant="outline" type="reset">Reset</Button>
                      <Button colorScheme="brand" type="submit">Save</Button>
                    </HStack>
                  </VStack>
                </form>
              </CardBody>
            </Card>
          </TabPanel>
          
          <TabPanel>
            {/* User Settings */}
            <Card bg={cardBg} boxShadow="md">
              <CardHeader>
                <Heading size="md">User Profile & Preferences</Heading>
              </CardHeader>
              <CardBody>
                <form onSubmit={handleUserSubmit}>
                  <VStack spacing={6} align="stretch">
                    <FormControl>
                      <FormLabel htmlFor="username">Username</FormLabel>
                      <Input 
                        id="username" 
                        name="username" 
                        value={userSettings.username} 
                        onChange={handleUserChange}
                      />
                    </FormControl>
                    
                    <FormControl>
                      <FormLabel htmlFor="email">Email</FormLabel>
                      <Input 
                        id="email" 
                        name="email" 
                        type="email" 
                        value={userSettings.email} 
                        onChange={handleUserChange}
                      />
                    </FormControl>
                    
                    <FormControl>
                      <FormLabel htmlFor="language">Preferred Language</FormLabel>
                      <Select 
                        id="language" 
                        name="language" 
                        value={userSettings.language} 
                        onChange={handleUserChange}
                      >
                        <option value="en">English</option>
                        <option value="es">Spanish</option>
                        <option value="fr">French</option>
                        <option value="de">German</option>
                        <option value="zh">Chinese</option>
                      </Select>
                    </FormControl>
                    
                    <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                      <FormControl>
                        <FormLabel htmlFor="dateFormat">Date Format</FormLabel>
                        <Select 
                          id="dateFormat" 
                          name="dateFormat" 
                          value={userSettings.dateFormat} 
                          onChange={handleUserChange}
                        >
                          <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                          <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                          <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                        </Select>
                      </FormControl>
                      
                      <FormControl>
                        <FormLabel htmlFor="timeFormat">Time Format</FormLabel>
                        <Select 
                          id="timeFormat" 
                          name="timeFormat" 
                          value={userSettings.timeFormat} 
                          onChange={handleUserChange}
                        >
                          <option value="12h">12-hour (AM/PM)</option>
                          <option value="24h">24-hour</option>
                        </Select>
                      </FormControl>
                    </SimpleGrid>
                    
                    <FormControl>
                      <FormLabel mb={2}>Notification Preferences</FormLabel>
                      <VStack align="start" spacing={2}>
                        <Checkbox defaultChecked>Email notifications</Checkbox>
                        <Checkbox defaultChecked>In-app notifications</Checkbox>
                        <Checkbox>Schema update alerts</Checkbox>
                        <Checkbox defaultChecked>Repository changes</Checkbox>
                      </VStack>
                    </FormControl>
                    
                    <Divider />
                    
                    <HStack justify="flex-end">
                      <Button variant="outline" type="reset">Reset</Button>
                      <Button colorScheme="brand" type="submit">Save</Button>
                    </HStack>
                  </VStack>
                </form>
              </CardBody>
            </Card>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  );
};

export default Settings;
