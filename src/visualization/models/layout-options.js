/**
 * Layout Options Model
 * 
 * Configuration options for layout algorithms
 * 
 * @module visualization/models/layout-options
 */

/**
 * Represents configuration options for diagram layouts
 */
export class LayoutOptions {
  /**
   * Create layout configuration options
   * 
   * @param {Object} config - Configuration options
   * @param {string} config.type - Layout algorithm type ('force-directed', 'hierarchical', 'circular')
   * @param {Object} config.force - Force-directed layout options
   * @param {Object} config.hierarchical - Hierarchical layout options
   * @param {Object} config.circular - Circular layout options
   * @param {boolean} config.incrementalLayout - Whether to apply layout incrementally
   * @param {Object} config.padding - Padding between entities
   */
  constructor({
    type = 'force-directed',
    force = {},
    hierarchical = {},
    circular = {},
    incrementalLayout = true,
    padding = { x: 50, y: 50 }
  } = {}) {
    this.type = type;
    
    // Force-directed layout options
    this.force = {
      strength: -300,          // Repulsive force between nodes
      distance: 150,           // Target distance between linked nodes
      iterations: 300,         // Number of simulation steps
      alpha: 0.3,              // Initial alpha (simulation "temperature")
      alphaDecay: 0.0228,      // Alpha decay rate
      velocityDecay: 0.4,      // Velocity decay rate (friction)
      ...force
    };
    
    // Hierarchical layout options
    this.hierarchical = {
      direction: 'TB',         // Direction: TB (top-bottom), LR (left-right), RL, BT
      levelDistance: 150,      // Distance between levels
      nodeDistance: 100,       // Minimum distance between nodes on same level
      sortMethod: 'optimal',   // Node sorting method: optimal, directed, hubsize, simple
      ...hierarchical
    };
    
    // Circular layout options
    this.circular = {
      radius: null,            // Radius (auto-calculated if null)
      startAngle: 0,           // Starting angle in radians
      endAngle: 2 * Math.PI,   // Ending angle in radians
      spacing: 30,             // Spacing between nodes
      ...circular
    };
    
    this.incrementalLayout = incrementalLayout;
    this.padding = padding;
  }

  /**
   * Get options for the specified layout type
   * 
   * @returns {Object} - Options for the current layout type
   */
  getTypeOptions() {
    switch (this.type) {
      case 'force-directed':
        return this.force;
      case 'hierarchical':
        return this.hierarchical;
      case 'circular':
        return this.circular;
      default:
        return this.force;
    }
  }

  /**
   * Clone this options object
   * 
   * @returns {LayoutOptions} - A new options object with the same properties
   */
  clone() {
    return new LayoutOptions({
      type: this.type,
      force: { ...this.force },
      hierarchical: { ...this.hierarchical },
      circular: { ...this.circular },
      incrementalLayout: this.incrementalLayout,
      padding: { ...this.padding }
    });
  }
  
  /**
   * Update options with new values
   * 
   * @param {Object} newOptions - New options to apply
   * @returns {LayoutOptions} - This options object (for chaining)
   */
  update(newOptions) {
    if (!newOptions) return this;
    
    if (newOptions.type) {
      this.type = newOptions.type;
    }
    
    if (newOptions.force) {
      this.force = {
        ...this.force,
        ...newOptions.force
      };
    }
    
    if (newOptions.hierarchical) {
      this.hierarchical = {
        ...this.hierarchical,
        ...newOptions.hierarchical
      };
    }
    
    if (newOptions.circular) {
      this.circular = {
        ...this.circular,
        ...newOptions.circular
      };
    }
    
    if (newOptions.incrementalLayout !== undefined) {
      this.incrementalLayout = newOptions.incrementalLayout;
    }
    
    if (newOptions.padding) {
      this.padding = {
        ...this.padding,
        ...newOptions.padding
      };
    }
    
    return this;
  }
}
