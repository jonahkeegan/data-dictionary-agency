/**
 * Visualization Engine
 * 
 * The Data Dictionary Agency (DDA) visualization module provides interactive
 * ER diagram rendering capabilities using D3.js. This module implements the
 * technical decision #TECH_002.
 * 
 * @module visualization
 */

export { VisualizationAPI } from './api/visualization-api';
export { D3Renderer } from './renderers/d3-renderer';
export { ForceDirectedLayout, HierarchicalLayout, CircularLayout } from './layouts';
export { EventBus } from './events/event-bus';
export { InteractionHandler } from './interactions/interaction-handler';
export { VisualEntity, VisualRelationship, LayoutOptions, InteractionState } from './models';
