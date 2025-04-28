import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { RepositoryService } from '../../services/api/repositories';
import { retryRequest } from '../../services/api/client';

/**
 * Async thunk for fetching all repositories
 */
export const fetchRepositories = createAsyncThunk(
  'repositories/fetchRepositories',
  async (params = {}, { rejectWithValue }) => {
    try {
      // Use retry mechanism for this critical operation
      return await retryRequest(() => RepositoryService.getAll(params));
    } catch (error) {
      return rejectWithValue(error.message || 'Failed to fetch repositories');
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
      return await RepositoryService.getById(repoId);
    } catch (error) {
      return rejectWithValue(error.message || 'Failed to fetch repository');
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
      return await RepositoryService.create(repositoryData);
    } catch (error) {
      return rejectWithValue(error.message || 'Failed to add repository');
    }
  }
);

/**
 * Async thunk for deleting a repository
 */
export const deleteRepository = createAsyncThunk(
  'repositories/deleteRepository',
  async (repoId, { rejectWithValue }) => {
    try {
      await RepositoryService.delete(repoId);
      return repoId;
    } catch (error) {
      return rejectWithValue(error.message || 'Failed to delete repository');
    }
  }
);

/**
 * Async thunk for triggering repository analysis
 */
export const triggerRepositoryAnalysis = createAsyncThunk(
  'repositories/triggerAnalysis',
  async (repoId, { rejectWithValue }) => {
    try {
      const result = await RepositoryService.triggerAnalysis(repoId);
      return { id: repoId, result };
    } catch (error) {
      return rejectWithValue(error.message || 'Failed to trigger repository analysis');
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
      })
      
      // Delete repository
      .addCase(deleteRepository.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(deleteRepository.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.repositories = state.repositories.filter(repo => repo.id !== action.payload);
        if (state.currentRepository && state.currentRepository.id === action.payload) {
          state.currentRepository = null;
        }
        state.error = null;
      })
      .addCase(deleteRepository.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      })
      
      // Trigger repository analysis
      .addCase(triggerRepositoryAnalysis.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(triggerRepositoryAnalysis.fulfilled, (state, action) => {
        state.status = 'succeeded';
        
        // Update repository status in the repositories array
        const index = state.repositories.findIndex(
          (repo) => repo.id === action.payload.id
        );
        if (index !== -1) {
          state.repositories[index].status = 'analyzing';
          state.repositories[index].progress = 0;
        }
        
        // Update current repository if it's the one being analyzed
        if (state.currentRepository && state.currentRepository.id === action.payload.id) {
          state.currentRepository.status = 'analyzing';
          state.currentRepository.progress = 0;
        }
        
        state.error = null;
      })
      .addCase(triggerRepositoryAnalysis.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      });
  },
});

// Export actions and reducer
export const { setCurrentRepository, clearRepositories } = repositoriesSlice.actions;
export default repositoriesSlice.reducer;
