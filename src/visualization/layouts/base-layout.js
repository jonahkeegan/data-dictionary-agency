/**
 * Base Layout
 * 
 * Abstract base class for layout algorithms
 * 
 * @module visualization/layouts/base-layout
 */

import { LayoutOptions } from '../models/layout-options';

/**
 * Abstract base class for layout algorithms
 */
export class BaseLayout {
  /**
   * Create a new layout instance
   * 
   * @param {Object} options - Layout options
   */
  constructor(options = {}) {
    this.options = new LayoutOptions(options);
  }

  /**
   * Calculate positions for entities and relationships
   * 
   * @abstract
   * @param {Array<VisualEntity>} entities - Entities to position
   * @param {Array<VisualRelationship>} relationships - Relationships to route
   * @param {Object} options - Additional layout options
   * @returns {Promise<Object>} - Positioned entities and relationships
   */
  async calculatePositions(entities, relationships, options = {}) {
    // Update options
    if (options) {
      this.options.update(options);
    }
    
    // This method should be overridden by subclasses
    throw new Error('BaseLayout.calculatePositions must be implemented by subclass');
  }

  /**
   * Calculate dimensions needed for the layout
   * 
   * @param {Array<VisualEntity>} entities - Entities to lay out
   * @returns {Object} - Required dimensions {width, height}
   */
  calculateRequiredDimensions(entities) {
    // Find the bounding box of all entities
    let minX = Number.MAX_VALUE;
    let minY = Number.MAX_VALUE;
    let maxX = Number.MIN_VALUE;
    let maxY = Number.MIN_VALUE;
    
    for (const entity of entities) {
      const x = entity.position.x;
      const y = entity.position.y;
      const width = entity.dimensions.width;
      const height = entity.dimensions.height;
      
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x + width);
      maxY = Math.max(maxY, y + height);
    }
    
    // Add padding
    minX -= this.options.padding.x;
    minY -= this.options.padding.y;
    maxX += this.options.padding.x;
    maxY += this.options.padding.y;
    
    return {
      x: minX,
      y: minY,
      width: maxX - minX,
      height: maxY - minY
    };
  }

  /**
   * Set the initial positions of entities
   * 
   * @param {Array<VisualEntity>} entities - Entities to position
   * @param {Object} bounds - Bounds to position within {width, height}
   */
  setInitialPositions(entities, bounds) {
    const { width, height } = bounds;
    const count = entities.length;
    
    if (count === 0) {
      return;
    }
    
    // Calculate grid dimensions based on aspect ratio
    const gridWidth = Math.ceil(Math.sqrt(count * width / height));
    const gridHeight = Math.ceil(count / gridWidth);
    
    // Calculate cell size
    const cellWidth = width / gridWidth;
    const cellHeight = height / gridHeight;
    
    // Place entities in a grid pattern
    for (let i = 0; i < count; i++) {
      const gridX = i % gridWidth;
      const gridY = Math.floor(i / gridWidth);
      
      const x = gridX * cellWidth + cellWidth / 2 - entities[i].dimensions.width / 2;
      const y = gridY * cellHeight + cellHeight / 2 - entities[i].dimensions.height / 2;
      
      entities[i].setPosition(x, y);
    }
  }

  /**
   * Update relationship routing based on entity positions
   * 
   * @param {Array<VisualRelationship>} relationships - Relationships to route
   * @param {Map<string, VisualEntity>} entityMap - Map of entity IDs to entities
   */
  routeRelationships(relationships, entityMap) {
    // Basic straight-line routing (to be extended by subclasses)
    relationships.forEach(relationship => {
      const sourceEntity = entityMap.get(relationship.source);
      const targetEntity = entityMap.get(relationship.target);
      
      if (!sourceEntity || !targetEntity) {
        return;
      }
      
      // Clear any existing path
      relationship.setPath([]);
    });
  }

  /**
   * Create a map of entity IDs to entities
   * 
   * @param {Array<VisualEntity>} entities - Entities to map
   * @returns {Map<string, VisualEntity>} - Map of entity IDs to entities
   */
  createEntityMap(entities) {
    const entityMap = new Map();
    
    for (const entity of entities) {
      entityMap.set(entity.id, entity);
    }
    
    return entityMap;
  }
}
