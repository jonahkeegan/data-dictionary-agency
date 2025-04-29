import configureMockStore from 'redux-mock-store';
import {
  toggleSidebar,
  setSidebarOpen,
  setSidebarWidth,
  setColorMode,
  toggleColorMode,
  setCustomTheme,
  resetTheme,
  addNotification,
  removeNotification,
  clearNotifications,
  markNotificationAsRead,
  setIsLoading,
  clearLoadingStates,
  setVisualizationLayout,
  toggleFieldTypes,
  toggleRelationshipLabels,
  setZoomLevel,
  highlightEntities,
  clearHighlightedEntities,
  hideEntity,
  showEntity,
  resetVisualizationOptions
} from '../uiSlice';

// Configure mock store
const mockStore = configureMockStore();

describe('uiSlice', () => {
  // Mock UI state
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
      layout: 'force-directed',
      showFieldTypes: true,
      showRelationshipLabels: true,
      zoomLevel: 1,
      highlightedEntities: [],
      hiddenEntities: [],
    },
  };

  beforeEach(() => {
    // Reset mock calls
    jest.clearAllMocks();
  });

  describe('sidebar actions', () => {
    it('should handle toggleSidebar', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          sidebar: {
            isOpen: true
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(toggleSidebar());
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(toggleSidebar.type);
    });
    
    it('should handle setSidebarOpen', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          sidebar: {
            isOpen: true
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(setSidebarOpen(false));
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(setSidebarOpen.type);
      expect(actions[0].payload).toBe(false);
    });
    
    it('should handle setSidebarWidth', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          sidebar: {
            width: 250
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(setSidebarWidth(300));
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(setSidebarWidth.type);
      expect(actions[0].payload).toBe(300);
    });
  });
  
  describe('theme actions', () => {
    it('should handle setColorMode', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          theme: {
            colorMode: 'light'
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(setColorMode('dark'));
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(setColorMode.type);
      expect(actions[0].payload).toBe('dark');
    });
    
    it('should handle toggleColorMode', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          theme: {
            colorMode: 'light'
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(toggleColorMode());
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(toggleColorMode.type);
    });
    
    it('should handle setCustomTheme', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          theme: {
            isCustomized: false
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(setCustomTheme({ primaryColor: '#ff0000' }));
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(setCustomTheme.type);
      expect(actions[0].payload).toEqual({ primaryColor: '#ff0000' });
    });
    
    it('should handle resetTheme', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          theme: {
            colorMode: 'dark',
            isCustomized: true
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(resetTheme());
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(resetTheme.type);
    });
  });
  
  describe('notification actions', () => {
    it('should handle addNotification', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          notifications: []
        }
      });
      
      // Create notification data
      const notification = {
        type: 'success',
        message: 'Operation successful',
        title: 'Success',
        duration: 3000
      };
      
      // Dispatch the action
      store.dispatch(addNotification(notification));
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(addNotification.type);
      expect(actions[0].payload).toEqual(notification);
    });
    
    it('should handle removeNotification', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          notifications: [
            { id: 'notif-1', message: 'Test notification' }
          ]
        }
      });
      
      // Dispatch the action
      store.dispatch(removeNotification('notif-1'));
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(removeNotification.type);
      expect(actions[0].payload).toBe('notif-1');
    });
    
    it('should handle clearNotifications', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          notifications: [
            { id: 'notif-1', message: 'Test notification 1' },
            { id: 'notif-2', message: 'Test notification 2' }
          ]
        }
      });
      
      // Dispatch the action
      store.dispatch(clearNotifications());
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(clearNotifications.type);
    });
    
    it('should handle markNotificationAsRead', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          notifications: [
            { id: 'notif-1', message: 'Test notification', isRead: false }
          ]
        }
      });
      
      // Dispatch the action
      store.dispatch(markNotificationAsRead('notif-1'));
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(markNotificationAsRead.type);
      expect(actions[0].payload).toBe('notif-1');
    });
  });
  
  describe('loading state actions', () => {
    it('should handle setIsLoading', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          loadingStates: {}
        }
      });
      
      // Dispatch the action
      store.dispatch(setIsLoading({ key: 'fetchData', isLoading: true }));
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(setIsLoading.type);
      expect(actions[0].payload).toEqual({ key: 'fetchData', isLoading: true });
    });
    
    it('should handle clearLoadingStates', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          loadingStates: {
            fetchData: true,
            saveData: false
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(clearLoadingStates());
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(clearLoadingStates.type);
    });
  });
  
  describe('visualization options actions', () => {
    it('should handle setVisualizationLayout', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          visualizationOptions: {
            layout: 'force-directed'
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(setVisualizationLayout('hierarchical'));
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(setVisualizationLayout.type);
      expect(actions[0].payload).toBe('hierarchical');
    });
    
    it('should handle toggleFieldTypes', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          visualizationOptions: {
            showFieldTypes: true
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(toggleFieldTypes());
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(toggleFieldTypes.type);
    });
    
    it('should handle toggleRelationshipLabels', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          visualizationOptions: {
            showRelationshipLabels: true
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(toggleRelationshipLabels());
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(toggleRelationshipLabels.type);
    });
    
    it('should handle setZoomLevel', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          visualizationOptions: {
            zoomLevel: 1
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(setZoomLevel(1.5));
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(setZoomLevel.type);
      expect(actions[0].payload).toBe(1.5);
    });
    
    it('should handle highlightEntities with single entity', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          visualizationOptions: {
            highlightedEntities: []
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(highlightEntities('entity-1'));
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(highlightEntities.type);
      expect(actions[0].payload).toBe('entity-1');
    });
    
    it('should handle highlightEntities with multiple entities', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          visualizationOptions: {
            highlightedEntities: []
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(highlightEntities(['entity-1', 'entity-2']));
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(highlightEntities.type);
      expect(actions[0].payload).toEqual(['entity-1', 'entity-2']);
    });
    
    it('should handle clearHighlightedEntities', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          visualizationOptions: {
            highlightedEntities: ['entity-1', 'entity-2']
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(clearHighlightedEntities());
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(clearHighlightedEntities.type);
    });
    
    it('should handle hideEntity', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          visualizationOptions: {
            hiddenEntities: []
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(hideEntity('entity-1'));
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(hideEntity.type);
      expect(actions[0].payload).toBe('entity-1');
    });
    
    it('should handle showEntity', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          visualizationOptions: {
            hiddenEntities: ['entity-1', 'entity-2']
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(showEntity('entity-1'));
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(showEntity.type);
      expect(actions[0].payload).toBe('entity-1');
    });
    
    it('should handle resetVisualizationOptions', () => {
      // Create mock store with initial state
      const store = mockStore({
        ui: {
          visualizationOptions: {
            layout: 'hierarchical',
            showFieldTypes: false,
            showRelationshipLabels: false,
            zoomLevel: 1.5,
            highlightedEntities: ['entity-1'],
            hiddenEntities: ['entity-2']
          }
        }
      });
      
      // Dispatch the action
      store.dispatch(resetVisualizationOptions());
      
      // Get actions from store
      const actions = store.getActions();
      
      // Assert on the actions
      expect(actions[0].type).toBe(resetVisualizationOptions.type);
    });
  });
});
