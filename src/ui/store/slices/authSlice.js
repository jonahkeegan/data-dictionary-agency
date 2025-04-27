import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

// API base URL
const API_URL = '/api';

/**
 * Async thunk for user login
 */
export const loginUser = createAsyncThunk(
  'auth/loginUser',
  async (credentials, { rejectWithValue }) => {
    try {
      const response = await axios.post(`${API_URL}/auth/login`, credentials);
      // Store token in localStorage for persistence
      localStorage.setItem('token', response.data.token);
      // Set default Authorization header for subsequent requests
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.token}`;
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Failed to login'
      );
    }
  }
);

/**
 * Async thunk for user logout
 */
export const logoutUser = createAsyncThunk(
  'auth/logoutUser',
  async (_, { rejectWithValue }) => {
    try {
      // Optionally call logout API endpoint
      await axios.post(`${API_URL}/auth/logout`);
      // Remove token from localStorage
      localStorage.removeItem('token');
      // Remove Authorization header
      delete axios.defaults.headers.common['Authorization'];
      return null;
    } catch (error) {
      // Even if API call fails, we still remove local tokens
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
      return rejectWithValue(
        error.response?.data?.message || 'Error during logout'
      );
    }
  }
);

/**
 * Async thunk for getting the current user
 */
export const getCurrentUser = createAsyncThunk(
  'auth/getCurrentUser',
  async (_, { rejectWithValue }) => {
    try {
      // Get stored token
      const token = localStorage.getItem('token');
      
      if (!token) {
        return null;
      }
      
      // Set default header with token
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      // Get current user
      const response = await axios.get(`${API_URL}/auth/me`);
      return response.data;
    } catch (error) {
      // If unauthorized, clear token
      if (error.response?.status === 401) {
        localStorage.removeItem('token');
        delete axios.defaults.headers.common['Authorization'];
      }
      return rejectWithValue(
        error.response?.data?.message || 'Failed to get current user'
      );
    }
  }
);

// Initial state
const initialState = {
  user: null,
  token: localStorage.getItem('token') || null,
  isAuthenticated: false,
  status: 'idle', // 'idle' | 'loading' | 'succeeded' | 'failed'
  error: null,
};

// Create slice
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    // Manual setters (useful for testing or direct manipulation)
    setUser: (state, action) => {
      state.user = action.payload;
      state.isAuthenticated = !!action.payload;
    },
    setToken: (state, action) => {
      state.token = action.payload;
      localStorage.setItem('token', action.payload);
      axios.defaults.headers.common['Authorization'] = `Bearer ${action.payload}`;
    },
    clearAuth: (state) => {
      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
      state.status = 'idle';
      state.error = null;
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
    },
    resetAuthStatus: (state) => {
      state.status = 'idle';
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      // Login user
      .addCase(loginUser.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.token = action.payload.token;
        state.user = action.payload.user;
        state.isAuthenticated = true;
        state.error = null;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
        state.isAuthenticated = false;
      })
      
      // Logout user
      .addCase(logoutUser.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(logoutUser.fulfilled, (state) => {
        state.status = 'idle';
        state.token = null;
        state.user = null;
        state.isAuthenticated = false;
        state.error = null;
      })
      .addCase(logoutUser.rejected, (state, action) => {
        // Even if API call fails, we still log out locally
        state.status = 'idle';
        state.token = null;
        state.user = null;
        state.isAuthenticated = false;
        state.error = action.payload;
      })
      
      // Get current user
      .addCase(getCurrentUser.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(getCurrentUser.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.user = action.payload;
        state.isAuthenticated = !!action.payload;
        state.error = null;
      })
      .addCase(getCurrentUser.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
        state.isAuthenticated = false;
        state.user = null;
        state.token = null;
      });
  },
});

// Export actions and reducer
export const { setUser, setToken, clearAuth, resetAuthStatus } = authSlice.actions;
export default authSlice.reducer;

// Selectors
export const selectAuth = (state) => state.auth;
export const selectIsAuthenticated = (state) => state.auth.isAuthenticated;
export const selectUser = (state) => state.auth.user;
export const selectAuthStatus = (state) => state.auth.status;
