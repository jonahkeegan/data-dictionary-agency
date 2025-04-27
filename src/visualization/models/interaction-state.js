/**
 * Interaction State Model
 * 
 * Tracks the current interaction state of the visualization
 * 
 * @module visualization/models/interaction-state
 */

/**
 * Represents the current interaction state of the visualization
 */
export class InteractionState {
  /**
   * Create a new interaction state
   * 
   * @param {Object} config - Configuration options
   * @param {number} config.scale - Current zoom scale
   * @param {Object} config.translate - Current translation {x, y}
   * @param {Array<string>} config.selectedEntityIds - IDs of selected entities
   * @param {Array<string>} config.selectedRelationshipIds - IDs of selected relationships
   * @param {string} config.hoverEntityId - ID of entity being hovered
   * @param {string} config.hoverRelationshipId - ID of relationship being hovered
   * @param {Object} config.dragState - Current drag operation state
   * @param {Object} config.viewportBounds - Visible bounds of the viewport
   */
  constructor({
    scale = 1,
    translate = { x: 0, y: 0 },
    selectedEntityIds = [],
    selectedRelationshipIds = [],
    hoverEntityId = null,
    hoverRelationshipId = null,
    dragState = null,
    viewportBounds = { x: 0, y: 0, width: 800, height: 600 }
  } = {}) {
    this.scale = scale;
    this.translate = translate;
    this.selectedEntityIds = selectedEntityIds;
    this.selectedRelationshipIds = selectedRelationshipIds;
    this.hoverEntityId = hoverEntityId;
    this.hoverRelationshipId = hoverRelationshipId;
    this.dragState = dragState;
    this.viewportBounds = viewportBounds;
    this.interactionMode = 'default'; // default, pan, select, connect, edit
    this.historyStack = [];
    this.historyPosition = -1;
    this.maxHistorySize = 50;
  }

  /**
   * Reset to default state
   * 
   * @returns {InteractionState} - This state (for chaining)
   */
  reset() {
    this.scale = 1;
    this.translate = { x: 0, y: 0 };
    this.selectedEntityIds = [];
    this.selectedRelationshipIds = [];
    this.hoverEntityId = null;
    this.hoverRelationshipId = null;
    this.dragState = null;
    this.interactionMode = 'default';
    return this;
  }

  /**
   * Set zoom scale
   * 
   * @param {number} scale - New zoom scale
   * @param {boolean} [recordHistory=true] - Whether to record this change in history
   * @returns {InteractionState} - This state (for chaining)
   */
  setScale(scale, recordHistory = true) {
    const previousScale = this.scale;
    this.scale = Math.max(0.1, Math.min(5, scale)); // Clamp between 0.1x and 5x
    
    if (recordHistory && previousScale !== this.scale) {
      this.recordHistory();
    }
    
    return this;
  }

  /**
   * Set translation (pan position)
   * 
   * @param {number} x - X translation
   * @param {number} y - Y translation
   * @param {boolean} [recordHistory=true] - Whether to record this change in history
   * @returns {InteractionState} - This state (for chaining)
   */
  setTranslate(x, y, recordHistory = true) {
    const previousTranslate = { ...this.translate };
    this.translate = { x, y };
    
    if (recordHistory && 
       (previousTranslate.x !== this.translate.x || 
        previousTranslate.y !== this.translate.y)) {
      this.recordHistory();
    }
    
    return this;
  }

  /**
   * Set entity selection
   * 
   * @param {Array<string>} entityIds - IDs of selected entities
   * @param {boolean} [recordHistory=true] - Whether to record this change in history
   * @returns {InteractionState} - This state (for chaining)
   */
  setSelectedEntities(entityIds, recordHistory = true) {
    const previousSelection = [...this.selectedEntityIds];
    this.selectedEntityIds = entityIds;
    
    if (recordHistory && JSON.stringify(previousSelection) !== JSON.stringify(this.selectedEntityIds)) {
      this.recordHistory();
    }
    
    return this;
  }

  /**
   * Toggle entity selection
   * 
   * @param {string} entityId - Entity ID to toggle
   * @param {boolean} [append=false] - Whether to add to current selection
   * @param {boolean} [recordHistory=true] - Whether to record this change in history
   * @returns {InteractionState} - This state (for chaining)
   */
  toggleEntitySelection(entityId, append = false, recordHistory = true) {
    const previousSelection = [...this.selectedEntityIds];
    
    const index = this.selectedEntityIds.indexOf(entityId);
    if (index >= 0) {
      // Entity is already selected, deselect it
      this.selectedEntityIds.splice(index, 1);
    } else {
      // Entity is not selected, select it
      if (append) {
        this.selectedEntityIds.push(entityId);
      } else {
        this.selectedEntityIds = [entityId];
      }
    }
    
    if (recordHistory && JSON.stringify(previousSelection) !== JSON.stringify(this.selectedEntityIds)) {
      this.recordHistory();
    }
    
    return this;
  }

