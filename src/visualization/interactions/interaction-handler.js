/**
 * Interaction Handler
 * 
 * Manages user interactions with the visualization
 * 
 * @module visualization/interactions/interaction-handler
 */

import { InteractionState } from '../models/interaction-state';

/**
 * Manages user interactions with the visualization
 */
export class InteractionHandler {
  /**
   * Create a new interaction handler
   * 
   * @param {EventBus} eventBus - Event bus for communication
   * @param {Object} options - Interaction options
   */
  constructor(eventBus, options = {}) {
    this.eventBus = eventBus;
    this.options = {
      enablePan: true,
      enableZoom: true,
      enableSelection: true,
      minZoom: 0.1,
      maxZoom: 5,
      ...options
    };
    
    this.state = new InteractionState();
    this.zoomHandler = null;
    this.dragHandler = null;
    this.initialized = false;
  }

  /**
   * Set up interactions for an SVG container
   * 
   * @param {SVGElement} svg - SVG container element
   * @param {Object} options - Interaction options
   */
  setup(svg, options = {}) {
    this.svg = svg;
    
    // Update options
    this.options = {
      ...this.options,
      ...options
    };
    
    // Set up event handlers
    this.setupEventListeners();
    
    // Mark as initialized
    this.initialized = true;
    
    // Publish initialization complete event
    this.eventBus.publish('interaction.initialized', this);
  }

