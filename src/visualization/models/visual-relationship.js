/**
 * Visual Relationship Model
 * 
 * Represents a relationship between entities in the ER diagram visualization
 * 
 * @module visualization/models/visual-relationship
 */

/**
 * Represents a visual relationship in the diagram
 */
export class VisualRelationship {
  /**
   * Create a new VisualRelationship
   * 
   * @param {Object} config - Configuration options
   * @param {string} config.id - Unique identifier
   * @param {string} config.source - Source entity ID
   * @param {string} config.target - Target entity ID
   * @param {string} config.label - Display label
   * @param {string} config.type - Relationship type (association, composition, etc.)
   * @param {string} config.sourceCardinality - Cardinality at the source end
   * @param {string} config.targetCardinality - Cardinality at the target end
   * @param {number} config.confidence - Confidence score (0-1) for detected relationships
   * @param {Array<Object>} config.path - Path points for custom routing
   * @param {Object} config.metadata - Additional metadata
   */
  constructor({
    id,
    source,
    target,
    label = '',
    type = 'association',
    sourceCardinality,
    targetCardinality,
    confidence = 1.0,
    path = [],
    metadata = {}
  } = {}) {
    if (!id) {
      throw new Error('Relationship id is required');
    }
    if (!source) {
      throw new Error('Source entity id is required');
    }
    if (!target) {
      throw new Error('Target entity id is required');
    }

    this.id = id;
    this.source = source;
    this.target = target;
    this.label = label;
    this.type = type;
    this.sourceCardinality = sourceCardinality;
    this.targetCardinality = targetCardinality;
    this.confidence = Math.max(0, Math.min(1, confidence)); // Clamp between 0 and 1
    this.path = path;
    this.metadata = metadata;
    this.selected = false;
    this.highlighted = false;
    this.visible = true;
  }

  /**
   * Clone this relationship
   * 
   * @returns {VisualRelationship} A new relationship with the same properties
   */
  clone() {
    return new VisualRelationship({
      id: this.id,
      source: this.source,
      target: this.target,
      label: this.label,
      type: this.type,
      sourceCardinality: this.sourceCardinality,
      targetCardinality: this.targetCardinality,
      confidence: this.confidence,
      path: [...this.path],
      metadata: { ...this.metadata }
    });
  }

  /**
   * Set custom path for relationship routing
   * 
   * @param {Array<Object>} points - Array of {x, y} points
   * @returns {VisualRelationship} - This relationship (for chaining)
   */
  setPath(points) {
    this.path = points;
    return this;
  }

  /**
   * Toggle selection state
   * 
   * @param {boolean} [selected] - Selected state or toggle if not provided
   * @returns {VisualRelationship} - This relationship (for chaining)
   */
  toggleSelected(selected) {
    this.selected = selected === undefined ? !this.selected : selected;
    return this;
  }

  /**
   * Toggle highlight state
   * 
   * @param {boolean} [highlighted] - Highlighted state or toggle if not provided
   * @returns {VisualRelationship} - This relationship (for chaining)
   */
  toggleHighlighted(highlighted) {
    this.highlighted = highlighted === undefined ? !this.highlighted : highlighted;
    return this;
  }

  /**
   * Toggle visibility
   * 
   * @param {boolean} [visible] - Visible state or toggle if not provided
   * @returns {VisualRelationship} - This relationship (for chaining)
   */
  toggleVisibility(visible) {
    this.visible = visible === undefined ? !this.visible : visible;
    return this;
  }

  /**
   * Get formatted display of the confidence score
   * 
   * @returns {string} Percentage string representation of confidence
   */
  getConfidenceDisplay() {
    return `${Math.round(this.confidence * 100)}%`;
  }

  /**
   * Check if relationship connects two specific entities
   * 
   * @param {string} entityId1 - First entity ID
   * @param {string} entityId2 - Second entity ID
   * @returns {boolean} - True if relationship connects these entities
   */
  connectsEntities(entityId1, entityId2) {
    return (
      (this.source === entityId1 && this.target === entityId2) ||
      (this.source === entityId2 && this.target === entityId1)
    );
  }
}
