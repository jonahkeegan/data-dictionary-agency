/**
 * Visualization Engine Test
 * 
 * This file demonstrates how to use the visualization engine.
 * 
 * @module visualization/test-visualization
 */

import { VisualizationAPI } from './api/visualization-api';
import { VisualEntity, VisualRelationship } from './models';
import { EventBus } from './events/event-bus';

/**
 * Create a sample visualization
 * 
 * @param {HTMLElement} container - DOM container element
 * @returns {Promise<Object>} - Visualization controller
 */
export async function createSampleVisualization(container) {
  // Create event bus for communication
  const eventBus = new EventBus();
  
  // Create visualization API
  const visualizationAPI = new VisualizationAPI({ 
    eventBus,
    defaultLayout: 'force-directed', 
    defaultWidth: 800, 
    defaultHeight: 600 
  });
  
  // Create sample entities
  const entities = [
    new VisualEntity({
      id: 'entity1',
      label: 'User',
      type: 'table',
      properties: [
        { name: 'id', type: 'integer', isPrimary: true },
        { name: 'username', type: 'string', isRequired: true },
        { name: 'email', type: 'string', isRequired: true },
        { name: 'createdAt', type: 'datetime' }
      ]
    }),
    new VisualEntity({
      id: 'entity2',
      label: 'Order',
      type: 'table',
      properties: [
        { name: 'id', type: 'integer', isPrimary: true },
        { name: 'userId', type: 'integer', isRequired: true },
        { name: 'orderDate', type: 'datetime', isRequired: true },
        { name: 'total', type: 'decimal' }
      ]
    }),
    new VisualEntity({
      id: 'entity3',
      label: 'Product',
      type: 'table',
      properties: [
        { name: 'id', type: 'integer', isPrimary: true },
        { name: 'name', type: 'string', isRequired: true },
        { name: 'price', type: 'decimal', isRequired: true },
        { name: 'stock', type: 'integer' }
      ]
    }),
    new VisualEntity({
      id: 'entity4',
      label: 'OrderItem',
      type: 'table',
      properties: [
        { name: 'id', type: 'integer', isPrimary: true },
        { name: 'orderId', type: 'integer', isRequired: true },
        { name: 'productId', type: 'integer', isRequired: true },
        { name: 'quantity', type: 'integer', isRequired: true },
        { name: 'price', type: 'decimal', isRequired: true }
      ]
    })
  ];
  
  // Create sample relationships
  const relationships = [
    new VisualRelationship({
      id: 'rel1',
      source: 'entity1',
      target: 'entity2',
      type: 'oneToMany',
      label: 'places',
      sourceCardinality: '1',
      targetCardinality: '*'
    }),
    new VisualRelationship({
      id: 'rel2',
      source: 'entity2',
      target: 'entity4',
      type: 'oneToMany',
      label: 'contains',
      sourceCardinality: '1',
      targetCardinality: '*'
    }),
    new VisualRelationship({
      id: 'rel3',
      source: 'entity3',
      target: 'entity4',
      type: 'oneToMany',
      label: 'included in',
      sourceCardinality: '1',
      targetCardinality: '*'
    })
  ];
  
  // Generate diagram with force-directed layout
  return visualizationAPI.generateDiagram(container, entities, relationships, {
    layout: 'force-directed',
    width: container.clientWidth || 800,
    height: container.clientHeight || 600
  });
}

/**
 * Create a sample visualization with hierarchical layout
 * 
 * @param {HTMLElement} container - DOM container element
 * @returns {Promise<Object>} - Visualization controller
 */
export async function createHierarchicalVisualization(container) {
  // Create event bus for communication
  const eventBus = new EventBus();
  
  // Create visualization API
  const visualizationAPI = new VisualizationAPI({ 
    eventBus,
    defaultLayout: 'hierarchical', 
    defaultWidth: 800, 
    defaultHeight: 600 
  });
  
  // Create sample entities (similar to above)
  const entities = [/* same as above */];
  
  // Create sample relationships (similar to above)
  const relationships = [/* same as above */];
  
  // Generate diagram with hierarchical layout
  return visualizationAPI.generateDiagram(container, entities, relationships, {
    layout: 'hierarchical',
    width: container.clientWidth || 800,
    height: container.clientHeight || 600,
    hierarchical: {
      direction: 'TB', // Top to bottom
      levelDistance: 150,
      nodeDistance: 100
    }
  });
}

/**
 * Create a sample visualization with circular layout
 * 
 * @param {HTMLElement} container - DOM container element
 * @returns {Promise<Object>} - Visualization controller
 */
export async function createCircularVisualization(container) {
  // Create event bus for communication
  const eventBus = new EventBus();
  
  // Create visualization API
  const visualizationAPI = new VisualizationAPI({ 
    eventBus,
    defaultLayout: 'circular', 
    defaultWidth: 800, 
    defaultHeight: 600 
  });
  
  // Create sample entities (similar to above)
  const entities = [/* same as above */];
  
  // Create sample relationships (similar to above)
  const relationships = [/* same as above */];
  
  // Generate diagram with circular layout
  return visualizationAPI.generateDiagram(container, entities, relationships, {
    layout: 'circular',
    width: container.clientWidth || 800,
    height: container.clientHeight || 600,
    circular: {
      radius: 200,
      startAngle: 0,
      endAngle: 2 * Math.PI
    }
  });
}

/**
 * Update a visualization (example of dynamic updates)
 * 
 * @param {Object} diagramController - Diagram controller from generateDiagram
 */
export function updateVisualization(diagramController) {
  // Add a new entity
  const newEntity = new VisualEntity({
    id: 'entity5',
    label: 'Category',
    type: 'table',
    properties: [
      { name: 'id', type: 'integer', isPrimary: true },
      { name: 'name', type: 'string', isRequired: true },
      { name: 'description', type: 'string' }
    ]
  });
  
  // Add a new relationship
  const newRelationship = new VisualRelationship({
    id: 'rel4',
    source: 'entity3',
    target: 'entity5',
    type: 'manyToOne',
    label: 'belongs to',
    sourceCardinality: '*',
    targetCardinality: '1'
  });
  
  // Update the diagram with new entities and relationships
  diagramController.update({
    schemas: [newEntity],
    relationships: [newRelationship]
  });
}
