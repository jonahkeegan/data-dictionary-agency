"""
YAML format detection plugin.
"""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from src.format_detection.models import DataType, FieldConstraint, FieldInfo, SchemaDetails

logger = logging.getLogger(__name__)

class YAMLParser:
    """Parser for YAML format."""

    def __init__(self):
        """Initialize the YAML parser."""
        logger.debug("Initializing YAML parser")

    def can_parse(self, content: bytes, filename: Optional[str] = None) -> Tuple[bool, float]:
        """Check if content can be parsed as YAML.
        
        Args:
            content: File content.
            filename: Optional filename.
            
        Returns:
            Tuple[bool, float]: (can_parse, confidence)
        """
        # Check file extension first if filename is provided
        if filename and filename.lower().endswith(('.yaml', '.yml')):
            # High confidence based on extension
            return True, 0.9
        
        # Check content patterns
        try:
            # Try to decode the first part of the content as UTF-8
            sample = content[:1000].decode('utf-8', errors='strict')
            
            # Look for common YAML patterns
            
            # Document start marker
            if '---' in sample:
                return True, 0.8
            
            # Key-value pairs
            if re.search(r'^[a-zA-Z0-9_-]+:\s*\S+', sample, re.MULTILINE):
                return True, 0.7
            
            # Lists with dashes
            if re.search(r'^-\s+\S+', sample, re.MULTILINE):
                return True, 0.7
            
            # Indented structure
            if re.search(r'^\s{2,}[a-zA-Z0-9_-]+:\s*\S+', sample, re.MULTILINE):
                return True, 0.65
            
            # Comments
            if re.search(r'^#.*$', sample, re.MULTILINE):
                # Comments alone are weak indicators
                return True, 0.4
            
        except UnicodeDecodeError:
            # Not a UTF-8 text file, probably not YAML
            return False, 0.0
        
        return False, 0.0

    def parse_schema(self, content: bytes, filename: Optional[str] = None) -> SchemaDetails:
        """Extract schema information from YAML content.
        
        Args:
            content: YAML content.
            filename: Optional filename.
            
        Returns:
            SchemaDetails: Extracted schema details.
            
        Raises:
            ValueError: If content cannot be parsed as YAML.
        """
        try:
            import yaml
            
            # Parse YAML
            try:
                # Use safe_load to prevent code execution
                yaml_data = yaml.safe_load(content.decode('utf-8'))
            except Exception as e:
                logger.error(f"Failed to parse YAML: {str(e)}")
                raise ValueError(f"Failed to parse YAML: {str(e)}")
            
            # Extract schema information
            fields = []
            metadata = {
                "structure_type": self._determine_structure_type(yaml_data),
                "yaml_version": None,  # Can't reliably determine YAML version from content
            }
            
            # Process structure and extract fields
            self._process_structure(yaml_data, fields)
            
            return SchemaDetails(
                fields=fields,
                primary_keys=[],  # YAML doesn't have a standard concept of primary keys
                foreign_keys=[],  # YAML doesn't have a standard concept of foreign keys
                unique_constraints=[],
                indices=[],
                metadata=metadata,
                dependencies=[],
            )
            
        except ImportError as e:
            logger.error(f"Required YAML parsing library not available: {str(e)}")
            raise ValueError(f"Required YAML parsing library not available: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing YAML schema: {str(e)}")
            raise ValueError(f"Error parsing YAML schema: {str(e)}")

    def _determine_structure_type(self, data: Any) -> str:
        """Determine the structure type of YAML data.
        
        Args:
            data: YAML data.
            
        Returns:
            str: Structure type.
        """
        if data is None:
            return "empty"
        elif isinstance(data, list):
            return "list"
        elif isinstance(data, dict):
            return "object"
        else:
            return "scalar"

    def _process_structure(self, data: Any, fields: List[FieldInfo], parent_path: str = "") -> None:
        """Process YAML structure and extract field information.
        
        Args:
            data: YAML data.
            fields: List to append fields to.
            parent_path: Path to parent element.
        """
        if isinstance(data, dict):
            # Process each key-value pair
            for key, value in data.items():
                field_path = f"{parent_path}.{key}" if parent_path else key
                
                # Determine field type and process accordingly
                if isinstance(value, (dict, list)):
                    # Complex type - recursively process
                    data_type = DataType.OBJECT if isinstance(value, dict) else DataType.ARRAY
                    
                    fields.append(FieldInfo(
                        name=key,
                        path=field_path,
                        data_type=data_type,
                        nullable=True,
                        description=f"{'Object' if data_type == DataType.OBJECT else 'Array'} field {key}",
                        constraints=[],
                        metadata={
                            "child_count": len(value) if value else 0,
                            "complex_type": True,
                        },
                    ))
                    
                    # Recursively process the structure
                    self._process_structure(value, fields, field_path)
                else:
                    # Primitive type
                    data_type = self._infer_type(value)
                    sample_value = str(value) if value is not None else None
                    
                    fields.append(FieldInfo(
                        name=key,
                        path=field_path,
                        data_type=data_type,
                        nullable=True,
                        description=f"Field {key}",
                        constraints=self._infer_constraints(value),
                        metadata={},
                        sample_values=[sample_value] if sample_value else None,
                    ))
                    
        elif isinstance(data, list):
            # Process list elements
            
            # Check if the list is homogeneous
            item_types = set()
            complex_items = False
            
            for i, item in enumerate(data[:10]):  # Sample first 10 items
                if isinstance(item, (dict, list)):
                    complex_items = True
                    
                item_type = self._infer_type(item)
                item_types.add(item_type)
            
            # Add field for the array itself
            array_field_path = parent_path
            
            # Only process list elements if they're complex objects
            if complex_items:
                # Process a sample of list items to infer schema
                for i, item in enumerate(data[:5]):  # Limit to first 5 items
                    if isinstance(item, dict):
                        item_path = f"{parent_path}[{i}]"
                        self._process_structure(item, fields, item_path)
                    elif isinstance(item, list):
                        item_path = f"{parent_path}[{i}]"
                        self._process_structure(item, fields, item_path)

    def _infer_type(self, value: Any) -> DataType:
        """Infer data type from a value.
        
        Args:
            value: Value to infer type from.
            
        Returns:
            DataType: Inferred data type.
        """
        if value is None:
            return DataType.NULL
        elif isinstance(value, bool):
            return DataType.BOOLEAN
        elif isinstance(value, int):
            return DataType.INTEGER
        elif isinstance(value, float):
            return DataType.FLOAT
        elif isinstance(value, str):
            # Check for date patterns
            if re.match(r'\d{4}-\d{2}-\d{2}$', value):
                return DataType.DATE
            
            # Check for datetime patterns
            if re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', value):
                return DataType.DATETIME
            
            return DataType.STRING
        elif isinstance(value, list):
            return DataType.ARRAY
        elif isinstance(value, dict):
            return DataType.OBJECT
        else:
            return DataType.UNKNOWN

    def _infer_constraints(self, value: Any) -> List[FieldConstraint]:
        """Infer constraints from a value.
        
        Args:
            value: Value to infer constraints from.
            
        Returns:
            List[FieldConstraint]: Inferred constraints.
        """
        constraints = []
        
        if isinstance(value, str):
            # Add length constraint
            constraints.append(FieldConstraint(
                type="length",
                value=len(value),
                description=f"String length: {len(value)}",
            ))
            
            # Check for formatting constraints (email, URL, etc.)
            if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
                constraints.append(FieldConstraint(
                    type="format",
                    value="email",
                    description="Email format",
                ))
            elif re.match(r'^(http|https)://', value):
                constraints.append(FieldConstraint(
                    type="format",
                    value="url",
                    description="URL format",
                ))
                
        elif isinstance(value, (int, float)):
            # Could infer min/max based on a single value, but it's not very reliable
            pass
            
        return constraints

    def extract_sample_data(self, content: bytes, max_records: int = 10) -> List[Dict[str, Any]]:
        """Extract sample data from YAML content.
        
        Args:
            content: YAML content.
            max_records: Maximum number of records to extract.
            
        Returns:
            List[Dict[str, Any]]: Sample data records.
            
        Raises:
            ValueError: If content cannot be parsed as YAML.
        """
        try:
            import yaml
            
            # Parse YAML
            try:
                # Use safe_load to prevent code execution
                yaml_data = yaml.safe_load(content.decode('utf-8'))
            except Exception as e:
                logger.error(f"Failed to parse YAML: {str(e)}")
                raise ValueError(f"Failed to parse YAML: {str(e)}")
            
            sample_records = []
            
            # Handle different YAML structures
            if isinstance(yaml_data, list):
                # List of items - each item is a record
                for i, item in enumerate(yaml_data[:max_records]):
                    if isinstance(item, dict):
                        sample_records.append(item)
                    else:
                        # Convert non-dict items to a dict with an index key
                        sample_records.append({"item": item})
                        
            elif isinstance(yaml_data, dict):
                # If root is a dict, check if it contains a list of records
                for key, value in yaml_data.items():
                    if isinstance(value, list) and len(value) > 1 and all(isinstance(x, dict) for x in value[:5]):
                        # Likely a list of records
                        for i, item in enumerate(value[:max_records]):
                            sample_records.append(item)
                        break
                
                # If no records found, use the root dict as a single record
                if not sample_records:
                    sample_records.append(yaml_data)
            else:
                # Scalar value - convert to a dict with a value key
                sample_records.append({"value": yaml_data})
            
            return sample_records
            
        except ImportError as e:
            logger.error(f"Required YAML parsing library not available: {str(e)}")
            raise ValueError(f"Required YAML parsing library not available: {str(e)}")
        except Exception as e:
            logger.error(f"Error extracting sample data: {str(e)}")
            raise ValueError(f"Error extracting sample data: {str(e)}")


# Register the plugin
def register_plugin():
    """Register the YAML parser plugin."""
    return {
        "format_id": "yaml",
        "parser": YAMLParser(),
        "format_info": {
            "id": "yaml",
            "name": "YAML",
            "description": "YAML Ain't Markup Language",
            "mime_types": ["application/yaml", "text/yaml"],
            "extensions": [".yaml", ".yml"],
            "capabilities": {
                "schema_extraction": True,
                "type_inference": True,
                "relationship_detection": True,
                "streaming": False,
            },
            "examples": ["---", "key: value", "- item"],
            "schema_type": "hierarchical",
            "version": "1.2",
        }
    }
