import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

// API base URL
const API_URL = '/api';

/**
 * Async thunk for fetching schemas by repository ID
 */
export const fetchSchemasByRepository = createAsyncThunk(
  'schemas/fetchSchemasByRepository',
  async (repoId, { rejectWithValue }) => {
    try {
      const response = await axios.get(`${API_URL}/repositories/${repoId}/schemas`);
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Failed to fetch schemas'
      );
    }
  }
);

/**
 * Async thunk for fetching a single schema by ID
 */
export const fetchSchemaById = createAsyncThunk(
  'schemas/fetchSchemaById',
  async (schemaId, { rejectWithValue }) => {
    try {
      const response = await axios.get(`${API_URL}/schemas/${schemaId}`);
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Failed to fetch schema'
      );
    }
  }
);

// Initial state
const initialState = {
  schemas: [],
  currentSchema: null,
  status: 'idle', // 'idle' | 'loading' | 'succeeded' | 'failed'
  error: null,
  filteredSchemas: [],
  filters: {
    formatType: null,
    search: '',
  },
};

// Create slice
const schemasSlice = createSlice({
  name: 'schemas',
  initialState,
  reducers: {
    setCurrentSchema: (state, action) => {
      state.currentSchema = action.payload;
    },
    clearSchemas: (state) => {
      state.schemas = [];
      state.currentSchema = null;
      state.filteredSchemas = [];
      state.status = 'idle';
      state.error = null;
    },
    setFormatTypeFilter: (state, action) => {
      state.filters.formatType = action.payload;
      state.filteredSchemas = filterSchemas(state.schemas, {
        ...state.filters,
        formatType: action.payload,
      });
    },
    setSearchFilter: (state, action) => {
      state.filters.search = action.payload;
      state.filteredSchemas = filterSchemas(state.schemas, {
        ...state.filters,
        search: action.payload,
      });
    },
    clearFilters: (state) => {
      state.filters = {
        formatType: null,
        search: '',
      };
      state.filteredSchemas = state.schemas;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch schemas by repository
      .addCase(fetchSchemasByRepository.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchSchemasByRepository.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.schemas = action.payload;
        state.filteredSchemas = filterSchemas(action.payload, state.filters);
        state.error = null;
      })
      .addCase(fetchSchemasByRepository.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      })
      
      // Fetch schema by ID
      .addCase(fetchSchemaById.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchSchemaById.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.currentSchema = action.payload;
        state.error = null;
        
        // Update in the schemas array if it exists
        const index = state.schemas.findIndex(
          (schema) => schema.id === action.payload.id
        );
        if (index !== -1) {
          state.schemas[index] = action.payload;
        } else {
          state.schemas.push(action.payload);
        }
        
        // Update filtered schemas
        state.filteredSchemas = filterSchemas(state.schemas, state.filters);
      })
      .addCase(fetchSchemaById.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      });
  },
});

/**
 * Helper function to filter schemas based on filters
 */
const filterSchemas = (schemas, filters) => {
  let result = [...schemas];
  
  // Filter by format type
  if (filters.formatType) {
    result = result.filter(schema => schema.formatType === filters.formatType);
  }
  
  // Filter by search term
  if (filters.search) {
    const searchLowerCase = filters.search.toLowerCase();
    result = result.filter(schema => 
      schema.name.toLowerCase().includes(searchLowerCase) ||
      (schema.description && schema.description.toLowerCase().includes(searchLowerCase)) ||
      (schema.path && schema.path.toLowerCase().includes(searchLowerCase))
    );
  }
  
  return result;
};

// Export actions and reducer
export const {
  setCurrentSchema,
  clearSchemas,
  setFormatTypeFilter,
  setSearchFilter,
  clearFilters,
} = schemasSlice.actions;
export default schemasSlice.reducer;
