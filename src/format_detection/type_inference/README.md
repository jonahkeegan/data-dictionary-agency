# Enhanced Type Inference System

## Overview

The Enhanced Type Inference System is a sophisticated component of the Data Dictionary Agency designed to improve type detection and analysis across multiple data formats. It goes beyond basic type detection by analyzing field names, value patterns, constraints, and complex data structures to provide high-confidence type information with alternatives when ambiguity exists.

## Key Features

- **Advanced Type Detection**: Infers types based on multiple signals including field names, value patterns, and constraints
- **Confidence Scoring**: Provides confidence scores for type decisions with detailed rationales
- **Alternative Type Suggestions**: Offers alternative type possibilities for ambiguous cases
- **Complex Structure Analysis**: Deeply analyzes arrays, objects, and map-like structures
- **Pattern Recognition**: Identifies common patterns like UUIDs, emails, dates, URLs, and more
- **Type Normalization**: Converts between format-specific types and normalized representations
- **Extensible Architecture**: Plugin-based system that can be extended with additional enhancers

## Architecture

The system follows a modular architecture with the following components:

1. **TypeInferenceService**: Core service that coordinates the type inference process
2. **TypeEnhancer**: Abstract base class for all type enhancers
3. **EnhancedTypeInfo**: Data model for enhanced type information 
4. **TypeInferenceIntegration**: Integration layer that connects to the format detection service

### Enhancer Plugins

The system includes several enhancer plugins that run in sequence, each adding more context to the type information:

- **NameBasedEnhancer**: Infers types based on field name patterns (e.g., "user_id", "created_at")
- **PatternBasedEnhancer**: Analyzes value patterns to detect specialized types (emails, dates, UUIDs)
- **ConstraintBasedEnhancer**: Uses schema constraints to refine type decisions
- **ComplexStructureEnhancer**: Analyzes arrays, objects, and map-like structures

## Usage

### Basic Usage

```python
from src.format_detection.type_inference.service import TypeInferenceService
from src.format_detection.models import SchemaDetails

# Initialize service
service = TypeInferenceService()

# Enhance a schema
enhanced_schema = service.enhance_schema(schema_details)

# Access enhanced type information
for field in enhanced_schema.fields:
    enhanced_type = field.metadata.get('enhanced_type')
    print(f"Field {field.name}: {enhanced_type['primary_type']} (confidence: {enhanced_type['confidence']['score']})")
    
    # Check for alternatives
    if enhanced_type['possible_alternatives']:
        print(f"  Alternative types: {[alt['type'] for alt in enhanced_type['possible_alternatives']]}")
```

### Integration with Format Detection

```python
from src.format_detection.service import FormatDetectionService

# Initialize service (type inference is automatically initialized)
service = FormatDetectionService()

# Parse a file with enhanced type information
result = await service.parse_file(filename, content, enhance_types=True)

# The result will include enhanced type information
```

## Type Confidence Model

Each inferred type includes a confidence score and explanation:

```json
{
  "primary_type": "string",
  "patterns": ["email"],
  "confidence": {
    "score": 0.95,
    "factors": {
      "pattern_match": 0.3,
      "email_pattern": 0.3,
      "name_pattern_match": 0.2
    },
    "rationale": "Field name 'email' matches pattern. 100% of sample values match email pattern",
    "detection_method": "pattern_based"
  },
  "possible_alternatives": []
}
```

## Format-Specific Type Handling

The system can adapt to format-specific type systems:

- **JSON Schema**: Maps to/from JSON Schema types and formats
- **SQL**: Maps to/from database column types
- **GraphQL**: Maps to/from GraphQL scalar and object types
- **Protobuf**: Maps to/from Protocol Buffer message types
- **CSV**: Infers column types from string representations

## Type Patterns

The system detects the following type patterns:

- `UUID`: UUID string format
- `EMAIL`: Email address format
- `DATE`: Date format (various representations)
- `DATETIME`: Date and time format
- `URL`: URL format
- `IP_ADDRESS`: IPv4 or IPv6 address format
- `PHONE_NUMBER`: Phone number format
- `CURRENCY`: Currency value format
- `PERCENTAGE`: Percentage format
- `ID`: General identifier pattern

## Complex Structure Analysis

For complex data structures, the system provides:

- **Array Analysis**: Item type detection, heterogeneous array detection
- **Object Analysis**: Property type detection, nested structure analysis
- **Map/Dictionary Analysis**: Key and value type detection

## Extending the System

To add a new type enhancer:

1. Create a class that inherits from `TypeEnhancer`
2. Implement the `enhance_type()` and `get_priority()` methods
3. Register the enhancer with the `TypeInferenceService`

```python
from src.format_detection.type_inference.service import TypeEnhancer

class CustomEnhancer(TypeEnhancer):
    def enhance_type(self, field_info, context):
        # Your enhancement logic here
        return enhanced_type
        
    def get_priority(self):
        return 50  # Higher values run later in the pipeline
```

## Performance Considerations

- The type inference system adds computational overhead to the parsing process
- For performance-critical scenarios, disable with `enhance_types=False`
- The system caches results for repeated analyses of the same schema
