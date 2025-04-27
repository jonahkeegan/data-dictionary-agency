/**
 * Visualization API
 * 
 * Main entry point for visualization generation. Orchestrates the visualization process
 * by coordinating data fetching, rendering, and layout calculation.
 * 
 * @module visualization/api
 */

import { RendererFactory } from '../renderers/renderer-factory';
import { LayoutFactory } from '../layouts/layout-factory';
import { VisualEntity, VisualRelationship } from '../models';

/**
 * Main API for generating and managing visualizations
 */
export class VisualizationAPI {
  /**
   * Create a new Visualization API instance
   * @param {Object} options - Configuration options
   */
  constructor(options = {}) {
    this.options = {
      defaultLayout: 'force-directed',
      defaultWidth: 800,
      defaultHeight: 600,
      ...options
    };
    this.rendererFactory = new RendererFactory();
    this.layoutFactory = new LayoutFactory();
    this.diagrams = new Map();
  }

  /**
   * Generate an ER diagram for the specified schemas
   * 
   * @param {HTMLElement} container - DOM element to render the diagram into
   * @param {Array<Object>} schemas - Schema data objects
   * @param {Array<Object>} relationships - Relationship data objects
   * @param {Object} options - Visualization options
   * @returns {Promise<Object>} - Diagram controller
   */
  async generateDiagram(container, schemas, relationships, options = {}) {
    if (!container) {
      throw new Error('Container element is required');
    }

    // Create combined options from defaults and provided options
    const visualOptions = {
      ...this.options,
      ...options,
      width: options.width || this.options.defaultWidth,
      height: options.height || this.options.defaultHeight,
      layout: options.layout || this.options.defaultLayout
    };

    // Transform data into visualization format
    const visualData = this.transformData(schemas, relationships);

    // Create renderer
    const renderer = this.rendererFactory.createRenderer(
      options.renderer || 'd3',
      visualOptions
    );

    // Calculate layout
    const layout = this.layoutFactory.createLayout(visualOptions.layout);
    const positionedData = await layout.calculatePositions(
      visualData.entities,
      visualData.relationships,
      visualOptions
    );

    // Render diagram
    const diagramController = await renderer.render(container, positionedData, visualOptions);

    // Store reference to the diagram
    const diagramId = diagramController.diagramId;
    this.diagrams.set(diagramId, {
      controller: diagramController,
      options: visualOptions,
      container,
      schemas,
      relationships
    });

    return {
      diagramId,
      update: (changes) => this.updateDiagram(diagramId, changes),
      destroy: () => this.destroyDiagram(diagramId)
    };
  }

  /**
   * Update an existing diagram with changes
   * 
   * @param {string} diagramId - ID of the diagram to update
   * @param {Object} changes - Changes to apply
   * @returns {Promise<void>}
   */
  async updateDiagram(diagramId, changes) {
    const diagram = this.diagrams.get(diagramId);
    if (!diagram) {
      throw new Error(`Diagram with ID ${diagramId} not found`);
    }

    // Apply changes
    if (changes.schemas) {
      diagram.schemas = changes.schemas;
    }

    if (changes.relationships) {
      diagram.relationships = changes.relationships;
    }

    if (changes.options) {
      diagram.options = {
        ...diagram.options,
        ...changes.options
      };
    }

    // Transform data
    const visualData = this.transformData(diagram.schemas, diagram.relationships);

    // Calculate layout if needed
    if (changes.schemas || changes.relationships || changes.options?.layout) {
      const layout = this.layoutFactory.createLayout(diagram.options.layout);
      const positionedData = await layout.calculatePositions(
        visualData.entities,
        visualData.relationships,
        diagram.options
      );
      visualData.entities = positionedData.entities;
      visualData.relationships = positionedData.relationships;
    }

    // Update diagram
    await diagram.controller.update(visualData);
  }

  /**
   * Destroy a diagram and clean up resources
   * 
   * @param {string} diagramId - ID of the diagram to destroy
   * @returns {Promise<void>}
   */
  async destroyDiagram(diagramId) {
    const diagram = this.diagrams.get(diagramId);
    if (!diagram) {
      throw new Error(`Diagram with ID ${diagramId} not found`);
    }

    // Destroy the diagram
    await diagram.controller.destroy();

    // Remove from tracked diagrams
    this.diagrams.delete(diagramId);
  }

  /**
   * Transform schema and relationship data into visualization format
   * 
   * @private
   * @param {Array<Object>} schemas - Schema data objects
   * @param {Array<Object>} relationships - Relationship data objects
   * @returns {Object} - Visual data for rendering
   */
  transformData(schemas, relationships) {
    // Transform schemas to visual entities
    const entities = schemas.map(schema => new VisualEntity({
      id: schema.id,
      label: schema.name || schema.id,
      type: schema.type || 'table',
      properties: schema.fields?.map(field => ({
        name: field.name,
        type: field.type,
        isPrimary: field.primaryKey || false,
        isRequired: field.required || false
      })) || [],
      metadata: {
        format: schema.format,
        source: schema.source
      }
    }));

    // Transform relationships to visual relationships
    const visualRelationships = relationships.map(rel => new VisualRelationship({
      id: rel.id || `${rel.source}-${rel.target}`,
      source: rel.source,
      target: rel.target,
      label: rel.label || '',
      type: rel.type || 'association',
      sourceCardinality: rel.sourceCardinality,
      targetCardinality: rel.targetCardinality,
      confidence: rel.confidence || 1,
      metadata: rel.metadata || {}
    }));

    return {
      entities,
      relationships: visualRelationships
    };
  }
}
