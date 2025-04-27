import { createSlice } from '@reduxjs/toolkit';

// Initial state
const initialState = {
  sidebar: {
    isOpen: true,
    width: 250,
  },
  theme: {
    colorMode: 'light',
    isCustomized: false,
  },
  notifications: [],
  loadingStates: {},
  visualizationOptions: {
    layout: 'force-directed', // 'force-directed', 'hierarchical', 'circular'
    showFieldTypes: true,
    showRelationshipLabels: true,
    zoomLevel: 1,
    highlightedEntities: [],
    hiddenEntities: [],
  },
};

// Create slice
const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    // Sidebar actions
    toggleSidebar: (state) => {
      state.sidebar.isOpen = !state.sidebar.isOpen;
    },
    setSidebarOpen: (state, action) => {
      state.sidebar.isOpen = action.payload;
    },
    setSidebarWidth: (state, action) => {
      state.sidebar.width = action.payload;
    },
    
    // Theme actions
    setColorMode: (state, action) => {
      state.theme.colorMode = action.payload;
    },
    toggleColorMode: (state) => {
      state.theme.colorMode = state.theme.colorMode === 'light' ? 'dark' : 'light';
    },
    setCustomTheme: (state, action) => {
      state.theme.isCustomized = true;
      // Additional theme customization could be stored here
    },
    resetTheme: (state) => {
      state.theme.isCustomized = false;
      state.theme.colorMode = 'light';
    },
    
    // Notification actions
    addNotification: (state, action) => {
      const { id, type, message, title, duration = 5000 } = action.payload;
      state.notifications.push({
        id: id || `notification-${Date.now()}`,
        type: type || 'info', // 'info', 'success', 'warning', 'error'
        message,
        title,
        duration,
        isRead: false,
        createdAt: Date.now(),
      });
    },
    removeNotification: (state, action) => {
      state.notifications = state.notifications.filter(
        (notification) => notification.id !== action.payload
      );
    },
    clearNotifications: (state) => {
      state.notifications = [];
    },
    markNotificationAsRead: (state, action) => {
      const notification = state.notifications.find(
        (notification) => notification.id === action.payload
      );
      if (notification) {
        notification.isRead = true;
      }
    },
    
    // Loading state actions
    setIsLoading: (state, action) => {
      const { key, isLoading } = action.payload;
      state.loadingStates[key] = isLoading;
    },
    clearLoadingStates: (state) => {
      state.loadingStates = {};
    },
    
    // Visualization options actions
    setVisualizationLayout: (state, action) => {
      state.visualizationOptions.layout = action.payload;
    },
    toggleFieldTypes: (state) => {
      state.visualizationOptions.showFieldTypes = !state.visualizationOptions.showFieldTypes;
    },
    toggleRelationshipLabels: (state) => {
      state.visualizationOptions.showRelationshipLabels = !state.visualizationOptions.showRelationshipLabels;
    },
    setZoomLevel: (state, action) => {
      state.visualizationOptions.zoomLevel = action.payload;
    },
    highlightEntities: (state, action) => {
      state.visualizationOptions.highlightedEntities = Array.isArray(action.payload)
        ? action.payload
        : [action.payload];
    },
    clearHighlightedEntities: (state) => {
      state.visualizationOptions.highlightedEntities = [];
    },
    hideEntity: (state, action) => {
      const entityId = action.payload;
      if (!state.visualizationOptions.hiddenEntities.includes(entityId)) {
        state.visualizationOptions.hiddenEntities.push(entityId);
      }
    },
    showEntity: (state, action) => {
      state.visualizationOptions.hiddenEntities = state.visualizationOptions.hiddenEntities.filter(
        (id) => id !== action.payload
      );
    },
    resetVisualizationOptions: (state) => {
      state.visualizationOptions = initialState.visualizationOptions;
    },
  },
});

// Export actions and reducer
export const {
  // Sidebar
  toggleSidebar,
  setSidebarOpen,
  setSidebarWidth,
  
  // Theme
  setColorMode,
  toggleColorMode,
  setCustomTheme,
  resetTheme,
  
  // Notifications
  addNotification,
  removeNotification,
  clearNotifications,
  markNotificationAsRead,
  
  // Loading states
  setIsLoading,
  clearLoadingStates,
  
  // Visualization options
  setVisualizationLayout,
  toggleFieldTypes,
  toggleRelationshipLabels,
  setZoomLevel,
  highlightEntities,
  clearHighlightedEntities,
  hideEntity,
  showEntity,
  resetVisualizationOptions,
} = uiSlice.actions;

export default uiSlice.reducer;
