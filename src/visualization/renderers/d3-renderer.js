/**
 * D3.js Renderer
 * 
 * Renderer implementation using D3.js for visualization.
 * Implements the technical decision #TECH_002.
 * 
 * @module visualization/renderers
 */

import * as d3 from 'd3';
import { v4 as uuidv4 } from 'uuid';
import { BaseRenderer } from './base-renderer';

/**
 * D3.js-based renderer implementation
 */
export class D3Renderer extends BaseRenderer {
  /**
   * Create a new D3Renderer instance
   * @param {Object} options - Renderer configuration options
   */
  constructor(options = {}) {
    super(options);
    
    this.options = {
      // Visual styling
      fontFamily: 'Arial, sans-serif',
      entityFill: '#f5f5f5',
      entityStroke: '#333333',
      relationshipStroke: '#666666',
      selectedFill: '#e1f5fe',
      selectedStroke: '#0277bd',
      headerColors: {
        table: '#4caf50',
        view: '#2196f3',
        api: '#ff9800',
        default: '#9e9e9e'
      },
      
      // Dimensions
      cornerRadius: 5,
      padding: 10,
      
      // Zoom configuration
      minZoom: 0.1,
      maxZoom: 4,
      
      ...this.options
    };
    
    // Generate a unique ID for this renderer instance
    this.diagramId = uuidv4();
    
    // D3.js elements
    this.svg = null;
    this.defs = null;
    this.zoom = null;
    this.entityGroup = null;
    this.relationshipGroup = null;
    
    // Track rendered elements
    this.entities = new Map();
    this.relationships = new Map();
    
    // Track selected elements
    this.selectedElements = {
      entities: new Set(),
      relationships: new Set()
    };
    
    // Reference to event bus (if provided)
    this.eventBus = options.eventBus;
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
    if (!container) {
      throw new Error('Container element is required');
    }

    // Create combined options from defaults and provided options
    const renderOptions = {
      ...this.options,
      ...options
    };
    
    this.container = container;
    this.options = renderOptions;
    
    // Create SVG container
    this.createSvgContainer();
    
    // Set up zoom behavior
    this.setupZoom();
    
    // Create entity and relationship groups
    this.createGroups();
    
    // Create arrow markers for relationships
    this.createArrowMarkers();
    
    // Render entities and relationships
    await this.renderEntities(data.entities);
    await this.renderRelationships(data.relationships);
    
    // Set up event handlers
    this.setupEventHandlers();
    
    // Return a controller for the rendered diagram
    return {
      diagramId: this.diagramId,
      update: (newData) => this.update(newData),
      destroy: () => this.destroy(),
      select: (selectionData) => this.select(selectionData),
      getInfo: () => this.getInfo()
    };
  }

  /**
   * Update an existing visualization with new data
   * 
   * @param {Object} data - Updated visualization data
   * @returns {Promise<void>}
   */
  async update(data) {
    if (!this.svg) {
      throw new Error('Cannot update: visualization not rendered');
    }
    
    if (data.entities) {
      await this.renderEntities(data.entities);
    }
    
    if (data.relationships) {
      await this.renderRelationships(data.relationships);
    }
  }

  /**
   * Destroy the visualization and clean up resources
   * 
   * @returns {Promise<void>}
   */
  async destroy() {
    if (this.svg) {
      // Remove event listeners
      this.removeEventHandlers();
      
      // Remove the SVG element
      d3.select(this.container).selectAll('svg').remove();
      
      // Clear data references
      this.entities.clear();
      this.relationships.clear();
      this.selectedElements.entities.clear();
      this.selectedElements.relationships.clear();
      
      // Clear DOM references
      this.svg = null;
      this.defs = null;
      this.zoom = null;
      this.entityGroup = null;
      this.relationshipGroup = null;
      
      return true;
    }
    
    return false;
  }

