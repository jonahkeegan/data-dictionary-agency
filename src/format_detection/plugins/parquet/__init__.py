"""
Parquet format detection plugin.
"""
import io
import logging
import re
import struct
from typing import Any, Dict, List, Optional, Tuple, Union

from src.format_detection.models import DataType, FieldConstraint, FieldInfo, SchemaDetails

logger = logging.getLogger(__name__)

class ParquetParser:
    """Parser for Parquet format."""

    def __init__(self):
        """Initialize the Parquet parser."""
        logger.debug("Initializing Parquet parser")
        
        # Mapping of Parquet types to our internal types
        self.parquet_type_mapping = {
            "BOOLEAN": DataType.BOOLEAN,
            "INT32": DataType.INTEGER,
            "INT64": DataType.INTEGER,
            "INT96": DataType.INTEGER,  # Usually used for timestamps
            "FLOAT": DataType.FLOAT,
            "DOUBLE": DataType.FLOAT,
            "BYTE_ARRAY": DataType.STRING,  # Could also be BINARY
            "FIXED_LEN_BYTE_ARRAY": DataType.BINARY,
        }
        
        # Mapping of Parquet logical types to our internal types
        self.parquet_logical_type_mapping = {
            "STRING": DataType.STRING,
            "MAP": DataType.OBJECT,
            "LIST": DataType.ARRAY,
            "ENUM": DataType.ENUM,
            "DECIMAL": DataType.FLOAT,
            "DATE": DataType.DATE,
            "TIME_MILLIS": DataType.STRING,
            "TIME_MICROS": DataType.STRING,
            "TIMESTAMP_MILLIS": DataType.DATETIME,
            "TIMESTAMP_MICROS": DataType.DATETIME,
            "UINT_8": DataType.INTEGER,
            "UINT_16": DataType.INTEGER,
            "UINT_32": DataType.INTEGER,
            "UINT_64": DataType.INTEGER,
            "INT_8": DataType.INTEGER,
            "INT_16": DataType.INTEGER,
            "INT_32": DataType.INTEGER,
            "INT_64": DataType.INTEGER,
            "JSON": DataType.OBJECT,
            "BSON": DataType.OBJECT,
            "UUID": DataType.STRING,
        }

    def can_parse(self, content: bytes, filename: Optional[str] = None) -> Tuple[bool, float]:
        """Check if content can be parsed as Parquet.
        
        Args:
            content: File content.
            filename: Optional filename.
            
        Returns:
            Tuple[bool, float]: (can_parse, confidence)
        """
        # Check file extension first if filename is provided
        if filename and filename.lower().endswith('.parquet'):
            # High confidence based on extension
            return True, 0.9
        
        # Check for Parquet file header magic bytes (PAR1)
        # Parquet files start with "PAR1" and also end with "PAR1"
        try:
            if len(content) < 8:
                return False, 0.0
                
            # Check for magic bytes at the beginning and end
            if content[:4] == b'PAR1' and content[-4:] == b'PAR1':
                return True, 0.95
            
        except Exception:
            # Not a Parquet file or content is corrupted
            return False, 0.0
        
        return False, 0.0

    def parse_schema(self, content: bytes, filename: Optional[str] = None) -> SchemaDetails:
        """Extract schema information from Parquet content.
        
        Args:
            content: Parquet content.
            filename: Optional filename.
            
        Returns:
            SchemaDetails: Extracted schema details.
            
        Raises:
            ValueError: If content cannot be parsed as Parquet.
        """
        try:
            # Use PyArrow for Parquet parsing
            import pyarrow.parquet as pq
            
            # Parse Parquet file
            try:
                # Read the content into a buffer
                buffer = io.BytesIO(content)
                
                # Use PyArrow to parse the Parquet file
                pq_file = pq.ParquetFile(buffer)
                
                # Get schema
                schema = pq_file.schema_arrow
                metadata = pq_file.metadata
            except Exception as e:
                logger.error(f"Failed to parse Parquet: {str(e)}")
                raise ValueError(f"Failed to parse Parquet: {str(e)}")
            
            # Extract schema information
            fields = []
            parquet_metadata = {
                "num_rows": metadata.num_rows,
                "num_row_groups": metadata.num_row_groups,
                "format_version": metadata.format_version,
                "created_by": metadata.created_by,
                "metadata": {},
            }
            
            # Extract key-value metadata
            for key in metadata.metadata:
                try:
                    # Metadata values are stored as bytes
                    value = metadata.metadata[key].decode('utf-8')
                    parquet_metadata["metadata"][key.decode('utf-8')] = value
                except Exception:
                    # Skip metadata values that can't be decoded
                    continue
            
            # Process schema fields
            self._process_schema_fields(schema, fields)
            
            # Extract relationships
            # Parquet doesn't have explicit relationships, but we could infer them
            # from nested structure or metadata
            
            return SchemaDetails(
                fields=fields,
                primary_keys=[],  # Parquet doesn't have explicit primary keys
                foreign_keys=[],  # Parquet doesn't have explicit foreign keys
                unique_constraints=[],
                indices=[],
                metadata=parquet_metadata,
                dependencies=[],
            )
            
        except ImportError as e:
            logger.error(f"Required Parquet parsing library not available: {str(e)}")
            raise ValueError(f"Required Parquet parsing library not available. Please install pyarrow with: pip install pyarrow")
        except Exception as e:
            logger.error(f"Error parsing Parquet schema: {str(e)}")
            raise ValueError(f"Error parsing Parquet schema: {str(e)}")

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
        """Extract sample data from Parquet content.
        
        Args:
            content: Parquet content.
            max_records: Maximum number of records to extract.
            
        Returns:
            List[Dict[str, Any]]: Sample data records.
            
        Raises:
            ValueError: If content cannot be parsed as Parquet.
        """
        try:
            # Use PyArrow for Parquet parsing
            import pyarrow.parquet as pq
            import pyarrow as pa
            
            # Parse Parquet file
            try:
                # Read the content into a buffer
                buffer = io.BytesIO(content)
                
                # Use PyArrow to parse the Parquet file
                pq_file = pq.ParquetFile(buffer)
                
                # Read a batch of rows
                table = pq_file.read_row_group(0, max_records=max_records)
            except Exception as e:
                logger.error(f"Failed to parse Parquet: {str(e)}")
                raise ValueError(f"Failed to parse Parquet: {str(e)}")
            
            # Convert table to records
            sample_records = table.to_pylist()[:max_records]
            
            # Handle records with nested structures
            for i, record in enumerate(sample_records):
                sample_records[i] = self._convert_record(record)
            
            return sample_records
            
        except ImportError as e:
            logger.error(f"Required Parquet parsing library not available: {str(e)}")
            raise ValueError(f"Required Parquet parsing library not available. Please install pyarrow with: pip install pyarrow")
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
    """Register the Parquet parser plugin."""
    return {
        "format_id": "parquet",
        "parser": ParquetParser(),
        "format_info": {
            "id": "parquet",
            "name": "Parquet",
            "description": "Apache Parquet columnar storage file format",
            "mime_types": ["application/vnd.apache.parquet"],
            "extensions": [".parquet"],
            "capabilities": {
                "schema_extraction": True,
                "type_inference": True,
                "relationship_detection": False,
                "streaming": False,
            },
            "examples": ["PAR1"],
            "schema_type": "columnar",
            "version": "2.0",
        }
    }
