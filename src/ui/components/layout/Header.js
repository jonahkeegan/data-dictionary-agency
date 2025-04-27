import React from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import {
  Box,
  Flex,
  HStack,
  IconButton,
  Button,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  MenuDivider,
  useColorModeValue,
  useDisclosure,
  Image,
  Text,
  Link,
  Avatar,
  Tooltip,
} from '@chakra-ui/react';
import { selectAuth, logoutUser } from '../../store/slices/authSlice';
import { toggleSidebar, toggleColorMode } from '../../store/slices/uiSlice';

/**
 * Application Header Component
 * Provides navigation, user account access, and theme toggle
 */
const Header = () => {
  const { isAuthenticated, user } = useSelector(selectAuth);
  const location = useLocation();
  const dispatch = useDispatch();
  
  // Color mode values
  const bg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  // Navigation items
  const navItems = [
    { label: 'Dashboard', path: '/' },
    { label: 'Repositories', path: '/repositories' },
    { label: 'Visualization', path: '/visualization' },
  ];
  
  // Handle sidebar toggle
  const handleSidebarToggle = () => {
    dispatch(toggleSidebar());
  };
  
  // Handle theme toggle
  const handleThemeToggle = () => {
    dispatch(toggleColorMode());
  };
  
  // Handle logout
  const handleLogout = () => {
    dispatch(logoutUser());
  };
  
  return (
    <Box 
      as="header" 
      bg={bg} 
      px={4} 
      py={2} 
      position="sticky" 
      top={0} 
      zIndex="sticky"
      borderBottom="1px" 
      borderColor={borderColor}
      boxShadow="sm"
    >
      <Flex alignItems="center" justifyContent="space-between">
        {/* Logo and Brand */}
        <HStack spacing={3}>
          <IconButton
            aria-label="Toggle Sidebar"
            icon={<Text fontSize="xl">☰</Text>}
            variant="ghost"
            onClick={handleSidebarToggle}
          />
          <RouterLink to="/">
            <Flex alignItems="center">
              <Text
                fontWeight="bold"
                fontSize="xl"
                bgGradient="linear(to-r, brand.500, accent.500)"
                bgClip="text"
              >
                Data Dictionary Agency
              </Text>
            </Flex>
          </RouterLink>
        </HStack>
        
        {/* Navigation Links (shown on larger screens) */}
        <HStack
          as="nav"
          spacing={4}
          display={{ base: 'none', md: 'flex' }}
          ml={10}
        >
          {navItems.map((item) => (
            <Link
              key={item.path}
              as={RouterLink}
              to={item.path}
              px={2}
              py={1}
              rounded="md"
              fontWeight={location.pathname === item.path ? 'semibold' : 'normal'}
              color={location.pathname === item.path ? 'brand.500' : 'inherit'}
              _hover={{
                textDecoration: 'none',
                bg: useColorModeValue('gray.100', 'gray.700'),
              }}
            >
              {item.label}
            </Link>
          ))}
        </HStack>
        
        {/* Right Side Controls */}
        <HStack spacing={3}>
          {/* Theme Toggle */}
          <Tooltip label="Toggle Dark Mode">
            <IconButton
              aria-label="Toggle Color Mode"
              icon={<Text fontSize="xl">{useColorModeValue('🌙', '☀️')}</Text>}
              variant="ghost"
              onClick={handleThemeToggle}
            />
          </Tooltip>
          
          {/* User Profile Menu */}
          {isAuthenticated ? (
            <Menu>
              <MenuButton
                as={Button}
                rounded="full"
                variant="link"
                cursor="pointer"
                minW={0}
              >
                <Avatar
                  size="sm"
                  name={user?.name || 'User'}
                  src={user?.avatar}
                />
              </MenuButton>
              <MenuList>
                <MenuItem as={RouterLink} to="/profile">Profile</MenuItem>
                <MenuItem as={RouterLink} to="/settings">Settings</MenuItem>
                <MenuDivider />
                <MenuItem onClick={handleLogout}>Logout</MenuItem>
              </MenuList>
            </Menu>
          ) : (
            <Button
              as={RouterLink}
              to="/login"
              size="sm"
              colorScheme="brand"
            >
              Login
            </Button>
          )}
        </HStack>
      </Flex>
    </Box>
  );
};

export default Header;