  /**
   * Create the SVG container
   * 
   * @private
   */
  createSvgContainer() {
    // Clear any existing content
    d3.select(this.container).selectAll('*').remove();
    
    // Create SVG element
    this.svg = d3.select(this.container)
      .append('svg')
      .attr('width', this.options.width)
      .attr('height', this.options.height)
      .attr('class', 'dda-visualization')
      .style('font-family', this.options.fontFamily);
    
    // Create defs section for markers, etc.
    this.defs = this.svg.append('defs');
  }

  /**
   * Set up zoom behavior
   * 
   * @private
   */
  setupZoom() {
    // Create zoom behavior
    this.zoom = d3.zoom()
      .scaleExtent([this.options.minZoom, this.options.maxZoom])
      .on('zoom', (event) => {
        // Apply zoom transform
        this.entityGroup.attr('transform', event.transform);
        this.relationshipGroup.attr('transform', event.transform);
        
        // Publish zoom event
        if (this.eventBus) {
          this.eventBus.publish('interaction.zoom', {
            scale: event.transform.k,
            point: [event.transform.x, event.transform.y]
          });
        }
      });
    
    // Apply zoom to SVG
    this.svg.call(this.zoom);
  }

  /**
   * Create groups for entities and relationships
   * 
   * @private
   */
  createGroups() {
    // Group for relationships (drawn first, below entities)
    this.relationshipGroup = this.svg.append('g')
      .attr('class', 'relationships');
    
    // Group for entities (drawn on top)
    this.entityGroup = this.svg.append('g')
      .attr('class', 'entities');
  }

  /**
   * Create arrow markers for relationships
   * 
   * @private
   */
  createArrowMarkers() {
    // Create marker for standard arrows
    this.defs.append('marker')
      .attr('id', `arrow-${this.diagramId}`)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 8)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', this.options.relationshipStroke);
    