  /**
   * Set relationship selection
   * 
   * @param {Array<string>} relationshipIds - IDs of selected relationships
   * @param {boolean} [recordHistory=true] - Whether to record this change in history
   * @returns {InteractionState} - This state (for chaining)
   */
  setSelectedRelationships(relationshipIds, recordHistory = true) {
    const previousSelection = [...this.selectedRelationshipIds];
    this.selectedRelationshipIds = relationshipIds;
    
    if (recordHistory && 
        JSON.stringify(previousSelection) !== JSON.stringify(this.selectedRelationshipIds)) {
      this.recordHistory();
    }
    
    return this;
  }

  /**
   * Set interaction mode
   * 
   * @param {string} mode - Interaction mode ('default', 'pan', 'select', 'connect', 'edit')
   * @returns {InteractionState} - This state (for chaining)
   */
  setInteractionMode(mode) {
    this.interactionMode = mode;
    return this;
  }

  /**
   * Set the viewport bounds
   * 
   * @param {Object} bounds - Viewport bounds {x, y, width, height}
   * @returns {InteractionState} - This state (for chaining)
   */
  setViewportBounds(bounds) {
    this.viewportBounds = bounds;
    return this;
  }

  /**
   * Start a drag operation
   * 
   * @param {string} type - Type of drag ('entity', 'relationship', 'canvas', 'select')
   * @param {Object} startPosition - Starting position {x, y}
   * @param {string} [targetId] - ID of the target being dragged
   * @returns {InteractionState} - This state (for chaining)
   */
  startDrag(type, startPosition, targetId = null) {
    this.dragState = {
      type,
      startPosition: { ...startPosition },
      currentPosition: { ...startPosition },
      targetId,
      startTime: Date.now()
    };
    return this;
  }

  /**
   * Update drag operation
   * 
   * @param {Object} currentPosition - Current position {x, y}
   * @returns {InteractionState} - This state (for chaining)
   */
  updateDrag(currentPosition) {
    if (this.dragState) {
      this.dragState.currentPosition = { ...currentPosition };
      this.dragState.delta = {
        x: currentPosition.x - this.dragState.startPosition.x,
        y: currentPosition.y - this.dragState.startPosition.y
      };
    }
    return this;
  }

  /**
   * End drag operation
   * 
   * @returns {Object} - Final drag state
   */
  endDrag() {
    const finalDragState = this.dragState;
    this.dragState = null;
    
    if (finalDragState) {
      this.recordHistory();
    }
    
    return finalDragState;
  }

  /**
   * Record current state to history stack
   * 
   * @private
   */
  recordHistory() {
    // Create a snapshot of the current state
    const snapshot = {
      scale: this.scale,
      translate: { ...this.translate },
      selectedEntityIds: [...this.selectedEntityIds],
      selectedRelationshipIds: [...this.selectedRelationshipIds]
    };
    
    // If we're not at the end of the history stack, remove all states after current position
    if (this.historyPosition < this.historyStack.length - 1) {
      this.historyStack = this.historyStack.slice(0, this.historyPosition + 1);
    }
    
    // Add new state to history
    this.historyStack.push(snapshot);
    
    // Enforce maximum history size
    if (this.historyStack.length > this.maxHistorySize) {
      this.historyStack.shift();
    }
    
    // Update position
    this.historyPosition = this.historyStack.length - 1;
  }

  /**
   * Undo the last state change
   * 
   * @returns {boolean} - Whether undo was successful
   */
  undo() {
    if (this.historyPosition <= 0) {
      return false;
    }
    
    this.historyPosition--;
    this.applyHistoryState(this.historyStack[this.historyPosition]);
    return true;
  }

  /**
   * Redo the last undone state change
   * 
   * @returns {boolean} - Whether redo was successful
   */
  redo() {
    if (this.historyPosition >= this.historyStack.length - 1) {
      return false;
    }
    
    this.historyPosition++;
    this.applyHistoryState(this.historyStack[this.historyPosition]);
    return true;
  }

  /**
   * Apply a history state
   * 
   * @private
   * @param {Object} state - History state to apply
   */
  applyHistoryState(state) {
    this.scale = state.scale;
    this.translate = { ...state.translate };
    this.selectedEntityIds = [...state.selectedEntityIds];
    this.selectedRelationshipIds = [...state.selectedRelationshipIds];
  }

  /**
   * Clone this interaction state
   * 
   * @returns {InteractionState} - A new interaction state with the same properties
   */
  clone() {
    return new InteractionState({
      scale: this.scale,
      translate: { ...this.translate },
      selectedEntityIds: [...this.selectedEntityIds],
      selectedRelationshipIds: [...this.selectedRelationshipIds],
      hoverEntityId: this.hoverEntityId,
      hoverRelationshipId: this.hoverRelationshipId,
      dragState: this.dragState ? { ...this.dragState } : null,
      viewportBounds: { ...this.viewportBounds }
    });
  }
}
