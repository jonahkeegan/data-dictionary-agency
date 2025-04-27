import { extendTheme } from '@chakra-ui/react';

// Color palette
const colors = {
  brand: {
    50: '#e6f7ff',
    100: '#b3e0ff',
    200: '#80caff',
    300: '#4db3ff',
    400: '#1a9dff',
    500: '#0080e6',
    600: '#0064b3',
    700: '#004880',
    800: '#002c4d',
    900: '#00101a',
  },
  accent: {
    50: '#f2fcf1',
    100: '#dcf5db',
    200: '#bcebb9',
    300: '#98df93',
    400: '#70cf69',
    500: '#4abb43',
    600: '#389632',
    700: '#2d7428',
    800: '#1d4d1b',
    900: '#0f290e',
  },
  neutral: {
    50: '#f7f7f7',
    100: '#e6e6e6',
    200: '#cccccc',
    300: '#b3b3b3',
    400: '#999999',
    500: '#808080',
    600: '#666666',
    700: '#4d4d4d',
    800: '#333333',
    900: '#1a1a1a',
  },
  success: {
    500: '#38a169',
  },
  warning: {
    500: '#dd6b20',
  },
  error: {
    500: '#e53e3e',
  },
  info: {
    500: '#3182ce',
  },
};

// Font configuration
const fonts = {
  body: 'Inter, system-ui, sans-serif',
  heading: 'Inter, system-ui, sans-serif',
  mono: 'Menlo, monospace',
};

// Component style overrides
const components = {
  Button: {
    baseStyle: {
      fontWeight: '600',
      borderRadius: 'md',
    },
    variants: {
      solid: {
        bg: 'brand.500',
        color: 'white',
        _hover: {
          bg: 'brand.600',
        },
      },
      outline: {
        borderColor: 'brand.500',
        color: 'brand.500',
      },
    },
  },
  Card: {
    baseStyle: {
      p: '4',
      borderRadius: 'lg',
      boxShadow: 'md',
    },
  },
  Heading: {
    baseStyle: {
      fontWeight: '600',
    },
  },
};

// Extended theme
export const theme = extendTheme({
  colors,
  fonts,
  components,
  styles: {
    global: {
      body: {
        bg: 'gray.50',
        color: 'gray.800',
      },
    },
  },
  config: {
    initialColorMode: 'light',
    useSystemColorMode: false,
  },
});
