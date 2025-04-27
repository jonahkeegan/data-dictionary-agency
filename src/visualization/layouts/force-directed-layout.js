/**
 * Force-Directed Layout
 * 
 * Force-directed layout algorithm for positioning entities in the diagram
 * Uses a physics simulation to distribute entities and minimize edge crossings
 * 
 * @module visualization/layouts/force-directed-layout
 */

import { BaseLayout } from './base-layout';

/**
 * Implementation of a force-directed layout algorithm
 */
export class ForceDirectedLayout extends BaseLayout {
  /**
   * Create a new force-directed layout
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
    
    // Clone entities to avoid modifying the originals during simulation
    const simulationEntities = entities.map(entity => ({
      id: entity.id,
      x: entity.position.x + entity.dimensions.width / 2,
      y: entity.position.y + entity.dimensions.height / 2,
      width: entity.dimensions.width,
      height: entity.dimensions.height,
      vx: 0,
      vy: 0
    }));
    
    // Clone relationships for the simulation
    const simulationLinks = relationships.map(relationship => ({
      source: relationship.source,
      target: relationship.target,
      id: relationship.id
    }));
    
    // Set initial positions if they're not already set
    const initialBounds = {
      width: options.width || 800,
      height: options.height || 600
    };
    
    // Check if entities already have positions
    const needsInitialPositions = simulationEntities.some(
      entity => (entity.x === 0 && entity.y === 0)
    );
    
    if (needsInitialPositions) {
      this.setInitialSimulationPositions(simulationEntities, initialBounds);
    }
    
    // Run the force-directed simulation
    await this.runSimulation(simulationEntities, simulationLinks);
    
    // Update the original entities with the new positions
    simulationEntities.forEach(simEntity => {
      const entity = entityMap.get(simEntity.id);
      if (entity) {
        // Position is the center of the entity, so adjust for dimensions
        entity.setPosition(
          simEntity.x - entity.dimensions.width / 2,
          simEntity.y - entity.dimensions.height / 2
        );
      }
    });
    
    // Update relationship routing
    this.routeRelationships(relationships, entityMap);
    
    return { entities, relationships };
  }

  /**
   * Set initial positions for simulation entities
   * 
   * @private
   * @param {Array<Object>} simulationEntities - Entities in the simulation
   * @param {Object} bounds - Bounds to position within {width, height}
   */
  setInitialSimulationPositions(simulationEntities, bounds) {
    const { width, height } = bounds;
    const count = simulationEntities.length;
    
    if (count === 0) {
      return;
    }
    
    // Use different initialization strategies based on the number of entities
    if (count <= 10) {
      // For small diagrams, arrange in a circle
      const radius = Math.min(width, height) * 0.35;
      const centerX = width / 2;
      const centerY = height / 2;
      
      simulationEntities.forEach((entity, i) => {
        const angle = (i / count) * 2 * Math.PI;
        entity.x = centerX + radius * Math.cos(angle);
        entity.y = centerY + radius * Math.sin(angle);
      });
    } else {
      // For larger diagrams, use a grid with some randomization
      const gridWidth = Math.ceil(Math.sqrt(count));
      const gridHeight = Math.ceil(count / gridWidth);
      
      const cellWidth = width / gridWidth;
      const cellHeight = height / gridHeight;
      
      simulationEntities.forEach((entity, i) => {
        const gridX = i % gridWidth;
        const gridY = Math.floor(i / gridWidth);
        
        // Add some randomness to prevent perfect grid alignments
        const jitter = () => (Math.random() - 0.5) * Math.min(cellWidth, cellHeight) * 0.3;
        
        entity.x = gridX * cellWidth + cellWidth / 2 + jitter();
        entity.y = gridY * cellHeight + cellHeight / 2 + jitter();
      });
    }
  }

  /**
   * Run the force-directed simulation
   * 
   * @private
   * @param {Array<Object>} nodes - Simulation nodes (entities)
   * @param {Array<Object>} links - Simulation links (relationships)
   * @returns {Promise<void>} - Promise that resolves when simulation is complete
   */
  async runSimulation(nodes, links) {
    // Convert links to use references instead of IDs
    const nodeMap = new Map();
    nodes.forEach(node => nodeMap.set(node.id, node));
    
    const processedLinks = links.map(link => ({
      source: nodeMap.get(link.source),
      target: nodeMap.get(link.target),
      id: link.id
    })).filter(link => link.source && link.target);
    
    // Get force options from layout options
    const options = this.options.force;
    
    // Apply forces for the specified number of iterations
    for (let i = 0; i < options.iterations; i++) {
      // Calculate forces
      this.applyRepulsiveForces(nodes, options.strength);
      this.applyAttractionForces(processedLinks, options.distance);
      
      // Update positions
      this.updatePositions(nodes, options);
      
      // Every 50 iterations, allow other processes to run
      if (i % 50 === 0) {
        await new Promise(resolve => setTimeout(resolve, 0));
      }
    }
  }

  /**
   * Apply repulsive forces between all nodes
   * 
   * @private
   * @param {Array<Object>} nodes - Simulation nodes
   * @param {number} strength - Repulsive force strength
   */
  applyRepulsiveForces(nodes, strength) {
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const nodeA = nodes[i];
        const nodeB = nodes[j];
        
        const dx = nodeB.x - nodeA.x;
        const dy = nodeB.y - nodeA.y;
        const distance = Math.sqrt(dx * dx + dy * dy) || 1;
        
        // Adjust distance to account for node sizes
        const minDistance = (nodeA.width + nodeB.width + nodeA.height + nodeB.height) / 4;
        
        // Apply inverse square force
        const force = strength / (distance * distance);
        
        // Normalize direction
        const unitX = dx / distance;
        const unitY = dy / distance;
        
        // Apply force (with stronger repulsion for overlapping nodes)
        const forceFactor = distance < minDistance ? force * 2 : force;
        
        nodeA.vx -= unitX * forceFactor;
        nodeA.vy -= unitY * forceFactor;
        nodeB.vx += unitX * forceFactor;
        nodeB.vy += unitY * forceFactor;
      }
    }
  }

  /**
   * Apply attractive forces along links
   * 
   * @private
   * @param {Array<Object>} links - Simulation links
   * @param {number} distance - Target distance for links
   */
  applyAttractionForces(links, distance) {
    for (const link of links) {
      const sourceNode = link.source;
      const targetNode = link.target;
      
      const dx = targetNode.x - sourceNode.x;
      const dy = targetNode.y - sourceNode.y;
      const currentDistance = Math.sqrt(dx * dx + dy * dy) || 1;
      
      // Calculate force based on difference from target distance
      const force = (currentDistance - distance) * 0.1;
      
      // Normalize direction
      const unitX = dx / currentDistance;
      const unitY = dy / currentDistance;
      
      // Apply force
      sourceNode.vx += unitX * force;
      sourceNode.vy += unitY * force;
      targetNode.vx -= unitX * force;
      targetNode.vy -= unitY * force;
    }
  }

  /**
   * Update node positions based on velocities
   * 
   * @private
   * @param {Array<Object>} nodes - Simulation nodes
   * @param {Object} options - Simulation options
   */
  updatePositions(nodes, options) {
    const alpha = options.alpha;
    const velocityDecay = options.velocityDecay;
    
    for (const node of nodes) {
      // Apply velocity
      node.x += node.vx * alpha;
      node.y += node.vy * alpha;
      
      // Apply velocity decay (friction)
      node.vx *= velocityDecay;
      node.vy *= velocityDecay;
    }
  }
}
