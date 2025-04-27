import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

// API base URL
const API_URL = '/api';

/**
 * Async thunk for fetching relationships by repository ID
 */
export const fetchRelationshipsByRepository = createAsyncThunk(
  'relationships/fetchRelationshipsByRepository',
  async (repoId, { rejectWithValue }) => {
    try {
      const response = await axios.get(`${API_URL}/repositories/${repoId}/relationships`);
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Failed to fetch relationships'
      );
    }
  }
);

/**
 * Async thunk for fetching relationships by schema ID
 */
export const fetchRelationshipsBySchema = createAsyncThunk(
  'relationships/fetchRelationshipsBySchema',
  async (schemaId, { rejectWithValue }) => {
    try {
      const response = await axios.get(`${API_URL}/schemas/${schemaId}/relationships`);
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Failed to fetch relationships'
      );
    }
  }
);

/**
 * Async thunk for fetching a single relationship by ID
 */
export const fetchRelationshipById = createAsyncThunk(
  'relationships/fetchRelationshipById',
  async (relationshipId, { rejectWithValue }) => {
    try {
      const response = await axios.get(`${API_URL}/relationships/${relationshipId}`);
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Failed to fetch relationship'
      );
    }
  }
);

// Initial state
const initialState = {
  relationships: [],
  currentRelationship: null,
  status: 'idle', // 'idle' | 'loading' | 'succeeded' | 'failed'
  error: null,
  filteredRelationships: [],
  filters: {
    type: null,
    confidenceLevel: null,
    search: '',
  },
};

// Create slice
const relationshipsSlice = createSlice({
  name: 'relationships',
  initialState,
  reducers: {
    setCurrentRelationship: (state, action) => {
      state.currentRelationship = action.payload;
    },
    clearRelationships: (state) => {
      state.relationships = [];
      state.currentRelationship = null;
      state.filteredRelationships = [];
      state.status = 'idle';
      state.error = null;
    },
    setTypeFilter: (state, action) => {
      state.filters.type = action.payload;
      state.filteredRelationships = filterRelationships(state.relationships, {
        ...state.filters,
        type: action.payload,
      });
    },
    setConfidenceLevelFilter: (state, action) => {
      state.filters.confidenceLevel = action.payload;
      state.filteredRelationships = filterRelationships(state.relationships, {
        ...state.filters,
        confidenceLevel: action.payload,
      });
    },
    setSearchFilter: (state, action) => {
      state.filters.search = action.payload;
      state.filteredRelationships = filterRelationships(state.relationships, {
        ...state.filters,
        search: action.payload,
      });
    },
    clearFilters: (state) => {
      state.filters = {
        type: null,
        confidenceLevel: null,
        search: '',
      };
      state.filteredRelationships = state.relationships;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch relationships by repository
      .addCase(fetchRelationshipsByRepository.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchRelationshipsByRepository.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.relationships = action.payload;
        state.filteredRelationships = filterRelationships(
          action.payload,
          state.filters
        );
        state.error = null;
      })
      .addCase(fetchRelationshipsByRepository.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      })

      // Fetch relationships by schema
      .addCase(fetchRelationshipsBySchema.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchRelationshipsBySchema.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.relationships = action.payload;
        state.filteredRelationships = filterRelationships(
          action.payload,
          state.filters
        );
        state.error = null;
      })
      .addCase(fetchRelationshipsBySchema.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      })

      // Fetch relationship by ID
      .addCase(fetchRelationshipById.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchRelationshipById.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.currentRelationship = action.payload;
        state.error = null;

        // Update in the relationships array if it exists
        const index = state.relationships.findIndex(
          (rel) => rel.id === action.payload.id
        );
        if (index !== -1) {
          state.relationships[index] = action.payload;
        } else {
          state.relationships.push(action.payload);
        }

        // Update filtered relationships
        state.filteredRelationships = filterRelationships(
          state.relationships,
          state.filters
        );
      })
      .addCase(fetchRelationshipById.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      });
  },
});

/**
 * Helper function to filter relationships based on filters
 */
const filterRelationships = (relationships, filters) => {
  let result = [...relationships];

  // Filter by type
  if (filters.type) {
    result = result.filter((rel) => rel.type === filters.type);
  }

  // Filter by confidence level
  if (filters.confidenceLevel) {
    result = result.filter((rel) => {
      if (filters.confidenceLevel === 'high') {
        return rel.confidence >= 0.75;
      } else if (filters.confidenceLevel === 'medium') {
        return rel.confidence >= 0.5 && rel.confidence < 0.75;
      } else if (filters.confidenceLevel === 'low') {
        return rel.confidence < 0.5;
      }
      return true;
    });
  }

  // Filter by search term
  if (filters.search) {
    const searchLowerCase = filters.search.toLowerCase();
    result = result.filter(
      (rel) =>
        rel.name?.toLowerCase().includes(searchLowerCase) ||
        rel.source?.toLowerCase().includes(searchLowerCase) ||
        rel.target?.toLowerCase().includes(searchLowerCase) ||
        rel.description?.toLowerCase().includes(searchLowerCase)
    );
  }

  return result;
};

// Export actions and reducer
export const {
  setCurrentRelationship,
  clearRelationships,
  setTypeFilter,
  setConfidenceLevelFilter,
  setSearchFilter,
  clearFilters,
} = relationshipsSlice.actions;
export default relationshipsSlice.reducer;
