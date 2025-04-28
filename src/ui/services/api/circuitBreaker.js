/**
 * Circuit Breaker Pattern
 * 
 * Implements the circuit breaker pattern to prevent cascading failures
 * when the API is experiencing issues. The circuit breaker will:
 * 
 * 1. Monitor for failures and track failure counts
 * 2. "Open" the circuit when failures exceed threshold
 * 3. Automatically reset after a cooling period
 * 4. Allow configurable fallback mechanisms
 */

// Circuit states
const STATES = {
  CLOSED: 'CLOSED',       // Normal operation - requests flow through
  OPEN: 'OPEN',           // Circuit is open - requests immediately fail
  HALF_OPEN: 'HALF_OPEN'  // Testing if system has recovered
};

// Default configuration
const DEFAULT_CONFIG = {
  failureThreshold: 5,     // Number of failures before opening circuit
  resetTimeout: 30000,     // 30 seconds before trying again
  monitorWindow: 60000,    // 1 minute rolling window for failures
  minimumRequests: 3,      // Minimum requests needed before circuit can open
  allowRetryInHalfOpen: 1, // How many requests to allow in HALF_OPEN state
  logEnabled: true         // Whether to log circuit state changes
};

// Store circuit breakers by name
const circuits = new Map();

/**
 * Create a new circuit breaker
 * @param {string} name - Unique name for the circuit (e.g., 'repositories-api')
 * @param {Object} [config] - Circuit configuration
 * @returns {Object} Circuit breaker instance
 */
export const create = (name, config = {}) => {
  // If circuit already exists, return it
  if (circuits.has(name)) {
    return circuits.get(name);
  }
  
  // Merge configuration
  const circuitConfig = {
    ...DEFAULT_CONFIG,
    ...config
  };
  
  // Initialize circuit state
  const circuit = {
    name,
    state: STATES.CLOSED,
    failures: [],
    halfOpenAttempts: 0,
    lastStateChange: Date.now(),
    config: circuitConfig,
    resetTimer: null
  };
  
  circuits.set(name, circuit);
  return circuit;
};

/**
 * Get a circuit breaker by name
 * @param {string} name - Circuit name
 * @returns {Object|null} Circuit breaker or null if not found
 */
export const get = (name) => {
  return circuits.get(name) || null;
};

/**
 * Log circuit state changes and events
 * @param {Object} circuit - Circuit breaker
 * @param {string} message - Log message
 * @param {string} [level='info'] - Log level (info, warn, error)
 */
const logCircuitEvent = (circuit, message, level = 'info') => {
  if (!circuit.config.logEnabled) return;
  
  const logMessage = `[Circuit ${circuit.name}] ${message}`;
  
  switch (level) {
    case 'warn':
      console.warn(logMessage);
      break;
    case 'error':
      console.error(logMessage);
      break;
    case 'info':
    default:
      console.info(logMessage);
  }
};

/**
 * Change circuit state
 * @param {Object} circuit - Circuit breaker
 * @param {string} newState - New state (from STATES)
 * @param {string} [reason] - Reason for state change
 */
const changeState = (circuit, newState, reason = '') => {
  const oldState = circuit.state;
  
  // Skip if state isn't changing
  if (oldState === newState) return;
  
  // Update circuit state
  circuit.state = newState;
  circuit.lastStateChange = Date.now();
  
  // Handle state-specific behavior
  if (newState === STATES.OPEN) {
    // Clear any existing reset timer
    if (circuit.resetTimer) {
      clearTimeout(circuit.resetTimer);
    }
    
    // Set up reset timer to go to HALF_OPEN after timeout
    circuit.resetTimer = setTimeout(() => {
      circuit.halfOpenAttempts = 0;
      changeState(circuit, STATES.HALF_OPEN, 'Reset timeout elapsed');
    }, circuit.config.resetTimeout);
    
    logCircuitEvent(
      circuit, 
      `OPEN: Circuit opened for ${circuit.config.resetTimeout}ms. ${reason}`,
      'warn'
    );
  } else if (newState === STATES.HALF_OPEN) {
    logCircuitEvent(
      circuit,
      `HALF_OPEN: Circuit is testing if system has recovered. ${reason}`,
      'info'
    );
  } else if (newState === STATES.CLOSED) {
    // Clear failures when closing the circuit
    circuit.failures = [];
    
    logCircuitEvent(
      circuit,
      `CLOSED: Circuit has been closed and is operating normally. ${reason}`,
      'info'
    );
  }
};

/**
 * Record a successful execution through the circuit
 * @param {string} circuitName - Circuit name
 */
