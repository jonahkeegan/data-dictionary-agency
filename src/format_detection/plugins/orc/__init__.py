"""
ORC format detection plugin.
"""
import io
import logging
import re
import struct
from typing import Any, Dict, List, Optional, Tuple, Union

from src.format_detection.models import DataType, FieldConstraint, FieldInfo, SchemaDetails

logger = logging.getLogger(__name__)

class ORCParser:
    """Parser for ORC (Optimized Row Columnar) format."""

    def __init__(self):
        """Initialize the ORC parser."""
        logger.debug("Initializing ORC parser")
        
        # Mapping of ORC types to our internal types
        self.orc_type_mapping = {
            "boolean": DataType.BOOLEAN,
            "tinyint": DataType.INTEGER,
            "smallint": DataType.INTEGER,
            "int": DataType.INTEGER,
            "bigint": DataType.INTEGER,
            "float": DataType.FLOAT,
            "double": DataType.FLOAT,
            "string": DataType.STRING,
            "char": DataType.STRING,
            "varchar": DataType.STRING,
            "binary": DataType.BINARY,
            "timestamp": DataType.DATETIME,
            "date": DataType.DATE,
            "decimal": DataType.FLOAT,
        }

    def can_parse(self, content: bytes, filename: Optional[str] = None) -> Tuple[bool, float]:
        """Check if content can be parsed as ORC.
        
        Args:
            content: File content.
            filename: Optional filename.
            
        Returns:
            Tuple[bool, float]: (can_parse, confidence)
        """
        # Check file extension first if filename is provided
        if filename and filename.lower().endswith('.orc'):
            # High confidence based on extension
            return True, 0.9
        
        # Check for ORC file format magic bytes
        # ORC files start with "ORC" followed by a version byte
        try:
            if len(content) < 4:
                return False, 0.0
                
            # Check for magic bytes at the beginning
            if content[:3] == b'ORC':
                return True, 0.95
            
        except Exception:
            # Not an ORC file or content is corrupted
            return False, 0.0
        
        return False, 0.0

    def parse_schema(self, content: bytes, filename: Optional[str] = None) -> SchemaDetails:
        """Extract schema information from ORC content.
        
        Args:
            content: ORC content.
            filename: Optional filename.
            
        Returns:
            SchemaDetails: Extracted schema details.
            
        Raises:
            ValueError: If content cannot be parsed as ORC.
        """
        try:
            # Use PyArrow for ORC parsing
            import pyarrow.orc as orc
            
            # Parse ORC file
            try:
                # Read the content into a buffer
                buffer = io.BytesIO(content)
                
                # Use PyArrow to parse the ORC file
                orc_file = orc.ORCFile(buffer)
                
                # Get schema and metadata
                schema = orc_file.schema
                metadata = orc_file.metadata
            except Exception as e:
                logger.error(f"Failed to parse ORC: {str(e)}")
                raise ValueError(f"Failed to parse ORC: {str(e)}")
            
            # Extract schema information
            fields = []
            orc_metadata = {
                "num_rows": metadata.num_rows,
                "content_length": metadata.content_length,
                "format_version": f"{metadata.format_version.major}.{metadata.format_version.minor}.{metadata.format_version.patch}",
                "compression": metadata.compression,
                "metadata": {},
            }
            
            # Add additional metadata if available
            if hasattr(metadata, 'created_by'):
                orc_metadata["created_by"] = metadata.created_by
            
            # Striping information
            if hasattr(metadata, 'num_stripes'):
                orc_metadata["num_stripes"] = metadata.num_stripes
            
            # Process schema fields
            self._process_schema_fields(schema, fields)
            
            return SchemaDetails(
                fields=fields,
                primary_keys=[],  # ORC doesn't have explicit primary keys
                foreign_keys=[],  # ORC doesn't have explicit foreign keys
                unique_constraints=[],
                indices=[],
                metadata=orc_metadata,
                dependencies=[],
            )
            
        except ImportError as e:
            logger.error(f"Required ORC parsing library not available: {str(e)}")
            raise ValueError(f"Required ORC parsing library not available. Please install pyarrow with: pip install pyarrow")
        except Exception as e:
            logger.error(f"Error parsing ORC schema: {str(e)}")
            raise ValueError(f"Error parsing ORC schema: {str(e)}")

    def _process_schema_fields(self, schema, fields: List[FieldInfo], parent_path: str = "") -> None:
        """Process Arrow schema and extract field information.
        
        Args:
            schema: Arrow schema.
            fields: List to append fields to.
            parent_path: Path to parent element.
        """
        import pyarrow as pa
        
        for field in schema:
            field_name = field.name
            field_path = f"{parent_path}.{field_name}" if parent_path else field_name
            field_type = field.type
            
            # Handle different Arrow types
            if pa.types.is_struct(field_type):
                # Handle struct type (nested fields)
                fields.append(FieldInfo(
                    name=field_name,
                    path=field_path,
                    data_type=DataType.OBJECT,
                    nullable=field.nullable,
                    description=f"Struct field {field_name}",
                    constraints=[],
                    metadata=self._extract_field_metadata(field),
                ))
                
                # Process nested fields
                self._process_schema_fields(field.type, fields, field_path)
                
            elif pa.types.is_list(field_type):
                # Handle list type
                fields.append(FieldInfo(
                    name=field_name,
                    path=field_path,
                    data_type=DataType.ARRAY,
                    nullable=field.nullable,
                    description=f"List field {field_name}",
                    constraints=[],
                    metadata=self._extract_field_metadata(field),
                ))
                
                # Extract item type
                list_field = field.type.value_field
                item_field_path = f"{field_path}.items"
                
                # Add field for list items
                fields.append(FieldInfo(
                    name="items",
                    path=item_field_path,
                    data_type=self._get_arrow_type(list_field.type),
                    nullable=list_field.nullable,
                    description=f"List items for {field_name}",
                    constraints=[],
                    metadata=self._extract_field_metadata(list_field),
                ))
                
            elif pa.types.is_map(field_type):
                # Handle map type
                fields.append(FieldInfo(
                    name=field_name,
                    path=field_path,
                    data_type=DataType.OBJECT,
                    nullable=field.nullable,
                    description=f"Map field {field_name}",
                    constraints=[],
                    metadata=self._extract_field_metadata(field),
                ))
                
                # Extract key and value types
                key_field = field.type.key_field
                key_field_path = f"{field_path}.key"
                
                value_field = field.type.item_field
                value_field_path = f"{field_path}.value"
                
                # Add fields for map keys and values
                fields.append(FieldInfo(
                    name="key",
                    path=key_field_path,
                    data_type=self._get_arrow_type(key_field.type),
                    nullable=key_field.nullable,
                    description=f"Map keys for {field_name}",
                    constraints=[],
                    metadata=self._extract_field_metadata(key_field),
                ))
                
                fields.append(FieldInfo(
                    name="value",
                    path=value_field_path,
                    data_type=self._get_arrow_type(value_field.type),
                    nullable=value_field.nullable,
                    description=f"Map values for {field_name}",
                    constraints=[],
                    metadata=self._extract_field_metadata(value_field),
                ))
                
            elif pa.types.is_union(field_type):
                # Handle union type
                fields.append(FieldInfo(
                    name=field_name,
                    path=field_path,
                    data_type=DataType.OBJECT,  # Represent unions as objects
                    nullable=field.nullable,
                    description=f"Union field {field_name}",
                    constraints=[],
                    metadata=self._extract_field_metadata(field),
                ))
                
                # Process each type in the union
                for i, type_id in enumerate(field.type.type_codes):
                    union_field = field.type.field(i)
                    union_field_path = f"{field_path}_{i}"
                    
                    fields.append(FieldInfo(
                        name=f"type_{type_id}",
                        path=union_field_path,
                        data_type=self._get_arrow_type(union_field.type),
                        nullable=True,  # Union fields are inherently nullable
                        description=f"Union type {type_id} for {field_name}",
                        constraints=[],
                        metadata=self._extract_field_metadata(union_field),
                    ))
                
            else:
                # Handle primitive types
                fields.append(FieldInfo(
                    name=field_name,
                    path=field_path,
                    data_type=self._get_arrow_type(field_type),
                    nullable=field.nullable,
                    description=f"Field {field_name}",
                    constraints=[],
                    metadata=self._extract_field_metadata(field),
                ))

    def _get_arrow_type(self, arrow_type) -> DataType:
        """Map Arrow data type to internal data type.
        
        Args:
            arrow_type: Arrow data type.
            
        Returns:
            DataType: Mapped internal data type.
        """
        import pyarrow as pa
        
        # Check for primitive types
        if pa.types.is_boolean(arrow_type):
            return DataType.BOOLEAN
        elif pa.types.is_integer(arrow_type):
            return DataType.INTEGER
        elif pa.types.is_floating(arrow_type):
            return DataType.FLOAT
        elif pa.types.is_decimal(arrow_type):
            return DataType.FLOAT
        elif pa.types.is_string(arrow_type):
            return DataType.STRING
        elif pa.types.is_binary(arrow_type):
            return DataType.BINARY
        elif pa.types.is_fixed_size_binary(arrow_type):
            return DataType.BINARY
        elif pa.types.is_date(arrow_type):
            return DataType.DATE
        elif pa.types.is_timestamp(arrow_type):
            return DataType.DATETIME
        elif pa.types.is_time(arrow_type):
            return DataType.STRING
        elif pa.types.is_list(arrow_type):
            return DataType.ARRAY
        elif pa.types.is_struct(arrow_type):
            return DataType.OBJECT
        elif pa.types.is_map(arrow_type):
            return DataType.OBJECT
        elif pa.types.is_union(arrow_type):
            return DataType.OBJECT
        elif pa.types.is_dictionary(arrow_type):
            return DataType.ENUM
        else:
            return DataType.UNKNOWN

    def _extract_field_metadata(self, field) -> Dict[str, Any]:
        """Extract metadata from an Arrow field.
        
        Args:
            field: Arrow field.
            
        Returns:
            Dict[str, Any]: Field metadata.
        """
        metadata = {
            "arrow_type": str(field.type),
        }
        
        # Extract field metadata
        if field.metadata:
            metadata["field_metadata"] = {}
            for key, value in field.metadata.items():
                try:
                    metadata["field_metadata"][key.decode('utf-8')] = value.decode('utf-8')
                except Exception:
                    # Skip metadata values that can't be decoded
                    continue
        
        return metadata

    def extract_sample_data(self, content: bytes, max_records: int = 10) -> List[Dict[str, Any]]:
        """Extract sample data from ORC content.
        
        Args:
            content: ORC content.
            max_records: Maximum number of records to extract.
            
        Returns:
            List[Dict[str, Any]]: Sample data records.
            
        Raises:
            ValueError: If content cannot be parsed as ORC.
        """
        try:
            # Use PyArrow for ORC parsing
            import pyarrow.orc as orc
            import pyarrow as pa
            
            # Parse ORC file
            try:
                # Read the content into a buffer
                buffer = io.BytesIO(content)
                
                # Use PyArrow to parse the ORC file
                orc_file = orc.ORCFile(buffer)
                
                # Read a batch of rows
                table = orc_file.read(max_records)
            except Exception as e:
                logger.error(f"Failed to parse ORC: {str(e)}")
                raise ValueError(f"Failed to parse ORC: {str(e)}")
            
            # Convert table to records
            sample_records = table.to_pylist()[:max_records]
            
            # Handle records with nested structures
            for i, record in enumerate(sample_records):
                sample_records[i] = self._convert_record(record)
            
            return sample_records
            
        except ImportError as e:
            logger.error(f"Required ORC parsing library not available: {str(e)}")
            raise ValueError(f"Required ORC parsing library not available. Please install pyarrow with: pip install pyarrow")
        except Exception as e:
            logger.error(f"Error extracting sample data: {str(e)}")
            raise ValueError(f"Error extracting sample data: {str(e)}")

    def _convert_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a record with possible Arrow objects to plain Python types.
        
        Args:
            record: Record with possible Arrow objects.
            
        Returns:
            Dict[str, Any]: Record with plain Python types.
        """
        import pyarrow as pa
        
        result = {}
        
        for key, value in record.items():
            # Handle None
            if value is None:
                result[key] = None
                continue
                
            # Handle Arrow arrays and other complex types
            if isinstance(value, pa.Array):
                result[key] = value.to_pylist()
            elif isinstance(value, pa.Scalar):
                result[key] = value.as_py()
            elif isinstance(value, (dict, list)):
                # Recursively convert nested structures
                if isinstance(value, dict):
                    result[key] = self._convert_record(value)
                else:  # list
                    result[key] = [
                        self._convert_record(item) if isinstance(item, dict) else item
                        for item in value
                    ]
            else:
                # Regular Python type
                result[key] = value
        
        return result


# Register the plugin
def register_plugin():
    """Register the ORC parser plugin."""
    return {
        "format_id": "orc",
        "parser": ORCParser(),
        "format_info": {
            "id": "orc",
            "name": "ORC",
            "description": "Apache ORC (Optimized Row Columnar) file format",
            "mime_types": ["application/x-orc"],
            "extensions": [".orc"],
            "capabilities": {
                "schema_extraction": True,
                "type_inference": True,
                "relationship_detection": False,
                "streaming": False,
            },
            "examples": ["ORC"],
            "schema_type": "columnar",
            "version": "1.0",
        }
    }
