"""
Protobuf schema format detection plugin.
"""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from src.format_detection.models import DataType, FieldConstraint, FieldInfo, SchemaDetails

logger = logging.getLogger(__name__)

class ProtobufParser:
    """Parser for Protocol Buffers schema format."""

    def __init__(self):
        """Initialize the Protobuf schema parser."""
        logger.debug("Initializing Protobuf schema parser")
        
        # Mapping of Protobuf types to our internal types
        self.protobuf_type_mapping = {
            "double": DataType.FLOAT,
            "float": DataType.FLOAT,
            "int32": DataType.INTEGER,
            "int64": DataType.INTEGER,
            "uint32": DataType.INTEGER,
            "uint64": DataType.INTEGER,
            "sint32": DataType.INTEGER,
            "sint64": DataType.INTEGER,
            "fixed32": DataType.INTEGER,
            "fixed64": DataType.INTEGER,
            "sfixed32": DataType.INTEGER,
            "sfixed64": DataType.INTEGER,
            "bool": DataType.BOOLEAN,
            "string": DataType.STRING,
            "bytes": DataType.BINARY,
            # Complex types
            "enum": DataType.ENUM,
            "message": DataType.OBJECT,
            "map": DataType.OBJECT,
            "repeated": DataType.ARRAY,
            "oneof": DataType.OBJECT,
        }

    def can_parse(self, content: bytes, filename: Optional[str] = None) -> Tuple[bool, float]:
        """Check if content can be parsed as Protobuf schema.
        
        Args:
            content: File content.
            filename: Optional filename.
            
        Returns:
            Tuple[bool, float]: (can_parse, confidence)
        """
        # Check file extension first if filename is provided
        if filename and filename.lower().endswith(('.proto')):
            # High confidence based on extension
            return True, 0.95
        
        # Check content patterns
        try:
            # Try to decode the first part of the content as UTF-8
            sample = content[:10000].decode('utf-8', errors='strict')
            
            # Look for common Protobuf schema patterns
            
            # Check for syntax declaration
            if re.search(r'syntax\s*=\s*["\'](proto2|proto3)["\'];', sample):
                return True, 0.95
            
            # Check for message definitions
            if re.search(r'message\s+[A-Za-z][A-Za-z0-9_]*\s*\{', sample):
                return True, 0.9
            
            # Check for enum definitions
            if re.search(r'enum\s+[A-Za-z][A-Za-z0-9_]*\s*\{', sample):
                return True, 0.85
            
            # Check for import statements
            if re.search(r'import\s+["\'](weak|public)?[^\'"]*["\'];', sample):
                return True, 0.7
            
            # Check for option statements
            if re.search(r'option\s+[A-Za-z][A-Za-z0-9_."]*\s*=', sample):
                return True, 0.6
            
            # Check for service definitions
            if re.search(r'service\s+[A-Za-z][A-Za-z0-9_]*\s*\{', sample):
                return True, 0.8
            
        except UnicodeDecodeError:
            # Not a UTF-8 text file, probably not Protobuf schema
            return False, 0.0
        
        return False, 0.0

    def parse_schema(self, content: bytes, filename: Optional[str] = None) -> SchemaDetails:
        """Extract schema information from Protobuf schema content.
        
        Args:
            content: Protobuf schema content.
            filename: Optional filename.
            
        Returns:
            SchemaDetails: Extracted schema details.
            
        Raises:
            ValueError: If content cannot be parsed as Protobuf schema.
        """
        try:
            # Decode Protobuf content
            proto_content = content.decode('utf-8')
            
            # Extract schema information
            fields = []
            metadata = {
                "syntax": self._extract_syntax(proto_content),
                "package": self._extract_package(proto_content),
                "imports": self._extract_imports(proto_content),
                "options": self._extract_options(proto_content),
                "messages": [],
                "enums": [],
                "services": [],
            }
            
            # Extract messages
            messages = self._extract_messages(proto_content)
            metadata["messages"] = [msg["name"] for msg in messages]
            
            # Extract enums
            enums = self._extract_enums(proto_content)
            metadata["enums"] = [enum["name"] for enum in enums]
            
            # Extract services
            services = self._extract_services(proto_content)
            metadata["services"] = [svc["name"] for svc in services]
            
            # Process message fields
            for message in messages:
                message_name = message["name"]
                
                # Process each field in the message
                for field in message["fields"]:
                    field_name = field["name"]
                    field_path = f"{message_name}.{field_name}"
                    field_type = field["type"]
                    field_number = field["number"]
                    
                    # Determine if field is repeated (array)
                    is_repeated = field.get("repeated", False)
                    data_type = DataType.ARRAY if is_repeated else self._map_protobuf_type(field_type)
                    
                    # Add field constraints
                    constraints = []
                    
                    # Add field number constraint
                    constraints.append(FieldConstraint(
                        type="field_number",
                        value=field_number,
                        description=f"Field number: {field_number}",
                    ))
                    
                    # Add required constraint for proto2 (if not optional and not repeated)
                    if metadata["syntax"] == "proto2" and not field.get("optional", False) and not is_repeated:
                        constraints.append(FieldConstraint(
                            type="required",
                            value=True,
                            description="Required field",
                        ))
                    
                    # Add default value constraint if present
                    if "default" in field:
                        constraints.append(FieldConstraint(
                            type="default",
                            value=field["default"],
                            description=f"Default value: {field['default']}",
                        ))
                    
                    # Add field to fields list
                    fields.append(FieldInfo(
                        name=field_name,
                        path=field_path,
                        data_type=data_type,
                        nullable=field.get("optional", True) or metadata["syntax"] == "proto3",
                        description=field.get("description", f"Field {field_name} in message {message_name}"),
                        constraints=constraints,
                        metadata={
                            "message": message_name,
                            "field_number": field_number,
                            "is_repeated": is_repeated,
                            "original_type": field_type,
                        },
                    ))
            
            # Process enums
            for enum in enums:
                enum_name = enum["name"]
                
                # Add enum as a field for top-level enums
                fields.append(FieldInfo(
                    name=enum_name,
                    path=enum_name,
                    data_type=DataType.ENUM,
                    nullable=False,
                    description=f"Enum {enum_name}",
                    constraints=[],
                    metadata={
                        "enum_values": {val["name"]: val["number"] for val in enum["values"]},
                        "is_enum": True,
                    },
                ))
            
            # Add dependencies based on imports
            dependencies = [{"type": "import", "path": imp} for imp in metadata["imports"]]
            
            return SchemaDetails(
                fields=fields,
                primary_keys=[],  # Protobuf doesn't have primary keys
                foreign_keys=[],  # Protobuf doesn't have foreign keys
                unique_constraints=[],
                indices=[],
                metadata=metadata,
                dependencies=dependencies,
            )
            
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode Protobuf schema content: {str(e)}")
            raise ValueError(f"Failed to decode Protobuf schema content: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing Protobuf schema: {str(e)}")
            raise ValueError(f"Error parsing Protobuf schema: {str(e)}")

    def _extract_syntax(self, content: str) -> str:
        """Extract Protobuf syntax version.
        
        Args:
            content: Protobuf schema content.
            
        Returns:
            str: Syntax version (proto2 or proto3, defaults to proto2).
        """
        syntax_match = re.search(r'syntax\s*=\s*["\'](proto[23])["\'];', content)
        return syntax_match.group(1) if syntax_match else "proto2"

    def _extract_package(self, content: str) -> Optional[str]:
        """Extract Protobuf package name.
        
        Args:
            content: Protobuf schema content.
            
        Returns:
            Optional[str]: Package name.
        """
        package_match = re.search(r'package\s+([A-Za-z][A-Za-z0-9_.]*);', content)
        return package_match.group(1) if package_match else None

    def _extract_imports(self, content: str) -> List[str]:
        """Extract Protobuf imports.
        
        Args:
            content: Protobuf schema content.
            
        Returns:
            List[str]: List of imported proto files.
        """
        imports = []
        import_matches = re.finditer(r'import\s+(?:(?:"([^"]*)")|(?:\'([^\']*)\'));', content)
        
        for match in import_matches:
            imported_file = match.group(1) or match.group(2)
            imports.append(imported_file)
        
        return imports

    def _extract_options(self, content: str) -> Dict[str, str]:
        """Extract Protobuf options.
        
        Args:
            content: Protobuf schema content.
            
        Returns:
            Dict[str, str]: Dictionary of options.
        """
        options = {}
        option_matches = re.finditer(r'option\s+([A-Za-z][A-Za-z0-9_."]*)\s*=\s*(?:(?:"([^"]*)")|(?:\'([^\']*)\')|([A-Za-z][A-Za-z0-9_.]*));', content)
        
        for match in option_matches:
            option_name = match.group(1)
            option_value = match.group(2) or match.group(3) or match.group(4)
            options[option_name] = option_value
        
        return options

    def _extract_messages(self, content: str) -> List[Dict[str, Any]]:
        """Extract Protobuf message definitions.
        
        Args:
            content: Protobuf schema content.
            
        Returns:
            List[Dict[str, Any]]: List of message definitions.
        """
        messages = []
        
        # Find all message blocks first
        message_blocks = []
        message_pattern = r'message\s+([A-Za-z][A-Za-z0-9_]*)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
        
        # Function to extract nested messages
        def extract_message_blocks(content, prefix=""):
            matches = re.finditer(message_pattern, content)
            blocks = []
            
            for match in matches:
                msg_name = match.group(1)
                full_name = f"{prefix}{msg_name}" if prefix else msg_name
                msg_content = match.group(2)
                
                blocks.append((full_name, msg_content))
                
                # Extract nested messages
                nested_blocks = extract_message_blocks(msg_content, f"{full_name}.")
                blocks.extend(nested_blocks)
            
            return blocks
        
        message_blocks = extract_message_blocks(content)
        
        # Process each message block
        for msg_name, msg_content in message_blocks:
            message = {
                "name": msg_name,
                "fields": [],
                "nested_messages": [],
                "nested_enums": [],
            }
            
            # Extract fields
            field_pattern = r'(?:(?:required|optional|repeated)\s+)?([A-Za-z][A-Za-z0-9_.<>]*)\s+([A-Za-z][A-Za-z0-9_]*)\s*=\s*(\d+)(?:\s+\[([^\]]*)\])?;'
            field_matches = re.finditer(field_pattern, msg_content)
            
            for field_match in field_matches:
                field_type = field_match.group(1)
                field_name = field_match.group(2)
                field_number = int(field_match.group(3))
                field_options = field_match.group(4)
                
                field = {
                    "name": field_name,
                    "type": field_type,
                    "number": field_number,
                }
                
                # Check if field is repeated
                if re.search(r'repeated\s+', field_match.group(0), re.IGNORECASE):
                    field["repeated"] = True
                
                # Check if field is optional (proto2 only)
                if re.search(r'optional\s+', field_match.group(0), re.IGNORECASE):
                    field["optional"] = True
                
                # Check for default value
                if field_options and "default" in field_options:
                    default_match = re.search(r'default\s*=\s*([^,\s]+)', field_options)
                    if default_match:
                        field["default"] = default_match.group(1)
                
                message["fields"].append(field)
            
            messages.append(message)
        
        return messages

    def _extract_enums(self, content: str) -> List[Dict[str, Any]]:
        """Extract Protobuf enum definitions.
        
        Args:
            content: Protobuf schema content.
            
        Returns:
            List[Dict[str, Any]]: List of enum definitions.
        """
        enums = []
        enum_pattern = r'enum\s+([A-Za-z][A-Za-z0-9_]*)\s*\{([^{}]*)\}'
        enum_matches = re.finditer(enum_pattern, content)
        
        for enum_match in enum_matches:
            enum_name = enum_match.group(1)
            enum_content = enum_match.group(2)
            
            enum = {
                "name": enum_name,
                "values": [],
            }
            
            # Extract enum values
            value_pattern = r'([A-Za-z][A-Za-z0-9_]*)\s*=\s*(\d+);'
            value_matches = re.finditer(value_pattern, enum_content)
            
            for value_match in value_matches:
                value_name = value_match.group(1)
                value_number = int(value_match.group(2))
                
                enum["values"].append({
                    "name": value_name,
                    "number": value_number,
                })
            
            enums.append(enum)
        
        return enums

    def _extract_services(self, content: str) -> List[Dict[str, Any]]:
        """Extract Protobuf service definitions.
        
        Args:
            content: Protobuf schema content.
            
        Returns:
            List[Dict[str, Any]]: List of service definitions.
        """
        services = []
        service_pattern = r'service\s+([A-Za-z][A-Za-z0-9_]*)\s*\{([^{}]*)\}'
        service_matches = re.finditer(service_pattern, content)
        
        for service_match in service_matches:
            service_name = service_match.group(1)
            service_content = service_match.group(2)
            
            service = {
                "name": service_name,
                "methods": [],
            }
            
            # Extract RPC methods
            method_pattern = r'rpc\s+([A-Za-z][A-Za-z0-9_]*)\s*\(\s*([A-Za-z][A-Za-z0-9_.]*)\s*\)\s*returns\s*\(\s*([A-Za-z][A-Za-z0-9_.]*)\s*\)'
            method_matches = re.finditer(method_pattern, service_content)
            
            for method_match in method_matches:
                method_name = method_match.group(1)
                request_type = method_match.group(2)
                response_type = method_match.group(3)
                
                service["methods"].append({
                    "name": method_name,
                    "request_type": request_type,
                    "response_type": response_type,
                })
            
            services.append(service)
        
        return services

    def _map_protobuf_type(self, protobuf_type: str) -> DataType:
        """Map Protobuf type to internal data type.
        
        Args:
            protobuf_type: Protobuf type.
            
        Returns:
            DataType: Corresponding internal data type.
        """
        # Check for map type
        map_match = re.match(r'map<([^,]+),\s*([^>]+)>', protobuf_type)
        if map_match:
            return DataType.OBJECT
        
        # Check if it's a custom message type
        if "." in protobuf_type or protobuf_type[0].isupper():
            return DataType.OBJECT
        
        # Use the mapping
        return self.protobuf_type_mapping.get(protobuf_type, DataType.UNKNOWN)

    def extract_sample_data(self, content: bytes, max_records: int = 10) -> List[Dict[str, Any]]:
        """Extract sample data from Protobuf schema content.
        
        Note: Protobuf schema doesn't contain sample data, so this method returns
        sample message structures based on the schema.
        
        Args:
            content: Protobuf schema content.
            max_records: Maximum number of records to extract.
            
        Returns:
            List[Dict[str, Any]]: Sample message structures.
            
        Raises:
            ValueError: If content cannot be parsed as Protobuf schema.
        """
        try:
            # Decode Protobuf content
            proto_content = content.decode('utf-8')
            
            # Extract messages, which serve as our "sample data"
            messages = self._extract_messages(proto_content)
            
            # Create sample records based on message definitions
            sample_records = []
            
            for i, message in enumerate(messages[:max_records]):
                sample_record = {
                    "message_name": message["name"],
                    "fields": [],
                }
                
                # Add fields
                for field in message["fields"]:
                    field_info = {
                        "name": field["name"],
                        "type": field["type"],
                        "number": field["number"],
                    }
                    
                    # Add cardinality
                    if field.get("repeated", False):
                        field_info["cardinality"] = "repeated"
                    elif field.get("optional", False):
                        field_info["cardinality"] = "optional"
                    else:
                        field_info["cardinality"] = "required"
                    
                    # Add default value if present
                    if "default" in field:
                        field_info["default"] = field["default"]
                    
                    sample_record["fields"].append(field_info)
                
                sample_records.append(sample_record)
            
            return sample_records
            
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode Protobuf schema content: {str(e)}")
            raise ValueError(f"Failed to decode Protobuf schema content: {str(e)}")
        except Exception as e:
            logger.error(f"Error extracting sample data: {str(e)}")
            raise ValueError(f"Error extracting sample data: {str(e)}")


# Register the plugin
def register_plugin():
    """Register the Protobuf schema parser plugin."""
    return {
        "format_id": "protobuf",
        "parser": ProtobufParser(),
        "format_info": {
            "id": "protobuf",
            "name": "Protocol Buffers",
            "description": "Google Protocol Buffers (protobuf) Schema Definition",
            "mime_types": ["text/x-protobuf", "application/x-protobuf"],
            "extensions": [".proto"],
            "capabilities": {
                "schema_extraction": True,
                "type_inference": True,
                "relationship_detection": True,
                "streaming": False,
            },
            "examples": ["syntax =", "message ", "enum ", "service ", "rpc "],
            "schema_type": "message",
            "version": "proto3",
        }
    }
