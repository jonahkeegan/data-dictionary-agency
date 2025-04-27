/**
 * Renderer Factory
 * 
 * Factory for creating renderer instances based on the specified type.
 * 
 * @module visualization/renderers
 */

import { D3Renderer } from './d3-renderer';

/**
 * Factory for creating renderer instances
 */
export class RendererFactory {
  /**
   * Create a new RendererFactory instance
   */
  constructor() {
    // Registry of available renderers
    this.rendererRegistry = {
      'd3': D3Renderer
    };
  }

  /**
   * Register a new renderer type
   * 
   * @param {string} type - Renderer type identifier
   * @param {class} rendererClass - Renderer class
   */
  registerRenderer(type, rendererClass) {
    if (typeof type !== 'string' || !type) {
      throw new Error('Renderer type must be a non-empty string');
    }
    
    if (typeof rendererClass !== 'function') {
      throw new Error('Renderer class must be a constructor function');
    }
    
    this.rendererRegistry[type] = rendererClass;
  }

  /**
   * Create a renderer instance of the specified type
   * 
   * @param {string} type - Type of renderer to create
   * @param {Object} options - Options to pass to the renderer
   * @returns {Object} - Renderer instance
   */
  createRenderer(type, options = {}) {
    // Default to D3 renderer if type not specified
    const rendererType = type || 'd3';
    
    const RendererClass = this.rendererRegistry[rendererType];
    
    if (!RendererClass) {
      throw new Error(`Renderer type '${rendererType}' is not registered`);
    }
    
    return new RendererClass(options);
  }

  /**
   * Get a list of available renderer types
   * 
   * @returns {Array<string>} - Array of available renderer types
   */
  getAvailableRenderers() {
    return Object.keys(this.rendererRegistry);
  }

  /**
   * Check if a renderer type is available
   * 
   * @param {string} type - Renderer type to check
   * @returns {boolean} - True if the renderer type is available
   */
  hasRenderer(type) {
    return !!this.rendererRegistry[type];
  }
}
