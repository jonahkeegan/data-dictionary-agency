/**
 * Hierarchical Layout
 * 
 * Hierarchical layout algorithm for positioning entities in the diagram
 * Arranges entities in a tree-like structure, based on relationships
 * 
 * @module visualization/layouts/hierarchical-layout
 */

import { BaseLayout } from './base-layout';

/**
 * Implementation of a hierarchical layout algorithm
 */
export class HierarchicalLayout extends BaseLayout {
  /**
   * Create a new hierarchical layout
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
    
    // Get hierarchical layout options
    const hierarchicalOptions = this.options.hierarchical;
    
    // Build the hierarchy graph
    const graph = this.buildHierarchyGraph(entities, relationships, hierarchicalOptions.direction);
    
    // Assign levels to each node
    this.assignLevels(graph);
    
    // Calculate horizontal positions
    this.calculateHorizontalPositions(graph, hierarchicalOptions);
    
    // Calculate layout dimensions
    const width = options.width || 800;
    const height = options.height || 600;
    
    // Position entities based on the graph
    this.positionEntities(entities, graph, width, height, hierarchicalOptions);
    
    // Update relationship routing
    this.routeRelationships(relationships, entityMap);
    
    return { entities, relationships };
  }

  /**
   * Build a hierarchy graph from entities and relationships
   * 
   * @private
   * @param {Array<VisualEntity>} entities - Entities to position
   * @param {Array<VisualRelationship>} relationships - Relationships between entities
   * @param {string} direction - Layout direction ('TB', 'LR', 'RL', 'BT')
   * @returns {Object} - Hierarchy graph
   */
  buildHierarchyGraph(entities, relationships, direction) {
    // Create nodes for all entities
    const nodes = entities.map(entity => ({
      id: entity.id,
      width: entity.dimensions.width,
      height: entity.dimensions.height,
      entity: entity,
      parents: [],
      children: [],
      level: -1,
      position: {
        x: 0,
        y: 0
      }
    }));
    
    // Create node map for easy lookup
    const nodeMap = new Map();
    nodes.forEach(node => nodeMap.set(node.id, node));
    
    // Add edges between nodes based on relationships
    relationships.forEach(relationship => {
      const sourceNode = nodeMap.get(relationship.source);
      const targetNode = nodeMap.get(relationship.target);
      
      if (!sourceNode || !targetNode) {
        return;
      }
      
      // Determine parent/child relationship based on relationship type
      // and direction
      if (relationship.type === 'composition' || relationship.type === 'aggregation') {
        // In composition/aggregation, source is parent of target
        sourceNode.children.push(targetNode);
        targetNode.parents.push(sourceNode);
      } else if (relationship.type === 'inheritance') {
        // In inheritance, target is parent of source
        targetNode.children.push(sourceNode);
        sourceNode.parents.push(targetNode);
      } else {
        // For other relationships, determine based on layout direction
        if (direction === 'TB' || direction === 'LR') {
          sourceNode.children.push(targetNode);
          targetNode.parents.push(sourceNode);
        } else {
          targetNode.children.push(sourceNode);
          sourceNode.parents.push(targetNode);
        }
      }
    });
    
    // If a node has no parents and no children, make all unassigned nodes its children
    // This ensures all nodes are included in the hierarchy
    const rootNodes = nodes.filter(node => node.parents.length === 0);
    const isolated = nodes.filter(node => node.parents.length === 0 && node.children.length === 0);
    
    if (isolated.length > 0 && rootNodes.length > 0) {
      const mainRoot = rootNodes.find(node => node.children.length > 0) || rootNodes[0];
      
      isolated.forEach(node => {
        if (node !== mainRoot) {
          mainRoot.children.push(node);
          node.parents.push(mainRoot);
        }
      });
    }
    
    return {
      nodes,
      nodeMap,
      direction
    };
  }

  /**
   * Assign levels to nodes in the graph
   * 
   * @private
   * @param {Object} graph - Hierarchy graph
   */
  assignLevels(graph) {
    // Find root nodes (nodes with no parents)
    const rootNodes = graph.nodes.filter(node => node.parents.length === 0);
    
    // If there are no root nodes, use the first node as root
    if (rootNodes.length === 0 && graph.nodes.length > 0) {
      rootNodes.push(graph.nodes[0]);
    }
    
    // Set the level of root nodes to 0
    rootNodes.forEach(root => {
      root.level = 0;
    });
    
    // Breadth-first traversal to assign levels
    const queue = [...rootNodes];
    const visited = new Set();
    
    while (queue.length > 0) {
      const node = queue.shift();
      
      if (visited.has(node.id)) {
        continue;
      }
      
      visited.add(node.id);
      
      // Visit children
      node.children.forEach(child => {
        // Set the child's level to one more than the parent's level
        // If the child already has a level, use the maximum
        if (child.level === -1 || child.level <= node.level) {
          child.level = node.level + 1;
        }
        
        queue.push(child);
      });
    }
    
    // Handle nodes that weren't assigned a level
    // (could happen if there are disconnected subgraphs)
    graph.nodes.forEach(node => {
      if (node.level === -1) {
        node.level = 0;
      }
    });
    
    // Calculate the maximum level
    graph.maxLevel = Math.max(...graph.nodes.map(node => node.level));
  }

