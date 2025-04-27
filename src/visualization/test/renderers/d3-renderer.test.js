/**
 * D3Renderer Tests
 *
 * Tests for the D3.js-based visualization renderer.
 */

import { D3Renderer } from '../../renderers/d3-renderer';
import { EventBus } from '../../events/event-bus';

// Mock D3 and DOM behavior
jest.mock('d3', () => {
  return {
    select: jest.fn(() => ({
      selectAll: jest.fn(() => ({
        remove: jest.fn(),
      })),
      append: jest.fn(() => ({
        attr: jest.fn(() => ({
          attr: jest.fn(() => ({
            attr: jest.fn(() => ({
              style: jest.fn(() => ({
                style: jest.fn(),
              })),
            })),
          })),
          style: jest.fn(),
          append: jest.fn(() => ({
            attr: jest.fn(() => ({
              attr: jest.fn(() => ({
                append: jest.fn(() => ({
                  attr: jest.fn(() => ({
                    attr: jest.fn(),
                  })),
                })),
              })),
            })),
          })),
        })),
      })),
      on: jest.fn(),
      node: jest.fn(() => ({})),
      call: jest.fn(),
    })),
    zoom: jest.fn(() => ({
      scaleExtent: jest.fn(() => ({
        on: jest.fn(),
      })),
    })),
    drag: jest.fn(() => ({
      on: jest.fn(() => ({
        on: jest.fn(() => ({
          on: jest.fn(),
        })),
      })),
    })),
  };
});

// Mock UUID to return predictable values for testing
jest.mock('uuid', () => ({
  v4: jest.fn(() => 'test-uuid'),
}));

// Create a mock document object for DOM operations
global.document = {
  createElement: jest.fn(() => ({
    getBoundingClientRect: jest.fn(() => ({ width: 100, height: 100 })),
  })),
};

// Create a mock window object for event handlers
global.window = {};

describe('D3Renderer', () => {
  let renderer;
  let container;
  let eventBus;
  
  beforeEach(() => {
    // Create mock container
    container = document.createElement('div');
    
    // Create event bus
    eventBus = new EventBus();
    
    // Create renderer
    renderer = new D3Renderer({ 
      eventBus,
      width: 800, 
      height: 600 
    });
  });
  
  afterEach(() => {
    // Clean up
    jest.clearAllMocks();
  });
  
  describe('constructor', () => {
    it('initializes with default options', () => {
      const defaultRenderer = new D3Renderer();
      expect(defaultRenderer.options.width).toBeDefined();
      expect(defaultRenderer.options.height).toBeDefined();
      expect(defaultRenderer.diagramId).toBe('test-uuid');
    });
    
    it('merges provided options with defaults', () => {
      const options = { 
        width: 1000, 
        height: 800,
        fontFamily: 'Helvetica, sans-serif',
      };
      
      const customRenderer = new D3Renderer(options);
      expect(customRenderer.options.width).toBe(1000);
      expect(customRenderer.options.height).toBe(800);
      expect(customRenderer.options.fontFamily).toBe('Helvetica, sans-serif');
      expect(customRenderer.options.entityFill).toBeDefined();
    });
  });
  
  describe('render', () => {
    it('creates SVG container with correct dimensions', async () => {
      const entities = [];
      const relationships = [];
      
      await renderer.render(container, { entities, relationships });
      
      expect(renderer.svg).toBeDefined();
    });
    
    it('throws an error if container is missing', async () => {
      await expect(
        renderer.render(null, { entities: [], relationships: [] })
      ).rejects.toThrow('Container element is required');
    });
    
    it('returns a controller object', async () => {
      const controller = await renderer.render(
        container, 
        { entities: [], relationships: [] }
      );
      
      expect(controller).toBeDefined();
      expect(controller.diagramId).toBe('test-uuid');
      expect(typeof controller.update).toBe('function');
      expect(typeof controller.destroy).toBe('function');
      expect(typeof controller.select).toBe('function');
      expect(typeof controller.getInfo).toBe('function');
    });
  });
  
  describe('update', () => {
    it('throws an error if diagram is not rendered', async () => {
      await expect(
        renderer.update({ entities: [], relationships: [] })
      ).rejects.toThrow('Cannot update: visualization not rendered');
    });
  });
  
  describe('destroy', () => {
    it('cleans up resources', async () => {
      // First render
      await renderer.render(container, { entities: [], relationships: [] });
      
      // Then destroy
      const result = await renderer.destroy();
      
      expect(result).toBe(true);
      expect(renderer.svg).toBeNull();
    });
    
    it('returns false if not rendered', async () => {
      const result = await renderer.destroy();
      expect(result).toBe(false);
    });
  });
  
  describe('event handling', () => {
    it('publishes events through event bus', async () => {
      // Spy on event bus
      const publishSpy = jest.spyOn(eventBus, 'publish');
      
      // Render diagram
      await renderer.render(container, { entities: [], relationships: [] });
      
      // Simulate zoom event
      const zoomCallback = renderer.zoom.on.mock.calls[0][1];
      zoomCallback({ transform: { k: 2, x: 100, y: 50 } });
      
      // Verify event was published
      expect(publishSpy).toHaveBeenCalledWith('interaction.zoom', {
        scale: 2,
        point: [100, 50]
      });
    });
  });
  
  describe('rendering entities', () => {
    it('handles empty entities array', async () => {
      await renderer.render(container, { entities: [], relationships: [] });
      expect(renderer.entities.size).toBe(0);
    });
    
    it('throws an error if entities is not an array', async () => {
      await renderer.render(container, { entities: [], relationships: [] });
      await expect(
        renderer.renderEntities({})
      ).rejects.toThrow('Entities must be an array');
    });
  });
  
  describe('rendering relationships', () => {
    it('handles empty relationships array', async () => {
      await renderer.render(container, { entities: [], relationships: [] });
      expect(renderer.relationships.size).toBe(0);
    });
    
    it('throws an error if relationships is not an array', async () => {
      await renderer.render(container, { entities: [], relationships: [] });
      await expect(
        renderer.renderRelationships({})
      ).rejects.toThrow('Relationships must be an array');
    });
  });
});