    // Create marker for 'one' cardinality
    this.defs.append('marker')
      .attr('id', `one-${this.diagramId}`)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 8)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L0,5')
      .attr('stroke', this.options.relationshipStroke)
      .attr('stroke-width', 1.5);
    
    // Create marker for 'many' cardinality
    this.defs.append('marker')
      .attr('id', `many-${this.diagramId}`)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 8)
      .attr('refY', 0)
      .attr('markerWidth', 8)
      .attr('markerHeight', 8)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5L0,-5')
      .attr('fill', this.options.relationshipStroke);
  }

  /**
   * Render entities
   * 
   * @private
   * @param {Array} entities - Entity data to render
   */
  async renderEntities(entities) {
    if (!Array.isArray(entities)) {
      throw new Error('Entities must be an array');
    }
    
    // Clear existing entities if re-rendering
    this.entityGroup.selectAll('*').remove();
    this.entities.clear();
    
    // Create entity groups
    const entitySelection = this.entityGroup
      .selectAll('.entity')
      .data(entities, d => d.id)
      .enter()
      .append('g')
      .attr('class', 'entity')
      .attr('id', d => `entity-${d.id}`)
      .attr('transform', d => `translate(${d.x || 0}, ${d.y || 0})`)
      .call(d3.drag()
        .on('start', this.onDragStart.bind(this))
        .on('drag', this.onDrag.bind(this))
        .on('end', this.onDragEnd.bind(this)));
    
    // Create entity rectangles (body)
    entitySelection
      .append('rect')
      .attr('class', 'entity-body')
      .attr('rx', this.options.cornerRadius)
      .attr('ry', this.options.cornerRadius)
      .attr('fill', this.options.entityFill)
      .attr('stroke', this.options.entityStroke)
      .attr('stroke-width', 1.5);
    
    // Create entity headers
    entitySelection
      .append('rect')
      .attr('class', 'entity-header')
      .attr('rx', this.options.cornerRadius)
      .attr('ry', this.options.cornerRadius)
      .attr('fill', d => this.getEntityHeaderColor(d))
      .attr('stroke', this.options.entityStroke)
      .attr('stroke-width', 1.5);
    
    // Create entity titles
    entitySelection
      .append('text')
      .attr('class', 'entity-title')
      .attr('x', this.options.padding)
      .attr('y', this.options.padding * 2)
      .attr('fill', 'white')
      .attr('font-weight', 'bold')
      .text(d => d.label);
    
    // Create property groups
    const propertyGroups = entitySelection
      .append('g')
      .attr('class', 'properties')
      .attr('transform', `translate(0, ${this.options.padding * 3})`);
    
    // Render properties for each entity
    entities.forEach(entity => {
      this.renderEntityProperties(
        d3.select(`#entity-${entity.id} .properties`),
        entity
      );
    });
    
    // Adjust entity dimensions based on content
    entitySelection.each((d, i, nodes) => {
      const node = d3.select(nodes[i]);
      const properties = node.select('.properties').node();
      const titleWidth = node.select('.entity-title').node().getBBox().width;
      
      // Calculate width based on content
      const width = Math.max(
        titleWidth + (this.options.padding * 2),
        properties ? properties.getBBox().width : 0
      );
      
      // Calculate height
      const headerHeight = this.options.padding * 2.5;
      const propertyHeight = properties ? properties.getBBox().height : 0;
      const height = headerHeight + propertyHeight + this.options.padding;
      
      // Update entity rectangles
      node.select('.entity-body')
        .attr('width', width)
        .attr('height', height);
      
      node.select('.entity-header')
        .attr('width', width)
        .attr('height', headerHeight);
      
      // Store dimensions for relationship calculations
      d.width = width;
      d.height = height;
      
      // Store entity reference
      this.entities.set(d.id, {
        entity: d,
        element: nodes[i],
        dimensions: { width, height }
      });
    });
    
    // Setup entity event handlers
    entitySelection
      .on('click', this.onEntityClick.bind(this))
      .on('dblclick', this.onEntityDoubleClick.bind(this));
  }

  /**
   * Render properties for an entity
   * 
   * @private
   * @param {d3.Selection} propertyGroup - D3 selection for the property group
   * @param {Object} entity - Entity data
   */
  renderEntityProperties(propertyGroup, entity) {
    if (!entity.properties || !Array.isArray(entity.properties)) {
      return;
    }
    
    const properties = propertyGroup
      .selectAll('.property')
      .data(entity.properties)
      .enter()
      .append('g')
      .attr('class', 'property')
      .attr('transform', (d, i) => `translate(0, ${i * 20})`);
    
    // Property name
    properties
      .append('text')
      .attr('class', 'property-name')
      .attr('x', this.options.padding)
      .attr('y', 15)
      .attr('font-weight', d => d.isPrimary ? 'bold' : 'normal')
      .text(d => d.name);
    
    // Property type
    properties
      .append('text')
      .attr('class', 'property-type')
      .attr('x', this.options.padding + 120)
      .attr('y', 15)
      .attr('fill', '#666')
      .text(d => d.type || '');
    
    // Primary key indicator
    properties
      .filter(d => d.isPrimary)
      .append('text')
      .attr('class', 'primary-key')
      .attr('x', this.options.padding - 15)
      .attr('y', 15)
      .attr('fill', '#F44336')
      .text('🔑');
  }

  /**
   * Render relationships
   * 
   * @private
   * @param {Array} relationships - Relationship data to render
   */
  async renderRelationships(relationships) {
    if (!Array.isArray(relationships)) {
      throw new Error('Relationships must be an array');
    }
    
    // Clear existing relationships if re-rendering
    this.relationshipGroup.selectAll('*').remove();
    this.relationships.clear();
    
    // Create relationship groups
    const relationshipSelection = this.relationshipGroup
      .selectAll('.relationship')
      .data(relationships, d => d.id)
      .enter()
      .append('g')
      .attr('class', 'relationship')
      .attr('id', d => `relationship-${d.id}`);
    
    // Process each relationship
    relationships.forEach(relationship => {
      this.renderRelationship(relationship);
    });
    
    // Setup relationship event handlers
    relationshipSelection
      .on('click', this.onRelationshipClick.bind(this))
      .on('dblclick', this.onRelationshipDoubleClick.bind(this));
  }

  /**
   * Render a single relationship
   * 
   * @private
   * @param {Object} relationship - Relationship data
   */
  renderRelationship(relationship) {
    // Get the source and target entities
    const sourceEntity = this.entities.get(relationship.source);
    const targetEntity = this.entities.get(relationship.target);
    
    // Skip if either entity is missing
    if (!sourceEntity || !targetEntity) {
      console.warn(`Cannot render relationship ${relationship.id}: missing entities`);
      return;
    }
    
    // Calculate connection points
    const points = this.calculateConnectionPoints(sourceEntity, targetEntity);
    
    // Create relationship group
    const relationshipGroup = this.relationshipGroup
      .append('g')
      .attr('class', 'relationship')
      .attr('id', `relationship-${relationship.id}`);
    
    // Draw the relationship line
    const path = relationshipGroup
      .append('path')
      .attr('class', 'relationship-path')
      .attr('d', this.createRelationshipPath(points))
      .attr('fill', 'none')
      .attr('stroke', this.options.relationshipStroke)
      .attr('stroke-width', 1.5)
      .attr('marker-end', `url(#arrow-${this.diagramId})`);
    
    // Add cardinality markers
    if (relationship.sourceCardinality === '1') {
      path.attr('marker-start', `url(#one-${this.diagramId})`);
    } else if (relationship.sourceCardinality === 'many' || relationship.sourceCardinality === '*') {
      path.attr('marker-start', `url(#many-${this.diagramId})`);
    }
    
    // Add relationship label if provided
    if (relationship.label) {
      const midpoint = this.getMidpoint(points);
      
      relationshipGroup
        .append('text')
        .attr('class', 'relationship-label')
        .attr('x', midpoint.x)
        .attr('y', midpoint.y - 10)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'central')
        .attr('fill', '#333')
        .text(relationship.label);
    }
    
    // Store relationship reference
    this.relationships.set(relationship.id, {
      relationship,
      element: relationshipGroup.node(),
      points
    });
  }

  /**
   * Calculate connection points between two entities
   * 
   * @private
   * @param {Object} sourceEntity - Source entity data
   * @param {Object} targetEntity - Target entity data
   * @returns {Object} - Connection points
   */
  calculateConnectionPoints(sourceEntity, targetEntity) {
    const source = sourceEntity.entity;
    const target = targetEntity.entity;
    
    // Calculate centers
    const sourceCenter = {
      x: source.x + (source.width / 2),
      y: source.y + (source.height / 2)
    };
    
    const targetCenter = {
      x: target.x + (target.width / 2),
      y: target.y + (target.height / 2)
    };
    
    // Calculate angle between centers
    const angle = Math.atan2(
      targetCenter.y - sourceCenter.y,
      targetCenter.x - sourceCenter.x
    );
    
    // Calculate intersection points with entity rectangles
    const sourcePoint = this.getIntersectionPoint(
      sourceCenter, source.width, source.height, angle
    );
    
    const targetPoint = this.getIntersectionPoint(
      targetCenter, target.width, target.height, angle + Math.PI
    );
    
    return {
      source: {
        x: source.x + sourcePoint.x,
        y: source.y + sourcePoint.y
      },
      target: {
        x: target.x + targetPoint.x,
        y: target.y + targetPoint.y
      }
    };
  }

  /**
   * Get the intersection point of a line from the center of a rectangle
   * 
   * @private
   * @param {Object} center - Center point of the rectangle
   * @param {number} width - Width of the rectangle
   * @param {number} height - Height of the rectangle
   * @param {number} angle - Angle of the line in radians
   * @returns {Object} - Intersection point relative to the rectangle's top-left corner
   */
  getIntersectionPoint(center, width, height, angle) {
    const w = width / 2;
    const h = height / 2;
    
    // Calculate intersection with the rectangle
    let x, y;
    
    const tanAngle = Math.tan(angle);
    
    if (Math.abs(tanAngle) < h / w) {
      // Intersects with left or right edge
      x = Math.sign(Math.cos(angle)) * w;
      y = tanAngle * x;
    } else {
      // Intersects with top or bottom edge
      y = Math.sign(Math.sin(angle)) * h;
      x = y / tanAngle;
    }
    
    return {
      x: w + x,
      y: h + y
    };
  }

  /**
   * Create path data for a relationship
   * 
   * @private
   * @param {Object} points - Connection points
   * @returns {string} - SVG path data
   */
  createRelationshipPath(points) {
    return `M${points.source.x},${points.source.y} L${points.target.x},${points.target.y}`;
  }

  /**
   * Get midpoint of a line
   * 
   * @private
   * @param {Object} points - Line points
   * @returns {Object} - Midpoint coordinates
   */
  getMidpoint(points) {
    return {
      x: (points.source.x + points.target.x) / 2,
      y: (points.source.y + points.target.y) / 2
    };
  }

  /**
   * Get header color for an entity based on its type
   * 
   * @private
   * @param {Object} entity - Entity data
   * @returns {string} - Color code
   */
  getEntityHeaderColor(entity) {
    const type = entity.type || 'default';
    return this.options.headerColors[type] || this.options.headerColors.default;
  }

  /**
   * Set up event handlers
   * 
   * @private
   */
  setupEventHandlers() {
    // Set up keyboard event handlers
    d3.select(window).on(`keydown.${this.diagramId}`, this.onKeyDown.bind(this));
    
    // Set up mouse event handlers for the SVG
    this.svg.on('click', this.onBackgroundClick.bind(this));
  }

  /**
   * Remove event handlers
   * 
   * @private
   */
  removeEventHandlers() {
    // Remove keyboard event handlers
    d3.select(window).on(`keydown.${this.diagramId}`, null);
    
    // Remove mouse event handlers
    if (this.svg) {
      this.svg.on('click', null);
    }
  }

  /**
   * Handle entity drag start
   * 
   * @private
   * @param {Event} event - D3 drag event
   */
  onDragStart(event, d) {
    if (this.eventBus) {
      this.eventBus.publish('interaction.dragStart', {
        entity: d,
        position: [event.x, event.y]
      });
    }
  }

  /**
   * Handle entity drag
   * 
   * @private
   * @param {Event} event - D3 drag event
   */
  onDrag(event, d) {
    // Update entity position
    d.x = event.x;
    d.y = event.y;
    
    // Update entity element
    d3.select(event.sourceEvent.target.closest('.entity'))
      .attr('transform', `translate(${d.x}, ${d.y})`);
    
    // Update connected relationships
    this.updateRelationshipsForEntity(d.id);
    
    if (this.eventBus) {
      this.eventBus.publish('interaction.drag', {
        entity: d,
        position: [event.x, event.y]
      });
    }
  }

  /**
   * Handle entity drag end
   * 
   * @private
   * @param {Event} event - D3 drag event
   */
  onDragEnd(event, d) {
    if (this.eventBus) {
      this.eventBus.publish('interaction.dragEnd', {
        entity: d,
        position: [event.x, event.y]
      });
    }
  }

  /**
   * Update relationships for an entity
   * 
   * @private
   * @param {string} entityId - Entity ID
   */
  updateRelationshipsForEntity(entityId) {
    // Find relationships connected to this entity
    const connectedRelationships = Array.from(this.relationships.values())
      .filter(r => r.relationship.source === entityId || r.relationship.target === entityId);
    
    // Update each relationship
    connectedRelationships.forEach(relationshipData => {
      const relationship = relationshipData.relationship;
      
      // Get the source and target entities
      const sourceEntity = this.entities.get(relationship.source);
      const targetEntity = this.entities.get(relationship.target);
      
      if (sourceEntity && targetEntity) {
        // Calculate new connection points
        const points = this.calculateConnectionPoints(sourceEntity, targetEntity);
        
        // Update the path
        d3.select(`#relationship-${relationship.id} path`)
          .attr('d', this.createRelationshipPath(points));
        
        // Update label position if present
        const label = d3.select(`#relationship-${relationship.id} text`);
        if (!label.empty()) {
          const midpoint = this.getMidpoint(points);
          label
            .attr('x', midpoint.x)
            .attr('y', midpoint.y - 10);
        }
        
        // Update stored points
        relationshipData.points = points;
      }
    });
  }

  /**
   * Handle entity click
   * 
   * @private
   * @param {Event} event - Click event
   */
  onEntityClick(event, d) {
    // Prevent event propagation
    event.stopPropagation();
    
    // Toggle selection state
    const isSelected = this.selectedElements.entities.has(d.id);
    
    if (event.ctrlKey || event.metaKey) {
      // Multi-select when Ctrl/Cmd is pressed
      if (isSelected) {
        this.selectedElements.entities.delete(d.id);
      } else {
        this.selectedElements.entities.add(d.id);
      }
    } else {
      // Single select otherwise
      this.selectedElements.entities.clear();
      this.selectedElements.relationships.clear();
      this.selectedElements.entities.add(d.id);
    }
    
    // Update visual appearance
    this.updateSelectionVisuals();
    
    // Publish event
    if (this.eventBus) {
      this.eventBus.publish('interaction.entityClick', {
        entity: d,
        selected: !isSelected,
        selectedEntities: Array.from(this.selectedElements.entities),
        point: [event.x, event.y]
      });
    }
  }

  /**
   * Handle entity double-click
   * 
   * @private
   * @param {Event} event - Double-click event
   */
  onEntityDoubleClick(event, d) {
    // Prevent event propagation
    event.stopPropagation();
    
    // Publish event
    if (this.eventBus) {
      this.eventBus.publish('interaction.entityDoubleClick', {
        entity: d,
        point: [event.x, event.y]
      });
    }
  }

  /**
   * Handle relationship click
   * 
   * @private
   * @param {Event} event - Click event
   */
  onRelationshipClick(event, d) {
    // Prevent event propagation
    event.stopPropagation();
    
    // Toggle selection state
    const isSelected = this.selectedElements.relationships.has(d.id);
    
    if (event.ctrlKey || event.metaKey) {
      // Multi-select when Ctrl/Cmd is pressed
      if (isSelected) {
        this.selectedElements.relationships.delete(d.id);
      } else {
        this.selectedElements.relationships.add(d.id);
      }
    } else {
      // Single select otherwise
      this.selectedElements.entities.clear();
      this.selectedElements.relationships.clear();
      this.selectedElements.relationships.add(d.id);
    }
    
    // Update visual appearance
    this.updateSelectionVisuals();
    
    // Publish event
    if (this.eventBus) {
      this.eventBus.publish('interaction.relationshipClick', {
        relationship: d,
        selected: !isSelected,
        selectedRelationships: Array.from(this.selectedElements.relationships),
        point: [event.x, event.y]
      });
    }
  }

  /**
   * Handle relationship double-click
   * 
   * @private
   * @param {Event} event - Double-click event
   */
  onRelationshipDoubleClick(event, d) {
    // Prevent event propagation
    event.stopPropagation();
    
    // Publish event
    if (this.eventBus) {
      this.eventBus.publish('interaction.relationshipDoubleClick', {
        relationship: d,
        point: [event.x, event.y]
      });
    }
  }

  /**
   * Handle background click
   * 
   * @private
   * @param {Event} event - Click event
   */
  onBackgroundClick(event) {
    // Only handle direct background clicks
    if (event.target === this.svg.node()) {
      // Clear selection
      const hadSelection = this.selectedElements.entities.size > 0 || 
                         this.selectedElements.relationships.size > 0;
      
      this.selectedElements.entities.clear();
      this.selectedElements.relationships.clear();
      
      // Update visual appearance
      this.updateSelectionVisuals();
      
      // Publish event
      if (this.eventBus && hadSelection) {
        this.eventBus.publish('interaction.selectionCleared', {
          point: [event.x, event.y]
        });
      }
    }
  }

  /**
   * Handle key down
   * 
   * @private
   * @param {Event} event - Key down event
   */
  onKeyDown(event) {
    // Handle keyboard shortcuts
    if (event.key === 'Delete' || event.key === 'Backspace') {
      // Delete selected elements
      if (this.selectedElements.entities.size > 0 || 
          this.selectedElements.relationships.size > 0) {
        
        // Publish delete event
        if (this.eventBus) {
          this.eventBus.publish('interaction.deleteSelected', {
            entities: Array.from(this.selectedElements.entities),
            relationships: Array.from(this.selectedElements.relationships)
          });
        }
        
        // Prevent default action
        event.preventDefault();
      }
    }
  }

  /**
   * Update selection visuals
   * 
   * @private
   */
  updateSelectionVisuals() {
    // Update entities
    d3.selectAll('.entity').each((d, i, nodes) => {
      const isSelected = this.selectedElements.entities.has(d.id);
      d3.select(nodes[i])
        .select('.entity-body')
        .attr('fill', isSelected ? this.options.selectedFill : this.options.entityFill)
        .attr('stroke', isSelected ? this.options.selectedStroke : this.options.entityStroke);
    });
    
    // Update relationships
    d3.selectAll('.relationship path').each((d, i, nodes) => {
      const relationship = d3.select(nodes[i].parentNode).datum();
      const isSelected = this.selectedElements.relationships.has(relationship.id);
      d3.select(nodes[i])
        .attr('stroke', isSelected ? this.options.selectedStroke : this.options.relationshipStroke)
        .attr('stroke-width', isSelected ? 2.5 : 1.5);
    });
  }

  /**
   * Select elements programmatically
   * 
   * @param {Object} selectionData - Data for selection
   * @param {Array<string>} selectionData.entities - Entity IDs to select
   * @param {Array<string>} selectionData.relationships - Relationship IDs to select
   * @param {boolean} selectionData.clear - Whether to clear existing selection
   * @returns {boolean} - Whether the selection changed
   */
  select(selectionData) {
    const previousEntityCount = this.selectedElements.entities.size;
    const previousRelationshipCount = this.selectedElements.relationships.size;
    
    if (selectionData.clear) {
      this.selectedElements.entities.clear();
      this.selectedElements.relationships.clear();
    }
    
    if (selectionData.entities) {
      selectionData.entities.forEach(id => {
        this.selectedElements.entities.add(id);
      });
    }
    
    if (selectionData.relationships) {
      selectionData.relationships.forEach(id => {
        this.selectedElements.relationships.add(id);
      });
    }
    
    // Update visual appearance
    this.updateSelectionVisuals();
    
    // Check if selection changed
    const selectionChanged = 
      previousEntityCount !== this.selectedElements.entities.size ||
      previousRelationshipCount !== this.selectedElements.relationships.size;
    
    // Publish event if selection changed
    if (selectionChanged && this.eventBus) {
      this.eventBus.publish('interaction.selectionChanged', {
        entities: Array.from(this.selectedElements.entities),
        relationships: Array.from(this.selectedElements.relationships)
      });
    }
    
    return selectionChanged;
  }
}