export const recordSuccess = (circuitName) => {
  const circuit = get(circuitName);
  if (!circuit) return;
  
  if (circuit.state === STATES.HALF_OPEN) {
    // If in HALF_OPEN state and request succeeds, close the circuit
    changeState(circuit, STATES.CLOSED, 'Successful test request');
  }
};

/**
 * Record a failed execution through the circuit
 * @param {string} circuitName - Circuit name
 * @param {Error} [error] - Error that caused the failure
 */
export const recordFailure = (circuitName, error = null) => {
  const circuit = get(circuitName);
  if (!circuit) return;
  
  const now = Date.now();
  
  // Add failure to the list
  circuit.failures.push({
    timestamp: now,
    error: error ? error.message : 'Unknown error'
  });
  
  // Prune old failures outside the monitoring window
  circuit.failures = circuit.failures.filter(
    failure => (now - failure.timestamp) <= circuit.config.monitorWindow
  );
  
  // If in HALF_OPEN state, immediately open circuit on failure
  if (circuit.state === STATES.HALF_OPEN) {
    changeState(
      circuit, 
      STATES.OPEN, 
      'Failed test request in HALF_OPEN state'
    );
    return;
  }
  
  // If in CLOSED state, check if we should open the circuit
  if (circuit.state === STATES.CLOSED) {
    const failureCount = circuit.failures.length;
    
    // Only open if we've had enough requests to make a decision
    if (failureCount >= circuit.config.minimumRequests &&
        failureCount >= circuit.config.failureThreshold) {
      changeState(
        circuit,
        STATES.OPEN,
        `Failure threshold exceeded (${failureCount} failures)`
      );
    }
  }
};

/**
 * Check if the circuit allows execution of the request
 * @param {string} circuitName - Circuit name
 * @returns {boolean} Whether execution is allowed
 */
export const canExecute = (circuitName) => {
  const circuit = get(circuitName);
  if (!circuit) return true; // If circuit doesn't exist, allow execution
  
  // If circuit is CLOSED, always allow execution
  if (circuit.state === STATES.CLOSED) {
    return true;
  }
  
  // If circuit is OPEN, don't allow execution
  if (circuit.state === STATES.OPEN) {
    return false;
  }
  
  // If circuit is HALF_OPEN, only allow limited requests through
  if (circuit.state === STATES.HALF_OPEN) {
    if (circuit.halfOpenAttempts < circuit.config.allowRetryInHalfOpen) {
      circuit.halfOpenAttempts++;
      return true;
    }
    return false;
  }
  
  return true;
};

/**
 * Reset a circuit to closed state
 * @param {string} circuitName - Circuit name
 */
export const reset = (circuitName) => {
  const circuit = get(circuitName);
  if (!circuit) return;
  
  // Clear any existing reset timer
  if (circuit.resetTimer) {
    clearTimeout(circuit.resetTimer);
    circuit.resetTimer = null;
  }
  
  // Reset state
  changeState(circuit, STATES.CLOSED, 'Manual reset');
};

/**
 * Get current circuit state
 * @param {string} circuitName - Circuit name
 * @returns {Object} Circuit state information
 */
export const getState = (circuitName) => {
  const circuit = get(circuitName);
  if (!circuit) return null;
  
  return {
    name: circuit.name,
    state: circuit.state,
    failureCount: circuit.failures.length,
    lastFailure: circuit.failures.length > 0 ? circuit.failures[circuit.failures.length - 1] : null,
    lastStateChange: circuit.lastStateChange,
    halfOpenAttempts: circuit.halfOpenAttempts,
    config: { ...circuit.config }
  };
};

/**
 * Execute a function with circuit breaker protection
 * @param {string} circuitName - Circuit name
 * @param {Function} fn - Function to execute
 * @param {Function} [fallback] - Fallback function if circuit is open
 * @param {Object} [options] - Additional options
 * @returns {Promise} Promise resolving to function result or fallback result
 */
export const execute = async (circuitName, fn, fallback = null, options = {}) => {
  const circuit = create(circuitName, options);
  
  if (!canExecute(circuitName)) {
    if (fallback) {
      return fallback();
    }
    
    // Default error if no fallback provided
    const error = new Error(`Circuit ${circuitName} is open`);
    error.circuitBreaker = { state: circuit.state, name: circuitName };
    throw error;
  }
  
  try {
    const result = await fn();
    recordSuccess(circuitName);
    return result;
  } catch (error) {
    recordFailure(circuitName, error);
    
    if (fallback) {
      return fallback(error);
    }
    
    throw error;
  }
};

export default {
  create,
  get,
  recordSuccess,
  recordFailure,
  canExecute,
  reset,
  getState,
  execute,
  STATES
};
