/**
 * Visual Entity Model
 * 
 * Represents an entity in the ER diagram visualization
 * 
 * @module visualization/models/visual-entity
 */

/**
 * Represents a visual entity in the diagram
 */
export class VisualEntity {
  /**
   * Create a new VisualEntity
   * 
   * @param {Object} config - Configuration options
   * @param {string} config.id - Unique identifier
   * @param {string} config.label - Display label
   * @param {string} config.type - Entity type (table, view, etc.)
   * @param {Array<Object>} config.properties - Entity properties/fields
   * @param {Object} config.position - Position coordinates {x, y}
   * @param {Object} config.dimensions - Size dimensions {width, height}
   * @param {Object} config.metadata - Additional metadata
   */
  constructor({
    id,
    label,
    type = 'table',
    properties = [],
    position = { x: 0, y: 0 },
    dimensions = { width: 200, height: 150 },
    metadata = {}
  } = {}) {
    if (!id) {
      throw new Error('Entity id is required');
    }

    this.id = id;
    this.label = label || id;
    this.type = type;
    this.properties = properties;
    this.position = position;
    this.dimensions = dimensions;
    this.metadata = metadata;
    this.selected = false;
    this.highlighted = false;
    this.visible = true;
    this.expanded = true;
  }

  /**
   * Clone this entity
   * 
   * @returns {VisualEntity} A new entity with the same properties
   */
  clone() {
    return new VisualEntity({
      id: this.id,
      label: this.label,
      type: this.type,
      properties: JSON.parse(JSON.stringify(this.properties)),
      position: { ...this.position },
      dimensions: { ...this.dimensions },
      metadata: { ...this.metadata }
    });
  }

  /**
   * Set entity position
   * 
   * @param {number} x - X coordinate
   * @param {number} y - Y coordinate
   * @returns {VisualEntity} - This entity (for chaining)
   */
  setPosition(x, y) {
    this.position = { x, y };
    return this;
  }

  /**
   * Add a property/field to the entity
   * 
   * @param {Object} property - Property to add
   * @param {string} property.name - Property name
   * @param {string} property.type - Property type
   * @param {boolean} property.isPrimary - Whether it's a primary key
   * @param {boolean} property.isRequired - Whether it's required
   * @returns {VisualEntity} - This entity (for chaining)
   */
  addProperty(property) {
    this.properties.push(property);
    return this;
  }

  /**
   * Toggle selection state
   * 
   * @param {boolean} [selected] - Selected state or toggle if not provided
   * @returns {VisualEntity} - This entity (for chaining)
   */
  toggleSelected(selected) {
    this.selected = selected === undefined ? !this.selected : selected;
    return this;
  }

  /**
   * Toggle highlight state
   * 
   * @param {boolean} [highlighted] - Highlighted state or toggle if not provided
   * @returns {VisualEntity} - This entity (for chaining)
   */
  toggleHighlighted(highlighted) {
    this.highlighted = highlighted === undefined ? !this.highlighted : highlighted;
    return this;
  }

  /**
   * Toggle visibility
   * 
   * @param {boolean} [visible] - Visible state or toggle if not provided
   * @returns {VisualEntity} - This entity (for chaining)
   */
  toggleVisibility(visible) {
    this.visible = visible === undefined ? !this.visible : visible;
    return this;
  }

  /**
   * Toggle expanded state
   * 
   * @param {boolean} [expanded] - Expanded state or toggle if not provided
   * @returns {VisualEntity} - This entity (for chaining)
   */
  toggleExpanded(expanded) {
    this.expanded = expanded === undefined ? !this.expanded : expanded;
    return this;
  }
}
