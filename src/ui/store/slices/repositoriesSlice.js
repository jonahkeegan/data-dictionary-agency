import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

// API base URL
const API_URL = '/api';

/**
 * Async thunk for fetching all repositories
 */
export const fetchRepositories = createAsyncThunk(
  'repositories/fetchRepositories',
  async (_, { rejectWithValue }) => {
    try {
      const response = await axios.get(`${API_URL}/repositories`);
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Failed to fetch repositories'
      );
    }
  }
);

/**
 * Async thunk for fetching a single repository by ID
 */
export const fetchRepositoryById = createAsyncThunk(
  'repositories/fetchRepositoryById',
  async (repoId, { rejectWithValue }) => {
    try {
      const response = await axios.get(`${API_URL}/repositories/${repoId}`);
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Failed to fetch repository'
      );
    }
  }
);

/**
 * Async thunk for adding a new repository
 */
export const addRepository = createAsyncThunk(
  'repositories/addRepository',
  async (repositoryData, { rejectWithValue }) => {
    try {
      const response = await axios.post(`${API_URL}/repositories`, repositoryData);
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Failed to add repository'
      );
    }
  }
);

// Initial state
const initialState = {
  repositories: [],
  currentRepository: null,
  status: 'idle', // 'idle' | 'loading' | 'succeeded' | 'failed'
  error: null,
};

// Create slice
const repositoriesSlice = createSlice({
  name: 'repositories',
  initialState,
  reducers: {
    setCurrentRepository: (state, action) => {
      state.currentRepository = action.payload;
    },
    clearRepositories: (state) => {
      state.repositories = [];
      state.currentRepository = null;
      state.status = 'idle';
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch repositories
      .addCase(fetchRepositories.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchRepositories.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.repositories = action.payload;
        state.error = null;
      })
      .addCase(fetchRepositories.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      })
      
      // Fetch repository by ID
      .addCase(fetchRepositoryById.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchRepositoryById.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.currentRepository = action.payload;
        state.error = null;
        
        // Update in the repositories array if it exists
        const index = state.repositories.findIndex(
          (repo) => repo.id === action.payload.id
        );
        if (index !== -1) {
          state.repositories[index] = action.payload;
        } else {
          state.repositories.push(action.payload);
        }
      })
      .addCase(fetchRepositoryById.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      })
      
      // Add repository
      .addCase(addRepository.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(addRepository.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.repositories.push(action.payload);
        state.currentRepository = action.payload;
        state.error = null;
      })
      .addCase(addRepository.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      });
  },
});

// Export actions and reducer
export const { setCurrentRepository, clearRepositories } = repositoriesSlice.actions;
export default repositoriesSlice.reducer;
