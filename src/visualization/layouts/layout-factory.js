/**
 * Layout Factory
 * 
 * Factory for creating layout algorithm instances
 * 
 * @module visualization/layouts/layout-factory
 */

import { ForceDirectedLayout } from './force-directed-layout';
import { HierarchicalLayout } from './hierarchical-layout';
import { CircularLayout } from './circular-layout';

/**
 * Factory for creating layout algorithm instances
 */
export class LayoutFactory {
  /**
   * Create a new layout factory
   */
  constructor() {
    this.layoutTypes = new Map();
    
    // Register default layouts
    this.registerLayout('force-directed', ForceDirectedLayout);
    this.registerLayout('hierarchical', HierarchicalLayout);
    this.registerLayout('circular', CircularLayout);
  }

  /**
   * Register a layout implementation
   * 
   * @param {string} type - Layout type identifier
   * @param {Class} layoutClass - Layout implementation class
   * @returns {LayoutFactory} - This factory (for chaining)
   */
  registerLayout(type, layoutClass) {
    this.layoutTypes.set(type, layoutClass);
    return this;
  }

  /**
   * Create a layout algorithm instance
   * 
   * @param {string} type - Layout type identifier
   * @param {Object} options - Layout options
   * @returns {BaseLayout} - Layout instance
   */
  createLayout(type = 'force-directed', options = {}) {
    const LayoutClass = this.layoutTypes.get(type);
    
    if (!LayoutClass) {
      throw new Error(`Layout type '${type}' not registered`);
    }
    
    return new LayoutClass(options);
  }

  /**
   * Get list of available layout types
   * 
   * @returns {Array<string>} - Array of layout type identifiers
   */
  getAvailableLayouts() {
    return Array.from(this.layoutTypes.keys());
  }
}