  /**
   * Calculate horizontal positions for nodes
   * 
   * @private
   * @param {Object} graph - Hierarchy graph
   * @param {Object} options - Layout options
   */
  calculateHorizontalPositions(graph, options) {
    // Group nodes by level
    const levels = new Array(graph.maxLevel + 1).fill(0).map(() => []);
    
    graph.nodes.forEach(node => {
      levels[node.level].push(node);
    });
    
    // Sort nodes within each level
    levels.forEach(level => {
      // Sort based on the median position of parents/children
      level.sort((a, b) => {
        // If a node has no connections, it gets positioned arbitrarily
        if (a.parents.length === 0 && a.children.length === 0) {
          return -1;
        }
        
        if (b.parents.length === 0 && b.children.length === 0) {
          return 1;
        }
        
        // Calculate median positions
        const aConnections = [...a.parents, ...a.children].filter(node => node.position.x !== 0);
        const bConnections = [...b.parents, ...b.children].filter(node => node.position.x !== 0);
        
        if (aConnections.length === 0 && bConnections.length === 0) {
          return 0;
        }
        
        if (aConnections.length === 0) {
          return -1;
        }
        
        if (bConnections.length === 0) {
          return 1;
        }
        
        const aMedian = aConnections.reduce((sum, node) => sum + node.position.x, 0) / aConnections.length;
        const bMedian = bConnections.reduce((sum, node) => sum + node.position.x, 0) / bConnections.length;
        
        return aMedian - bMedian;
      });
    });
    
    // Assign x positions within each level
    levels.forEach((level, levelIndex) => {
      // Calculate total width of nodes at this level
      const totalWidth = level.reduce((sum, node) => sum + node.width, 0);
      
      // Calculate total spacing between nodes
      const spacing = options.nodeDistance;
      const totalSpacing = (level.length - 1) * spacing;
      
      // Calculate the width needed for this level
      const levelWidth = totalWidth + totalSpacing;
      
      // Assign x positions
      let currentX = -levelWidth / 2;
      
      level.forEach(node => {
        node.position.x = currentX + node.width / 2;
        currentX += node.width + spacing;
      });
    });
  }

  /**
   * Position entities based on the hierarchical graph
   * 
   * @private
   * @param {Array<VisualEntity>} entities - Entities to position
   * @param {Object} graph - Hierarchy graph
   * @param {number} width - Layout width
   * @param {number} height - Layout height
   * @param {Object} options - Layout options
   */
  positionEntities(entities, graph, width, height, options) {
    // Get layout direction
    const direction = options.direction;
    const levelDistance = options.levelDistance;
    
    // Calculate total height needed for the layout
    const totalLevels = graph.maxLevel + 1;
    const totalHeight = totalLevels * levelDistance;
    
    // Position each entity based on its node in the graph
    entities.forEach(entity => {
      const node = graph.nodeMap.get(entity.id);
      
      if (!node) {
        return;
      }
      
      const levelPosition = node.level * levelDistance - totalHeight / 2 + levelDistance / 2;
      
      // Apply position based on direction
      if (direction === 'TB') {
        // Top to bottom
        entity.setPosition(
          width / 2 + node.position.x - entity.dimensions.width / 2,
          height / 2 + levelPosition - entity.dimensions.height / 2
        );
      } else if (direction === 'BT') {
        // Bottom to top
        entity.setPosition(
          width / 2 + node.position.x - entity.dimensions.width / 2,
          height / 2 - levelPosition - entity.dimensions.height / 2
        );
      } else if (direction === 'LR') {
        // Left to right
        entity.setPosition(
          width / 2 + levelPosition - entity.dimensions.width / 2,
          height / 2 + node.position.x - entity.dimensions.height / 2
        );
      } else if (direction === 'RL') {
        // Right to left
        entity.setPosition(
          width / 2 - levelPosition - entity.dimensions.width / 2,
          height / 2 + node.position.x - entity.dimensions.height / 2
        );
      }
    });
  }

  /**
   * Route relationships for hierarchical layout
   * 
   * @override
   * @param {Array<VisualRelationship>} relationships - Relationships to route
   * @param {Map<string, VisualEntity>} entityMap - Map of entity IDs to entities
   */
  routeRelationships(relationships, entityMap) {
    // Enhanced routing for hierarchical layout
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
      
      // For hierarchical layout, we'll use an orthogonal routing
      // with a midpoint between the entities
      const midPoint = {
        x: (sourceCenter.x + targetCenter.x) / 2,
        y: (sourceCenter.y + targetCenter.y) / 2
      };
      
      // Set relationship path
      relationship.setPath([sourceCenter, midPoint, targetCenter]);
    });
  }
}
