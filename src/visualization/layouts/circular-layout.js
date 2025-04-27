/**
 * Circular Layout
 * 
 * Circular layout algorithm for positioning entities in the diagram
 * Arranges entities in a circular pattern, optionally grouped by metadata
 * 
 * @module visualization/layouts/circular-layout
 */

import { BaseLayout } from './base-layout';

/**
 * Implementation of a circular layout algorithm
 */
export class CircularLayout extends BaseLayout {
  /**
   * Create a new circular layout
   * 
   * @param {Object} options - Layout options
   */
  constructor(options = {}) {
    super(options);
  }

  /**
   * Calculate positions for entities and relationships
   * 
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
    
    // Don't process empty diagrams
    if (entities.length === 0) {
      return { entities, relationships };
    }

    // Create a map of entity IDs to entities for easy lookup
    const entityMap = this.createEntityMap(entities);
    
    // Get circular layout options
    const circularOptions = this.options.circular;
    
    // Calculate layout dimensions
    const width = options.width || 800;
    const height = options.height || 600;
    const centerX = width / 2;
    const centerY = height / 2;
    
    // Calculate radius if not specified
    const radius = circularOptions.radius || 
                   Math.min(width, height) * 0.4 - Math.max(...entities.map(e => Math.max(e.dimensions.width, e.dimensions.height)));
    
    // Check if we should group entities by a property
    const groupProperty = options.groupBy || null;
    let groups = [];
    
    if (groupProperty && entities.some(e => e.metadata && e.metadata[groupProperty])) {
      // Group entities by the specified property
      const groupMap = new Map();
      
      entities.forEach(entity => {
        const groupValue = entity.metadata && entity.metadata[groupProperty] || 'unknown';
        
        if (!groupMap.has(groupValue)) {
          groupMap.set(groupValue, []);
        }
        
        groupMap.get(groupValue).push(entity);
      });
      
      groups = Array.from(groupMap.entries()).map(([name, groupEntities]) => ({
        name,
        entities: groupEntities
      }));
    } else {
      // No grouping, all entities in one group
      groups = [{
        name: 'all',
        entities: entities
      }];
    }
    
    // Position entities in groups
    await this.positionGroups(groups, centerX, centerY, radius, circularOptions);
    
    // Update relationship routing
    this.routeRelationships(relationships, entityMap);
    
    return { entities, relationships };
  }

  /**
   * Position entity groups in a circular layout
   * 
   * @private
   * @param {Array<Object>} groups - Entity groups
   * @param {number} centerX - X coordinate of the center
   * @param {number} centerY - Y coordinate of the center
   * @param {number} radius - Radius of the layout
   * @param {Object} options - Circular layout options
   * @returns {Promise<void>}
   */
  async positionGroups(groups, centerX, centerY, radius, options) {
    const groupCount = groups.length;
    
    if (groupCount === 1) {
      // Only one group, position in a simple circle
      await this.positionEntitiesInCircle(
        groups[0].entities,
        centerX,
        centerY,
        radius,
        options.startAngle,
        options.endAngle
      );
    } else {
      // Multiple groups, position in segments of the circle
      const totalAngle = options.endAngle - options.startAngle;
      const groupAngle = totalAngle / groupCount;
      
      // Add some spacing between groups
      const groupSpacing = Math.min(0.1, 0.5 / groupCount);
      const adjustedGroupAngle = groupAngle * (1 - groupSpacing);
      
      for (let i = 0; i < groupCount; i++) {
        const startAngle = options.startAngle + i * groupAngle;
        const endAngle = startAngle + adjustedGroupAngle;
        
        // Group center angle
        const groupCenterAngle = (startAngle + endAngle) / 2;
        
        // Add some padding to the group
        await this.positionEntitiesInCircle(
          groups[i].entities,
          centerX,
          centerY,
          radius,
          startAngle,
          endAngle
        );
        
        // Every few groups, allow other processes to run
        if (i % 5 === 0) {
          await new Promise(resolve => setTimeout(resolve, 0));
        }
      }
    }
  }

  /**
   * Position entities in a circular arc
   * 
   * @private
   * @param {Array<VisualEntity>} entities - Entities to position
   * @param {number} centerX - X coordinate of the center
   * @param {number} centerY - Y coordinate of the center
   * @param {number} radius - Radius of the circle
   * @param {number} startAngle - Starting angle (in radians)
   * @param {number} endAngle - Ending angle (in radians)
   * @returns {Promise<void>}
   */
  async positionEntitiesInCircle(entities, centerX, centerY, radius, startAngle, endAngle) {
    const count = entities.length;
    
    if (count === 0) {
      return;
    }
    
    // Special case for a single entity
    if (count === 1) {
      const entity = entities[0];
      entity.setPosition(
        centerX - entity.dimensions.width / 2,
        centerY - entity.dimensions.height / 2
      );
      return;
    }
    
    // Calculate angles for each entity
    const angleStep = (endAngle - startAngle) / count;
    
    // Position entities along the circle
    entities.forEach((entity, i) => {
      const angle = startAngle + i * angleStep;
      
      // Calculate position based on angle and radius
      const x = centerX + radius * Math.cos(angle) - entity.dimensions.width / 2;
      const y = centerY + radius * Math.sin(angle) - entity.dimensions.height / 2;
      
      entity.setPosition(x, y);
    });
  }

  /**
   * Route relationships for circular layout
   * 
   * @override
   * @param {Array<VisualRelationship>} relationships - Relationships to route
   * @param {Map<string, VisualEntity>} entityMap - Map of entity IDs to entities
   */
  routeRelationships(relationships, entityMap) {
    // Extension of base implementation for circular layout
    relationships.forEach(relationship => {
      const sourceEntity = entityMap.get(relationship.source);
      const targetEntity = entityMap.get(relationship.target);
      
      if (!sourceEntity || !targetEntity) {
        return;
      }
      
      // Calculate source and target centers
      const sourceCenter = {
        x: sourceEntity.position.x + sourceEntity.dimensions.width / 2,
        y: sourceEntity.position.y + sourceEntity.dimensions.height / 2
      };
      
      const targetCenter = {
        x: targetEntity.position.x + targetEntity.dimensions.width / 2,
        y: targetEntity.position.y + targetEntity.dimensions.height / 2
      };
      
      // Clear any existing path
      relationship.setPath([sourceCenter, targetCenter]);
    });
  }
}
