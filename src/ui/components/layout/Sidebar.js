import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useLocation, Link as RouterLink } from 'react-router-dom';
import {
  Box,
  VStack,
  HStack,
  Text,
  Icon,
  Divider,
  Badge,
  useColorModeValue,
  Collapse,
  List,
  ListItem,
  Flex,
} from '@chakra-ui/react';

/**
 * Sidebar Navigation Component
 * Provides the main navigation for the application
 */
const Sidebar = () => {
  const location = useLocation();
  const dispatch = useDispatch();
  const { isOpen, width } = useSelector((state) => state.ui.sidebar);
  
  // Color mode values
  const bg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const hoverBg = useColorModeValue('gray.100', 'gray.700');
  const activeBg = useColorModeValue('gray.200', 'gray.600');
  
  // Navigation items with icon representation as text for now
  const navigationItems = [
    {
      label: 'Dashboard',
      icon: '📊',
      path: '/',
    },
    {
      label: 'Repositories',
      icon: '📁',
      path: '/repositories',
      badge: 3, // Number of repositories
    },
    {
      label: 'Schemas',
      icon: '📄',
      path: '/schemas',
    },
    {
      label: 'Visualization',
      icon: '🔍',
      path: '/visualization',
    },
    {
      label: 'Documentation',
      icon: '📝',
      path: '/documentation',
    },
    {
      label: 'Settings',
      icon: '⚙️',
      path: '/settings',
    },
  ];
  
  if (!isOpen) {
    return (
      <Box
        as="aside"
        width="60px"
        bg={bg}
        borderRight="1px"
        borderColor={borderColor}
        height="calc(100vh - 60px)"
        position="sticky"
        top="60px"
        overflowY="auto"
        transition="width 0.2s"
        py={4}
      >
        <VStack spacing={6} align="center">
          {navigationItems.map((item) => (
            <RouterLink key={item.path} to={item.path}>
              <Box
                p={2}
                borderRadius="md"
                cursor="pointer"
                bg={location.pathname === item.path ? activeBg : 'transparent'}
                _hover={{ bg: hoverBg }}
                position="relative"
              >
                <Text fontSize="xl">{item.icon}</Text>
                {item.badge && (
                  <Badge
                    position="absolute"
                    top="-2px"
                    right="-5px"
                    colorScheme="brand"
                    borderRadius="full"
                    fontSize="xs"
                  >
                    {item.badge}
                  </Badge>
                )}
              </Box>
            </RouterLink>
          ))}
        </VStack>
      </Box>
    );
  }
  
  return (
    <Box
      as="aside"
      width={`${width}px`}
      bg={bg}
      borderRight="1px"
      borderColor={borderColor}
      height="calc(100vh - 60px)"
      position="sticky"
      top="60px"
      overflowY="auto"
      transition="width 0.2s"
      py={4}
    >
      <VStack spacing={1} align="stretch">
        {navigationItems.map((item) => (
          <RouterLink key={item.path} to={item.path}>
            <HStack
              px={4}
              py={3}
              borderRadius="md"
              cursor="pointer"
              bg={location.pathname === item.path ? activeBg : 'transparent'}
              _hover={{ bg: hoverBg }}
              spacing={4}
            >
              <Text fontSize="lg">{item.icon}</Text>
              <Text fontWeight={location.pathname === item.path ? 'medium' : 'normal'}>
                {item.label}
              </Text>
              {item.badge && (
                <Badge colorScheme="brand" borderRadius="full" ml="auto">
                  {item.badge}
                </Badge>
              )}
            </HStack>
          </RouterLink>
        ))}
      </VStack>
      
      {/* Recent Items Section */}
      <Box mt={8}>
        <Text px={4} fontSize="sm" fontWeight="medium" mb={2} color="gray.500">
          RECENT ITEMS
        </Text>
        <List spacing={1}>
          <ListItem>
            <RouterLink to="/schemas/123">
              <HStack
                px={4}
                py={2}
                borderRadius="md"
                cursor="pointer"
                _hover={{ bg: hoverBg }}
                spacing={3}
              >
                <Text fontSize="sm">🔶</Text>
                <Text fontSize="sm" noOfLines={1}>users_schema.json</Text>
              </HStack>
            </RouterLink>
          </ListItem>
          <ListItem>
            <RouterLink to="/schemas/456">
              <HStack
                px={4}
                py={2}
                borderRadius="md"
                cursor="pointer"
                _hover={{ bg: hoverBg }}
                spacing={3}
              >
                <Text fontSize="sm">🔷</Text>
                <Text fontSize="sm" noOfLines={1}>products_table.sql</Text>
              </HStack>
            </RouterLink>
          </ListItem>
          <ListItem>
            <RouterLink to="/schemas/789">
              <HStack
                px={4}
                py={2}
                borderRadius="md"
                cursor="pointer"
                _hover={{ bg: hoverBg }}
                spacing={3}
              >
                <Text fontSize="sm">🟢</Text>
                <Text fontSize="sm" noOfLines={1}>orders_schema.avro</Text>
              </HStack>
            </RouterLink>
          </ListItem>
        </List>
      </Box>
      
      {/* Footer Section */}
      <Flex
        direction="column"
        mt="auto"
        pt={6}
        borderTop="1px"
        borderColor={borderColor}
        px={4}
        pb={4}
      >
        <Text fontSize="xs" color="gray.500">
          Data Dictionary Agency v0.1.0
        </Text>
        <Text fontSize="xs" color="gray.500">
          © 2025 - All rights reserved
        </Text>
      </Flex>
    </Box>
  );
};

export default Sidebar;
