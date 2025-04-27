/**
 * Event Bus
 * 
 * Central event system for communication between visualization components
 * 
 * @module visualization/events/event-bus
 */

/**
 * Event bus implementation for visualization components
 */
export class EventBus {
  /**
   * Create a new event bus
   */
  constructor() {
    this.subscribers = new Map();
    this.oneTimeSubscribers = new Map();
  }

  /**
   * Subscribe to an event
   * 
   * @param {string} event - Event name
   * @param {Function} callback - Event callback
   * @returns {Object} - Subscription object with unsubscribe method
   */
  subscribe(event, callback) {
    if (!this.subscribers.has(event)) {
      this.subscribers.set(event, new Set());
    }
    
    this.subscribers.get(event).add(callback);
    
    return {
      unsubscribe: () => this.unsubscribe(event, callback)
    };
  }

  /**
   * Subscribe to an event and unsubscribe after first trigger
   * 
   * @param {string} event - Event name
   * @param {Function} callback - Event callback
   * @returns {Object} - Subscription object with unsubscribe method
   */
  subscribeOnce(event, callback) {
    const onceCallback = (data) => {
      callback(data);
      this.unsubscribe(event, onceCallback);
    };
    
    if (!this.oneTimeSubscribers.has(event)) {
      this.oneTimeSubscribers.set(event, new Set());
    }
    
    this.oneTimeSubscribers.get(event).add(onceCallback);
    
    return {
      unsubscribe: () => this.unsubscribe(event, onceCallback, true)
    };
  }

  /**
   * Unsubscribe from an event
   * 
   * @param {string} event - Event name
   * @param {Function} callback - Event callback
   * @param {boolean} isOneTime - Whether it's a one-time subscription
   * @returns {boolean} - Whether unsubscribe was successful
   */
  unsubscribe(event, callback, isOneTime = false) {
    const subscriberMap = isOneTime ? this.oneTimeSubscribers : this.subscribers;
    
    if (!subscriberMap.has(event)) {
      return false;
    }
    
    const subscribers = subscriberMap.get(event);
    const removed = subscribers.delete(callback);
    
    // Clean up empty sets
    if (subscribers.size === 0) {
      subscriberMap.delete(event);
    }
    
    return removed;
  }

  /**
   * Publish an event to all subscribers
   * 
   * @param {string} event - Event name
   * @param {*} data - Event data
   * @returns {number} - Number of subscribers notified
   */
  publish(event, data) {
    let count = 0;
    
    // Notify regular subscribers
    if (this.subscribers.has(event)) {
      const subscribers = this.subscribers.get(event);
      
      for (const callback of subscribers) {
        try {
          callback(data);
          count++;
        } catch (error) {
          console.error(`Error in event subscriber for '${event}':`, error);
        }
      }
    }
    
    // Notify one-time subscribers
    if (this.oneTimeSubscribers.has(event)) {
      const subscribers = this.oneTimeSubscribers.get(event);
      
      for (const callback of subscribers) {
        try {
          callback(data);
          count++;
        } catch (error) {
          console.error(`Error in one-time event subscriber for '${event}':`, error);
        }
      }
      
      // Clear all one-time subscribers for this event
      this.oneTimeSubscribers.delete(event);
    }
    
    return count;
  }

  /**
   * Check if an event has subscribers
   * 
   * @param {string} event - Event name
   * @returns {boolean} - Whether the event has subscribers
   */
  hasSubscribers(event) {
    return (
      (this.subscribers.has(event) && this.subscribers.get(event).size > 0) ||
      (this.oneTimeSubscribers.has(event) && this.oneTimeSubscribers.get(event).size > 0)
    );
  }

  /**
   * Get number of subscribers for an event
   * 
   * @param {string} event - Event name
   * @returns {number} - Number of subscribers
   */
  subscriberCount(event) {
    let count = 0;
    
    if (this.subscribers.has(event)) {
      count += this.subscribers.get(event).size;
    }
    
    if (this.oneTimeSubscribers.has(event)) {
      count += this.oneTimeSubscribers.get(event).size;
    }
    
    return count;
  }

  /**
   * Clear all subscriptions
   */
  clear() {
    this.subscribers.clear();
    this.oneTimeSubscribers.clear();
  }

  /**
   * Get list of events with subscribers
   * 
   * @returns {Array<string>} - List of event names
   */
  getEvents() {
    const events = new Set([
      ...this.subscribers.keys(),
      ...this.oneTimeSubscribers.keys()
    ]);
    
    return Array.from(events);
  }
}
