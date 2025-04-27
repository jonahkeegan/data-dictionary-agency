/**
 * Base Renderer
 * 
 * Abstract base class for all visualization renderers.
 * Defines the common interface that all renderers must implement.
 * 
 * @module visualization/renderers
 */

/**
 * Abstract base class for renderers
 */
export class BaseRenderer {
  /**
   * Create a new renderer instance
   * @param {Object} options - Renderer configuration options
   */
  constructor(options = {}) {
    if (this.constructor === BaseRenderer) {
      throw new Error('BaseRenderer is an abstract class and cannot be instantiated directly');
    }
    
    this.options = {
      width: 800,
      height: 600,
      ...options
    };
    
    this.diagramId = null;
  }

  /**
   * Render the visualization data into the specified container
   * 
   * @param {HTMLElement} container - DOM element to render the visualization into
   * @param {Object} data - Visualization data (entities and relationships)
   * @param {Object} options - Rendering options
   * @returns {Promise<Object>} - Controller for the rendered diagram
   */
  async render(container, data, options = {}) {
    throw new Error('render() method must be implemented by subclass');
  }

  /**
   * Update an existing visualization with new data
   * 
   * @param {Object} data - Updated visualization data
   * @param {Object} options - Update options
   * @returns {Promise<void>}
   */
  async update(data, options = {}) {
    throw new Error('update() method must be implemented by subclass');
  }

  /**
   * Destroy the visualization and clean up resources
   * 
   * @returns {Promise<void>}
   */
  async destroy() {
    throw new Error('destroy() method must be implemented by subclass');
  }

  /**
   * Get information about the renderer
   * 
   * @returns {Object} - Renderer information
   */
  getInfo() {
    return {
      type: this.constructor.name,
      options: this.options
    };
  }
}