  /**
   * Set up event listeners
   * 
   * @private
   */
  setupEventListeners() {
    const svg = this.svg;
    
    if (!svg) {
      return;
    }
    
    // Mouse events
    if (this.options.enableZoom) {
      svg.addEventListener('wheel', this.handleWheel.bind(this), { passive: false });
    }
    
    if (this.options.enablePan) {
      svg.addEventListener('mousedown', this.handleMouseDown.bind(this));
      svg.addEventListener('mousemove', this.handleMouseMove.bind(this));
      svg.addEventListener('mouseup', this.handleMouseUp.bind(this));
      svg.addEventListener('mouseleave', this.handleMouseLeave.bind(this));
    }
    
    if (this.options.enableSelection) {
      svg.addEventListener('click', this.handleClick.bind(this));
      svg.addEventListener('dblclick', this.handleDoubleClick.bind(this));
    }
    
    // Touch events
    svg.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
    svg.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
    svg.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });
    
    // Keyboard events
    svg.setAttribute('tabindex', '0'); // Make SVG focusable
    svg.addEventListener('keydown', this.handleKeyDown.bind(this));
  }

  /**
   * Handle mouse wheel event for zooming
   * 
   * @param {WheelEvent} event - Wheel event
   */
  handleWheel(event) {
    if (!this.options.enableZoom) {
      return;
    }
    
    // Prevent default to avoid page scrolling
    event.preventDefault();
    
    // Calculate zoom factor
    const delta = event.deltaY < 0 ? 1.1 : 0.9;
    
    // Get mouse position relative to SVG
    const point = this.getMousePosition(event);
    
    // Update state
    this.zoomAtPoint(delta, point);
    
    // Publish zoom event
    this.eventBus.publish('interaction.zoom', {
      scale: this.state.scale,
      point
    });
  }

  /**
   * Handle mouse down event for panning or selection
   * 
   * @param {MouseEvent} event - Mouse event
   */
  handleMouseDown(event) {
    // Get mouse position
    const point = this.getMousePosition(event);
    
    if (event.button === 0) { // Left button
      if (event.ctrlKey || event.metaKey) {
        // Selection drag
        if (this.options.enableSelection) {
          this.state.startDrag('select', point);
          this.eventBus.publish('interaction.selectionStart', point);
        }
      } else {
        // Pan drag
        if (this.options.enablePan) {
          this.state.startDrag('canvas', point);
          this.eventBus.publish('interaction.panStart', point);
        }
      }
    }
  }

  /**
   * Handle mouse move event for panning or selection
   * 
   * @param {MouseEvent} event - Mouse event
   */
  handleMouseMove(event) {
    // Get mouse position
    const point = this.getMousePosition(event);
    
    // Update hover state
    this.updateHover(point);
    
    // Handle drag operations
    if (this.state.dragState) {
      this.state.updateDrag(point);
      
      const dragState = this.state.dragState;
      
      if (dragState.type === 'canvas') {
        // Pan the view
        const dx = point.x - dragState.startPosition.x;
        const dy = point.y - dragState.startPosition.y;
        
        this.state.setTranslate(
          this.state.translate.x + dx,
          this.state.translate.y + dy
        );
        
        // Reset drag start position to avoid accumulated delta
        dragState.startPosition = point;
        
        // Publish pan event
        this.eventBus.publish('interaction.pan', {
          translate: this.state.translate,
          delta: { x: dx, y: dy }
        });
      } else if (dragState.type === 'select') {
        // Update selection area
        this.updateSelectionArea(dragState.startPosition, point);
        
        // Publish selection update event
        this.eventBus.publish('interaction.selectionUpdate', {
          start: dragState.startPosition,
          current: point
        });
      }
    }
  }

  /**
   * Handle mouse up event to end drag operations
   * 
   * @param {MouseEvent} event - Mouse event
   */
  handleMouseUp(event) {
    // Get mouse position
    const point = this.getMousePosition(event);
    
    // End any ongoing drag operation
    if (this.state.dragState) {
      const dragState = this.state.endDrag();
      
      if (dragState.type === 'canvas') {
        // Publish pan end event
        this.eventBus.publish('interaction.panEnd', {
          translate: this.state.translate
        });
      } else if (dragState.type === 'select') {
        // Finalize selection
        this.finalizeSelection(dragState.startPosition, point, event.ctrlKey || event.metaKey);
        
        // Publish selection end event
        this.eventBus.publish('interaction.selectionEnd', {
          start: dragState.startPosition,
          end: point,
          append: event.ctrlKey || event.metaKey
        });
      }
    }
  }

  /**
   * Handle mouse leave event
   * 
   * @param {MouseEvent} event - Mouse event
   */
  handleMouseLeave(event) {
    // End any ongoing drag operation when mouse leaves the SVG
    if (this.state.dragState) {
      this.state.endDrag();
      
      // Publish drag cancel event
      this.eventBus.publish('interaction.dragCancel', {
        reason: 'mouseleave'
      });
    }
    
    // Clear hover state
    this.clearHover();
  }

  /**
   * Handle click event for selection
   * 
   * @param {MouseEvent} event - Mouse event
   */
  handleClick(event) {
    if (!this.options.enableSelection) {
      return;
    }
    
    // Get mouse position
    const point = this.getMousePosition(event);
    
    // Check if this is part of a drag (should be handled by dragEnd)
    if (this.state.dragState) {
      return;
    }
    
    // Check for entity selection
    const entity = this.findEntityAtPoint(point);
    
    if (entity) {
      const append = event.ctrlKey || event.metaKey;
      
      // Toggle entity selection
      this.toggleEntitySelection(entity.id, append);
      
      // Publish entity click event
      this.eventBus.publish('interaction.entityClick', {
        entity,
        point,
        append
      });
    } else {
      // Click on empty space, clear selection unless modifier key is pressed
      if (!event.ctrlKey && !event.metaKey) {
        this.clearSelection();
      }
      
      // Publish background click event
      this.eventBus.publish('interaction.backgroundClick', {
        point
      });
    }
  }

  /**
   * Handle double click event
   * 
   * @param {MouseEvent} event - Mouse event
   */
  handleDoubleClick(event) {
    // Get mouse position
    const point = this.getMousePosition(event);
    
    // Check for entity double-click
    const entity = this.findEntityAtPoint(point);
    
    if (entity) {
      // Publish entity double-click event
      this.eventBus.publish('interaction.entityDoubleClick', {
        entity,
        point
      });
    } else {
      // Publish background double-click event
      this.eventBus.publish('interaction.backgroundDoubleClick', {
        point
      });
    }
  }

  /**
   * Handle touch start event
   * 
   * @param {TouchEvent} event - Touch event
   */
  handleTouchStart(event) {
    if (event.touches.length === 1) {
      // Single touch - similar to mouse down
      event.preventDefault();
      
      const touch = event.touches[0];
      const point = this.getTouchPosition(touch);
      
      this.state.startDrag('canvas', point);
      this.eventBus.publish('interaction.touchStart', point);
    } else if (event.touches.length === 2) {
      // Pinch to zoom
      event.preventDefault();
      
      const touch1 = event.touches[0];
      const touch2 = event.touches[1];
      
      const point1 = this.getTouchPosition(touch1);
      const point2 = this.getTouchPosition(touch2);
      
      this.state.startDrag('pinch', {
        touch1: point1,
        touch2: point2,
        distance: this.getDistance(point1, point2)
      });
      
      this.eventBus.publish('interaction.pinchStart', {
        center: this.getMidpoint(point1, point2),
        distance: this.getDistance(point1, point2)
      });
    }
  }

  /**
   * Handle touch move event
   * 
   * @param {TouchEvent} event - Touch event
   */
  handleTouchMove(event) {
    if (!this.state.dragState) {
      return;
    }
    
    event.preventDefault();
    
    if (event.touches.length === 1 && this.state.dragState.type === 'canvas') {
      // Single touch move - similar to mouse move for panning
      const touch = event.touches[0];
      const point = this.getTouchPosition(touch);
      
      // Update drag state
      this.state.updateDrag(point);
      
      // Calculate delta
      const dragState = this.state.dragState;
      const dx = point.x - dragState.startPosition.x;
      const dy = point.y - dragState.startPosition.y;
      
      // Pan the view
      this.state.setTranslate(
        this.state.translate.x + dx,
        this.state.translate.y + dy
      );
      
      // Reset drag start position
      dragState.startPosition = point;
      
      // Publish pan event
      this.eventBus.publish('interaction.touchPan', {
        translate: this.state.translate,
        delta: { x: dx, y: dy }
      });
    } else if (event.touches.length === 2 && this.state.dragState.type === 'pinch') {
      // Pinch zoom
      const touch1 = event.touches[0];
      const touch2 = event.touches[1];
      
      const point1 = this.getTouchPosition(touch1);
      const point2 = this.getTouchPosition(touch2);
      
      // Calculate new distance between touch points
      const newDistance = this.getDistance(point1, point2);
      const initialDistance = this.state.dragState.distance;
      
      // Calculate zoom factor based on the change in distance
      const zoomFactor = newDistance / initialDistance;
      
      // Calculate center point of the pinch
      const center = this.getMidpoint(point1, point2);
      
      // Apply zoom
      this.zoomAtPoint(zoomFactor, center);
      
      // Update the stored distance
      this.state.dragState.distance = newDistance;
      this.state.dragState.touch1 = point1;
      this.state.dragState.touch2 = point2;
      
      // Publish pinch event
      this.eventBus.publish('interaction.pinch', {
        center,
        scale: this.state.scale,
        factor: zoomFactor
      });
    }
  }

  /**
   * Handle touch end event
   * 
   * @param {TouchEvent} event - Touch event
   */
  handleTouchEnd(event) {
    if (!this.state.dragState) {
      return;
    }
    
    event.preventDefault();
    
    // End the drag operation
    const dragType = this.state.dragState.type;
    this.state.endDrag();
    
    if (dragType === 'canvas') {
      // Publish touch pan end event
      this.eventBus.publish('interaction.touchPanEnd', {
        translate: this.state.translate
      });
    } else if (dragType === 'pinch') {
      // Publish pinch end event
      this.eventBus.publish('interaction.pinchEnd', {
        scale: this.state.scale
      });
    }
  }

  /**
   * Handle keyboard events
   * 
   * @param {KeyboardEvent} event - Keyboard event
   */
  handleKeyDown(event) {
    // Handle keyboard shortcuts
    switch (event.key) {
      case 'Escape':
        // Cancel drag operations
        if (this.state.dragState) {
          this.state.endDrag();
          this.eventBus.publish('interaction.dragCancel', {
            reason: 'escape'
          });
        }
        break;
      
      case 'Delete':
      case 'Backspace':
        // Delete selected entities
        if (this.state.selectedEntityIds.length > 0) {
          this.eventBus.publish('interaction.deleteSelected', {
            entityIds: [...this.state.selectedEntityIds],
            relationshipIds: [...this.state.selectedRelationshipIds]
          });
        }
        break;
      
      case 'a':
        // Select all entities when Ctrl+A is pressed
        if (event.ctrlKey || event.metaKey) {
          event.preventDefault();
          this.selectAllEntities();
          this.eventBus.publish('interaction.selectAll', {});
        }
        break;
      
      case 'z':
        // Undo when Ctrl+Z is pressed
        if (event.ctrlKey || event.metaKey) {
          event.preventDefault();
          if (this.state.undo()) {
            this.eventBus.publish('interaction.undo', {
              state: { 
                scale: this.state.scale, 
                translate: this.state.translate,
                selectedEntityIds: [...this.state.selectedEntityIds],
                selectedRelationshipIds: [...this.state.selectedRelationshipIds]
              }
            });
          }
        }
        break;
      
      case 'y':
        // Redo when Ctrl+Y is pressed
        if (event.ctrlKey || event.metaKey) {
          event.preventDefault();
          if (this.state.redo()) {
            this.eventBus.publish('interaction.redo', {
              state: { 
                scale: this.state.scale, 
                translate: this.state.translate,
                selectedEntityIds: [...this.state.selectedEntityIds],
                selectedRelationshipIds: [...this.state.selectedRelationshipIds] 
              }
            });
          }
        }
        break;
    }
  }

  /**
   * Get mouse position relative to SVG
   * 
   * @param {MouseEvent} event - Mouse event
   * @returns {Object} - Position {x, y}
   */
  getMousePosition(event) {
    if (!this.svg) {
      return { x: 0, y: 0 };
    }
    
    const ctm = this.svg.getScreenCTM();
    
    if (!ctm) {
      return { x: 0, y: 0 };
    }
    
    return {
      x: (event.clientX - ctm.e) / ctm.a,
      y: (event.clientY - ctm.f) / ctm.d
    };
  }

  /**
   * Get touch position relative to SVG
   * 
   * @param {Touch} touch - Touch point
   * @returns {Object} - Position {x, y}
   */
  getTouchPosition(touch) {
    if (!this.svg) {
      return { x: 0, y: 0 };
    }
    
    const ctm = this.svg.getScreenCTM();
    
    if (!ctm) {
      return { x: 0, y: 0 };
    }
    
    return {
      x: (touch.clientX - ctm.e) / ctm.a,
      y: (touch.clientY - ctm.f) / ctm.d
    };
  }

  /**
   * Calculate distance between two points
   * 
   * @param {Object} point1 - First point {x, y}
   * @param {Object} point2 - Second point {x, y}
   * @returns {number} - Distance
   */
  getDistance(point1, point2) {
    const dx = point2.x - point1.x;
    const dy = point2.y - point1.y;
    return Math.sqrt(dx * dx + dy * dy);
  }

  /**
   * Calculate midpoint between two points
   * 
   * @param {Object} point1 - First point {x, y}
   * @param {Object} point2 - Second point {x, y}
   * @returns {Object} - Midpoint {x, y}
   */
  getMidpoint(point1, point2) {
    return {
      x: (point1.x + point2.x) / 2,
      y: (point1.y + point2.y) / 2
    };
  }

  /**
   * Zoom at a specific point
   * 
   * @param {number} factor - Zoom factor
   * @param {Object} point - Zoom center point {x, y}
   */
  zoomAtPoint(factor, point) {
    // Calculate new scale
    const oldScale = this.state.scale;
    const newScale = Math.max(
      this.options.minZoom,
      Math.min(this.options.maxZoom, oldScale * factor)
    );
    
    // If scale didn't change (limit reached), return
    if (newScale === oldScale) {
      return;
    }
    
    // Calculate new translation to zoom at point
    const scaleFactor = newScale / oldScale;
    
    const dx = point.x - (point.x - this.state.translate.x) * scaleFactor;
    const dy = point.y - (point.y - this.state.translate.y) * scaleFactor;
    
    // Update state
    this.state.setScale(newScale, false);
    this.state.setTranslate(dx, dy);
  }

  /**
   * Find entity at a specific point
   * 
   * @param {Object} point - Point {x, y}
   * @returns {Object|null} - Entity at the point or null
   */
  findEntityAtPoint(point) {
    // This is a placeholder. The actual implementation would be provided
    // by the renderer and needs to account for the current transformation.
    
    // Publish hit test event and expect a response
    let result = null;
    
    this.eventBus.publish('interaction.hitTest', {
      point,
      callback: (entity) => {
        result = entity;
      }
    });
    
    return result;
  }

  /**
   * Update hover state
   * 
   * @param {Object} point - Mouse position {x, y}
   */
  updateHover(point) {
    // Find entity under cursor
    const entity = this.findEntityAtPoint(point);
    
    // Update hover state if it changed
    if (entity && entity.id !== this.state.hoverEntityId) {
      // Clear previous hover
      if (this.state.hoverEntityId) {
        this.eventBus.publish('interaction.entityHoverOut', {
          entityId: this.state.hoverEntityId
        });
      }
      
      // Set new hover
      this.state.hoverEntityId = entity.id;
      
      // Publish hover event
      this.eventBus.publish('interaction.entityHoverIn', {
        entity
      });
    } else if (!entity && this.state.hoverEntityId) {
      // Clear hover when not over any entity
      this.eventBus.publish('interaction.entityHoverOut', {
        entityId: this.state.hoverEntityId
      });
      
      this.state.hoverEntityId = null;
    }
  }

  /**
   * Clear hover state
   */
  clearHover() {
    if (this.state.hoverEntityId) {
      // Publish hover out event
      this.eventBus.publish('interaction.entityHoverOut', {
        entityId: this.state.hoverEntityId
      });
      
      // Clear state
      this.state.hoverEntityId = null;
    }
  }

  /**
   * Toggle entity selection
   * 
   * @param {string} entityId - Entity ID
   * @param {boolean} append - Whether to add to current selection
   */
  toggleEntitySelection(entityId, append) {
    this.state.toggleEntitySelection(entityId, append);
    
    // Publish selection changed event
    this.eventBus.publish('interaction.selectionChanged', {
      entities: [...this.state.selectedEntityIds],
      relationships: [...this.state.selectedRelationshipIds]
    });
  }

  /**
   * Clear selection
   */
  clearSelection() {
    if (this.state.selectedEntityIds.length > 0 || this.state.selectedRelationshipIds.length > 0) {
      // Clear selection
      this.state.setSelectedEntities([]);
      this.state.setSelectedRelationships([]);
      
      // Publish selection changed event
      this.eventBus.publish('interaction.selectionChanged', {
        entities: [],
        relationships: []
      });
    }
  }

  /**
   * Select all entities
   */
  selectAllEntities() {
    // This is a placeholder. The actual implementation needs to know
    // about all entities in the diagram.
    
    // Publish select all event
    this.eventBus.publish('interaction.requestSelectAll', {
      callback: (entityIds, relationshipIds) => {
        // Update selection with all entities
        this.state.setSelectedEntities(entityIds);
        this.state.setSelectedRelationships(relationshipIds);
        
        // Publish selection changed event
        this.eventBus.publish('interaction.selectionChanged', {
          entities: entityIds,
          relationships: relationshipIds
        });
      }
    });
  }

  /**
   * Update selection area during drag
   * 
   * @param {Object} start - Start point {x, y}
   * @param {Object} end - End point {x, y}
   */
  updateSelectionArea(start, end) {
    // Calculate selection rectangle
    const selectionRect = {
      x: Math.min(start.x, end.x),
      y: Math.min(start.y, end.y),
      width: Math.abs(end.x - start.x),
      height: Math.abs(end.y - start.y)
    };
    
    // Publish selection rectangle update event
    this.eventBus.publish('interaction.selectionRect', selectionRect);
  }

  /**
   * Finalize selection after drag
   * 
   * @param {Object} start - Start point {x, y}
   * @param {Object} end - End point {x, y}
   * @param {boolean} append - Whether to add to current selection
   */
  finalizeSelection(start, end, append) {
    // Calculate selection rectangle
    const selectionRect = {
      x: Math.min(start.x, end.x),
      y: Math.min(start.y, end.y),
      width: Math.abs(end.x - start.x),
      height: Math.abs(end.y - start.y)
    };
    
    // If selection area is too small, treat as a click
    if (selectionRect.width < 5 && selectionRect.height < 5) {
      return;
    }
    
    // Publish selection rectangle event
    this.eventBus.publish('interaction.finalizeSelection', {
      rect: selectionRect,
      append,
      callback: (entityIds, relationshipIds) => {
        // Update selection with entities in the rectangle
        if (append) {
          // Add to current selection
          const newEntityIds = [
            ...new Set([...this.state.selectedEntityIds, ...entityIds])
          ];
          
          const newRelationshipIds = [
            ...new Set([...this.state.selectedRelationshipIds, ...relationshipIds])
          ];
          
          this.state.setSelectedEntities(newEntityIds);
          this.state.setSelectedRelationships(newRelationshipIds);
        } else {
          // Replace current selection
          this.state.setSelectedEntities(entityIds);
          this.state.setSelectedRelationships(relationshipIds);
        }
        
        // Publish selection changed event
        this.eventBus.publish('interaction.selectionChanged', {
          entities: this.state.selectedEntityIds,
          relationships: this.state.selectedRelationshipIds
        });
      }
    });
  }

  /**
   * Cleanup and remove event listeners
   */
  cleanup() {
    if (!this.svg) {
      return;
    }
    
    // Remove event listeners
    this.svg.removeEventListener('wheel', this.handleWheel);
    this.svg.removeEventListener('mousedown', this.handleMouseDown);
    this.svg.removeEventListener('mousemove', this.handleMouseMove);
    this.svg.removeEventListener('mouseup', this.handleMouseUp);
    this.svg.removeEventListener('mouseleave', this.handleMouseLeave);
    this.svg.removeEventListener('click', this.handleClick);
    this.svg.removeEventListener('dblclick', this.handleDoubleClick);
    this.svg.removeEventListener('touchstart', this.handleTouchStart);
    this.svg.removeEventListener('touchmove', this.handleTouchMove);
    this.svg.removeEventListener('touchend', this.handleTouchEnd);
    this.svg.removeEventListener('keydown', this.handleKeyDown);
    
    // Clear state
    this.state = new InteractionState();
    this.initialized = false;
  }
}
