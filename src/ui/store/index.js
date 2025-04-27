import { configureStore } from '@reduxjs/toolkit';
import repositoriesReducer from './slices/repositoriesSlice';
import schemasReducer from './slices/schemasSlice';
import relationshipsReducer from './slices/relationshipsSlice';
import uiReducer from './slices/uiSlice';
import authReducer from './slices/authSlice';

/**
 * Redux store configuration
 * Centralized state management for the application
 */
export const store = configureStore({
  reducer: {
    repositories: repositoriesReducer,
    schemas: schemasReducer,
    relationships: relationshipsReducer,
    ui: uiReducer,
    auth: authReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore these action types
        ignoredActions: ['auth/setUser'],
        // Ignore these field paths in all actions
        ignoredActionPaths: ['payload.timestamp'],
        // Ignore these paths in the state
        ignoredPaths: ['auth.user'],
      },
    }),
  devTools: process.env.NODE_ENV !== 'production',
});

// Export types for TypeScript usage
export const selectRepositories = (state) => state.repositories;
export const selectSchemas = (state) => state.schemas;
export const selectRelationships = (state) => state.relationships;
export const selectUi = (state) => state.ui;
export const selectAuth = (state) => state.auth;
