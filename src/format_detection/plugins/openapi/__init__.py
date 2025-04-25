"""
OpenAPI/Swagger schema format detection plugin.
"""
import json
import logging
import re
import yaml
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from src.format_detection.models import DataType, FieldConstraint, FieldInfo, SchemaDetails

logger = logging.getLogger(__name__)

class OpenAPIParser:
    """Parser for OpenAPI/Swagger schema format."""

    def __init__(self):
        """Initialize the OpenAPI/Swagger schema parser."""
        logger.debug("Initializing OpenAPI/Swagger schema parser")
        
        # Mapping of OpenAPI/Swagger types to our internal types
        self.openapi_type_mapping = {
            "string": DataType.STRING,
            "integer": DataType.INTEGER,
            "number": DataType.FLOAT,
            "boolean": DataType.BOOLEAN,
            "array": DataType.ARRAY,
            "object": DataType.OBJECT,
            "file": DataType.BINARY,
        }
        
        # OpenAPI/Swagger formats and corresponding data types
        self.openapi_format_mapping = {
            "date": DataType.DATE,
            "date-time": DataType.DATETIME,
            "password": DataType.STRING,
            "byte": DataType.BINARY,
            "binary": DataType.BINARY,
            "email": DataType.STRING,
            "uuid": DataType.STRING,
            "uri": DataType.STRING,
            "hostname": DataType.STRING,
            "ipv4": DataType.STRING,
            "ipv6": DataType.STRING,
            "int32": DataType.INTEGER,
            "int64": DataType.INTEGER,
            "float": DataType.FLOAT,
            "double": DataType.FLOAT,
        }

    def can_parse(self, content: bytes, filename: Optional[str] = None) -> Tuple[bool, float]:
        """Check if content can be parsed as OpenAPI/Swagger schema.
        
        Args:
            content: File content.
            filename: Optional filename.
            
        Returns:
            Tuple[bool, float]: (can_parse, confidence)
        """
        # Check file extension first if filename is provided
        if filename and filename.lower().endswith(('.yaml', '.yml', '.json', '.openapi.json', '.swagger.json')):
            # Medium confidence based on extension
            confidence = 0.6
        else:
            confidence = 0.0
        
        # Check content patterns
        try:
            # Try to decode the content as UTF-8
            content_str = content.decode('utf-8')
            
            # First, try to parse as JSON
            try:
                data = json.loads(content_str)
            except json.JSONDecodeError:
                # If not JSON, try to parse as YAML
                try:
                    data = yaml.safe_load(content_str)
                except Exception:
                    return False, 0.0
            
            # Check if 'swagger' or 'openapi' field is present
            if not isinstance(data, dict):
                return False, 0.0
            
            if 'swagger' in data:
                version = data['swagger']
                if isinstance(version, str) and version.startswith('2.'):
                    return True, 0.95
            
            if 'openapi' in data:
                version = data['openapi']
                if isinstance(version, str) and version.startswith('3.'):
                    return True, 0.95
            
            # Check for other OpenAPI specific fields
            openapi_fields = [
                "info", "paths", "components", "tags", "externalDocs",
                "servers", "security", "securityDefinitions", "responses",
                "parameters", "definitions", "schemes"
            ]
            
            # Count how many OpenAPI fields are present
            field_count = sum(1 for field in openapi_fields if field in data)
            
            # Check if 'info' field has version and title
            if 'info' in data and isinstance(data['info'], dict):
                if 'title' in data['info'] and 'version' in data['info']:
                    confidence = max(confidence, 0.7)
            
            # Check if 'paths' field is present and is a dict
            if 'paths' in data and isinstance(data['paths'], dict):
                confidence = max(confidence, 0.8)
                
                # Check for HTTP methods in paths
                http_methods = ["get", "post", "put", "delete", "options", "head", "patch"]
                for path in data['paths'].values():
                    if isinstance(path, dict) and any(method in path for method in http_methods):
                        confidence = max(confidence, 0.9)
            
            # Additional checks for specific combinations
            if field_count >= 4:
                confidence = max(confidence, 0.85)
            elif field_count >= 2:
                confidence = max(confidence, 0.7)
            
            if confidence > 0.6:
                return True, confidence
            
        except UnicodeDecodeError:
            # Not a UTF-8 text file
            return False, 0.0
        
        return False, confidence

    def parse_schema(self, content: bytes, filename: Optional[str] = None) -> SchemaDetails:
        """Extract schema information from OpenAPI/Swagger schema content.
        
        Args:
            content: OpenAPI/Swagger schema content.
            filename: Optional filename.
            
        Returns:
            SchemaDetails: Extracted schema details.
            
        Raises:
            ValueError: If content cannot be parsed as OpenAPI/Swagger schema.
        """
        try:
            # Parse OpenAPI/Swagger schema
            spec = self._parse_content(content)
            
            # Extract schema information
            fields = []
            metadata = {
                "spec_version": self._extract_spec_version(spec),
                "title": self._extract_title(spec),
                "description": self._extract_description(spec),
                "version": self._extract_api_version(spec),
                "servers": self._extract_servers(spec),
                "paths": self._extract_paths_summary(spec),
                "tags": self._extract_tags(spec),
            }
            
            # Extract schema components
            components = self._extract_components(spec)
            
            # Process schema structure and extract fields from components
            for component_name, component_schema in components.items():
                self._process_component(component_name, component_schema, fields)
            
            # Extract relationships between components
            relationships = self._extract_relationships(components)
            metadata["relationships"] = relationships
            
            # Extract dependencies
            dependencies = self._extract_dependencies(spec)
            
            return SchemaDetails(
                fields=fields,
                primary_keys=[],  # OpenAPI doesn't have primary keys
                foreign_keys=[],  # OpenAPI doesn't have foreign keys
                unique_constraints=[],
                indices=[],
                metadata=metadata,
                dependencies=dependencies,
            )
            
        except Exception as e:
            logger.error(f"Error parsing OpenAPI/Swagger schema: {str(e)}")
            raise ValueError(f"Error parsing OpenAPI/Swagger schema: {str(e)}")

    def _parse_content(self, content: bytes) -> Dict[str, Any]:
        """Parse OpenAPI/Swagger content as either JSON or YAML.
        
        Args:
            content: OpenAPI/Swagger content.
            
        Returns:
            Dict[str, Any]: Parsed content.
            
        Raises:
            ValueError: If content cannot be parsed.
        """
        content_str = content.decode('utf-8')
        
        # Try to parse as JSON first
        try:
            return json.loads(content_str)
        except json.JSONDecodeError:
            # If not JSON, try to parse as YAML
            try:
                return yaml.safe_load(content_str)
            except Exception as e:
                logger.error(f"Failed to parse OpenAPI/Swagger schema: {str(e)}")
                raise ValueError(f"Failed to parse OpenAPI/Swagger schema: {str(e)}")

    def _extract_spec_version(self, spec: Dict[str, Any]) -> str:
        """Extract OpenAPI/Swagger specification version.
        
        Args:
            spec: OpenAPI/Swagger specification.
            
        Returns:
            str: Specification version.
        """
        if 'swagger' in spec:
            return f"Swagger {spec['swagger']}"
        elif 'openapi' in spec:
            return f"OpenAPI {spec['openapi']}"
        return "Unknown"

    def _extract_title(self, spec: Dict[str, Any]) -> Optional[str]:
        """Extract API title from spec.
        
        Args:
            spec: OpenAPI/Swagger specification.
            
        Returns:
            Optional[str]: API title.
        """
        info = spec.get('info', {})
        if isinstance(info, dict):
            return info.get('title')
        return None

    def _extract_description(self, spec: Dict[str, Any]) -> Optional[str]:
        """Extract API description from spec.
        
        Args:
            spec: OpenAPI/Swagger specification.
            
        Returns:
            Optional[str]: API description.
        """
        info = spec.get('info', {})
        if isinstance(info, dict):
            return info.get('description')
        return None

    def _extract_api_version(self, spec: Dict[str, Any]) -> Optional[str]:
        """Extract API version from spec.
        
        Args:
            spec: OpenAPI/Swagger specification.
            
        Returns:
            Optional[str]: API version.
        """
        info = spec.get('info', {})
        if isinstance(info, dict):
            return info.get('version')
        return None

    def _extract_servers(self, spec: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract servers information from spec.
        
        Args:
            spec: OpenAPI/Swagger specification.
            
        Returns:
            List[Dict[str, str]]: List of servers.
        """
        servers = []
        
        # OpenAPI 3.0
        if 'servers' in spec and isinstance(spec['servers'], list):
            for server in spec['servers']:
                if isinstance(server, dict) and 'url' in server:
                    servers.append({
                        'url': server['url'],
                        'description': server.get('description', '')
                    })
        
        # Swagger 2.0
        elif 'host' in spec:
            schemes = spec.get('schemes', ['https'])
            base_path = spec.get('basePath', '/')
            
            for scheme in schemes:
                servers.append({
                    'url': f"{scheme}://{spec['host']}{base_path}",
                    'description': f"Swagger 2.0 {scheme} server"
                })
        
        return servers

    def _extract_paths_summary(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract summary of API paths.
        
        Args:
            spec: OpenAPI/Swagger specification.
            
        Returns:
            List[Dict[str, Any]]: List of path summaries.
        """
        paths_summary = []
        
        paths = spec.get('paths', {})
        if not isinstance(paths, dict):
            return paths_summary
        
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
                
            path_summary = {
                'path': path,
                'operations': []
            }
            
            # HTTP methods
            http_methods = ["get", "post", "put", "delete", "options", "head", "patch"]
            
            for method in http_methods:
                if method in path_item and isinstance(path_item[method], dict):
                    operation = path_item[method]
                    
                    operation_summary = {
                        'method': method.upper(),
                        'summary': operation.get('summary', ''),
                        'operationId': operation.get('operationId', ''),
                        'tags': operation.get('tags', []),
                    }
                    
                    path_summary['operations'].append(operation_summary)
            
            paths_summary.append(path_summary)
        
        return paths_summary

    def _extract_tags(self, spec: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract tags from spec.
        
        Args:
            spec: OpenAPI/Swagger specification.
            
        Returns:
            List[Dict[str, str]]: List of tags.
        """
        tags = []
        
        spec_tags = spec.get('tags', [])
        if isinstance(spec_tags, list):
            for tag in spec_tags:
                if isinstance(tag, dict) and 'name' in tag:
                    tags.append({
                        'name': tag['name'],
                        'description': tag.get('description', '')
                    })
        
        return tags

    def _extract_components(self, spec: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract schema components.
        
        Args:
            spec: OpenAPI/Swagger specification.
            
        Returns:
            Dict[str, Dict[str, Any]]: Schema components.
        """
        components = {}
        
        # OpenAPI 3.0: components/schemas
        if 'components' in spec and isinstance(spec['components'], dict):
            schemas = spec['components'].get('schemas', {})
            if isinstance(schemas, dict):
                for name, schema in schemas.items():
                    if isinstance(schema, dict):
                        components[name] = schema
        
        # Swagger 2.0: definitions
        elif 'definitions' in spec and isinstance(spec['definitions'], dict):
            for name, schema in spec['definitions'].items():
                if isinstance(schema, dict):
                    components[name] = schema
        
        return components

    def _process_component(self, component_name: str, component_schema: Dict[str, Any], fields: List[FieldInfo]) -> None:
        """Process a schema component and extract field information.
        
        Args:
            component_name: Name of the component.
            component_schema: Component schema.
            fields: List to append fields to.
        """
        # Add field for the component itself
        fields.append(FieldInfo(
            name=component_name,
            path=component_name,
            data_type=DataType.OBJECT,
            nullable=False,
            description=component_schema.get('description', f"Schema component: {component_name}"),
            constraints=[],
            metadata={
                "type": component_schema.get('type', 'object'),
                "component": True,
            },
        ))
        
        # Handle different schema types
        schema_type = component_schema.get('type')
        
        if schema_type == 'object':
            # Process object properties
            properties = component_schema.get('properties', {})
            if isinstance(properties, dict):
                for prop_name, prop_schema in properties.items():
                    if isinstance(prop_schema, dict):
                        field_path = f"{component_name}.{prop_name}"
                        self._process_property(prop_name, prop_schema, field_path, fields, component_name)
        
        elif schema_type == 'array':
            # Process array items
            items = component_schema.get('items', {})
            if isinstance(items, dict):
                field_path = f"{component_name}.items"
                self._process_property("items", items, field_path, fields, component_name)

    def _process_property(self, prop_name: str, prop_schema: Dict[str, Any], field_path: str, fields: List[FieldInfo], parent_name: str) -> None:
        """Process a property schema and extract field information.
        
        Args:
            prop_name: Name of the property.
            prop_schema: Property schema.
            field_path: Field path.
            fields: List to append fields to.
            parent_name: Name of the parent component.
        """
        # Get property type
        prop_type = prop_schema.get('type')
        
        # Handle $ref
        if '$ref' in prop_schema:
            # Extract the referenced component name
            ref = prop_schema['$ref']
            ref_parts = ref.split('/')
            ref_name = ref_parts[-1] if ref_parts else "Unknown"
            
            # Add field for reference
            fields.append(FieldInfo(
                name=prop_name,
                path=field_path,
                data_type=DataType.OBJECT,  # Referenced components are objects
                nullable=True,
                description=prop_schema.get('description', f"Reference to {ref_name}"),
                constraints=[],
                metadata={
                    "ref": ref,
                    "ref_name": ref_name,
                    "parent": parent_name,
                },
            ))
            
            return
        
        # For arrays, process items
        if prop_type == 'array' and 'items' in prop_schema:
            items = prop_schema['items']
            
            # Handle array of $refs
            if isinstance(items, dict) and '$ref' in items:
                ref = items['$ref']
                ref_parts = ref.split('/')
                ref_name = ref_parts[-1] if ref_parts else "Unknown"
                
                # Add field for array
                fields.append(FieldInfo(
                    name=prop_name,
                    path=field_path,
                    data_type=DataType.ARRAY,
                    nullable=True,
                    description=prop_schema.get('description', f"Array of {ref_name}"),
                    constraints=self._extract_constraints(prop_schema),
                    metadata={
                        "items_ref": ref,
                        "items_ref_name": ref_name,
                        "parent": parent_name,
                    },
                ))
                
                return
            
            # Regular array items
            if isinstance(items, dict) and 'type' in items:
                # Add field for array
                fields.append(FieldInfo(
                    name=prop_name,
                    path=field_path,
                    data_type=DataType.ARRAY,
                    nullable=True,
                    description=prop_schema.get('description', f"Array of {items.get('type', 'items')}"),
                    constraints=self._extract_constraints(prop_schema),
                    metadata={
                        "items_type": items.get('type'),
                        "items_format": items.get('format'),
                        "parent": parent_name,
                    },
                ))
                
                return
        
        # For objects, process nested properties
        if prop_type == 'object' and 'properties' in prop_schema:
            properties = prop_schema['properties']
            
            # Add field for object
            fields.append(FieldInfo(
                name=prop_name,
                path=field_path,
                data_type=DataType.OBJECT,
                nullable=True,
                description=prop_schema.get('description', f"Object {prop_name}"),
                constraints=self._extract_constraints(prop_schema),
                metadata={
                    "parent": parent_name,
                    "properties_count": len(properties) if isinstance(properties, dict) else 0,
                },
            ))
            
            # Process nested properties
            if isinstance(properties, dict):
                for nested_name, nested_schema in properties.items():
                    if isinstance(nested_schema, dict):
                        nested_path = f"{field_path}.{nested_name}"
                        self._process_property(nested_name, nested_schema, nested_path, fields, field_path)
                
            return
        
        # For simple types
        data_type = self.openapi_type_mapping.get(prop_type, DataType.UNKNOWN)
        
        # Override data type based on format if present
        if 'format' in prop_schema and prop_schema['format'] in self.openapi_format_mapping:
            data_type = self.openapi_format_mapping[prop_schema['format']]
        
        # Add field for simple type
        fields.append(FieldInfo(
            name=prop_name,
            path=field_path,
            data_type=data_type,
            nullable=True,  # OpenAPI properties are nullable by default
            description=prop_schema.get('description', f"Field {prop_name}"),
            constraints=self._extract_constraints(prop_schema),
            metadata={
                "type": prop_type,
                "format": prop_schema.get('format'),
                "parent": parent_name,
            },
        ))

    def _extract_constraints(self, schema: Dict[str, Any]) -> List[FieldConstraint]:
        """Extract constraints from schema.
        
        Args:
            schema: OpenAPI/Swagger schema.
            
        Returns:
            List[FieldConstraint]: Extracted constraints.
        """
        constraints = []
        
        # Common constraints for all types
        if 'nullable' in schema:
            constraints.append(FieldConstraint(
                type="nullable",
                value=schema['nullable'],
                description=f"Nullable: {schema['nullable']}",
            ))
        
        if 'deprecated' in schema:
            constraints.append(FieldConstraint(
                type="deprecated",
                value=schema['deprecated'],
                description=f"Deprecated: {schema['deprecated']}",
            ))
        
        # String constraints
        if schema.get('type') == 'string':
            if 'minLength' in schema:
                constraints.append(FieldConstraint(
                    type="min_length",
                    value=schema['minLength'],
                    description=f"Minimum length: {schema['minLength']}",
                ))
            
            if 'maxLength' in schema:
                constraints.append(FieldConstraint(
                    type="max_length",
                    value=schema['maxLength'],
                    description=f"Maximum length: {schema['maxLength']}",
                ))
            
            if 'pattern' in schema:
                constraints.append(FieldConstraint(
                    type="pattern",
                    value=schema['pattern'],
                    description=f"Pattern: {schema['pattern']}",
                ))
            
            if 'enum' in schema:
                constraints.append(FieldConstraint(
                    type="enum",
                    value=schema['enum'],
                    description=f"Enum: {schema['enum']}",
                ))
        
        # Number constraints
        if schema.get('type') in ['integer', 'number']:
            if 'minimum' in schema:
                constraints.append(FieldConstraint(
                    type="minimum",
                    value=schema['minimum'],
                    description=f"Minimum: {schema['minimum']}",
                ))
            
            if 'maximum' in schema:
                constraints.append(FieldConstraint(
                    type="maximum",
                    value=schema['maximum'],
                    description=f"Maximum: {schema['maximum']}",
                ))
            
            if 'exclusiveMinimum' in schema:
                constraints.append(FieldConstraint(
                    type="exclusive_minimum",
                    value=schema['exclusiveMinimum'],
                    description=f"Exclusive minimum: {schema['exclusiveMinimum']}",
                ))
            
            if 'exclusiveMaximum' in schema:
                constraints.append(FieldConstraint(
                    type="exclusive_maximum",
                    value=schema['exclusiveMaximum'],
                    description=f"Exclusive maximum: {schema['exclusiveMaximum']}",
                ))
            
            if 'multipleOf' in schema:
                constraints.append(FieldConstraint(
                    type="multiple_of",
                    value=schema['multipleOf'],
                    description=f"Multiple of: {schema['multipleOf']}",
                ))
        
        # Array constraints
        if schema.get('type') == 'array':
            if 'minItems' in schema:
                constraints.append(FieldConstraint(
                    type="min_items",
                    value=schema['minItems'],
                    description=f"Minimum items: {schema['minItems']}",
                ))
            
            if 'maxItems' in schema:
                constraints.append(FieldConstraint(
                    type="max_items",
                    value=schema['maxItems'],
                    description=f"Maximum items: {schema['maxItems']}",
                ))
            
            if 'uniqueItems' in schema:
                constraints.append(FieldConstraint(
                    type="unique_items",
                    value=schema['uniqueItems'],
                    description=f"Unique items: {schema['uniqueItems']}",
                ))
        
        # Object constraints
        if schema.get('type') == 'object':
            if 'required' in schema and isinstance(schema['required'], list):
                constraints.append(FieldConstraint(
                    type="required_properties",
                    value=schema['required'],
                    description=f"Required properties: {', '.join(schema['required'])}",
                ))
            
            if 'minProperties' in schema:
                constraints.append(FieldConstraint(
                    type="min_properties",
                    value=schema['minProperties'],
                    description=f"Minimum properties: {schema['minProperties']}",
                ))
            
            if 'maxProperties' in schema:
                constraints.append(FieldConstraint(
                    type="max_properties",
                    value=schema['maxProperties'],
                    description=f"Maximum properties: {schema['maxProperties']}",
                ))
        
        # Default value constraint
        if 'default' in schema:
            constraints.append(FieldConstraint(
                type="default",
                value=schema['default'],
                description=f"Default: {schema['default']}",
            ))
        
        # Example constraint
        if 'example' in schema:
            constraints.append(FieldConstraint(
                type="example",
                value=schema['example'],
                description=f"Example: {schema['example']}",
            ))
        
        return constraints

    def _extract_relationships(self, components: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract relationships between components.
        
        Args:
            components: Schema components.
            
        Returns:
            List[Dict[str, Any]]: List of relationships.
        """
        relationships = []
        
        # Examine each component for references to other components
        for component_name, component_schema in components.items():
            # Process object properties
            if component_schema.get('type') == 'object' and 'properties' in component_schema:
                properties = component_schema['properties']
                if isinstance(properties, dict):
                    for prop_name, prop_schema in properties.items():
                        if not isinstance(prop_schema, dict):
                            continue
                            
                        # Check for direct references
                        if '$ref' in prop_schema:
                            ref = prop_schema['$ref']
                            ref_parts = ref.split('/')
                            ref_name = ref_parts[-1] if ref_parts else "Unknown"
                            
                            # Add relationship
                            relationships.append({
                                "from": component_name,
                                "to": ref_name,
                                "field": prop_name,
                                "cardinality": "one",
                            })
                        
                        # Check for array references
                        elif prop_schema.get('type') == 'array' and 'items' in prop_schema:
                            items = prop_schema['items']
                            if isinstance(items, dict) and '$ref' in items:
                                ref = items['$ref']
                                ref_parts = ref.split('/')
                                ref_name = ref_parts[-1] if ref_parts else "Unknown"
                                
                                # Add relationship
                                relationships.append({
                                    "from": component_name,
                                    "to": ref_name,
                                    "field": prop_name,
                                    "cardinality": "many",
                                })
        
        return relationships

    def _extract_dependencies(self, spec: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract dependencies from spec.
        
        Args:
            spec: OpenAPI/Swagger specification.
            
        Returns:
            List[Dict[str, str]]: List of dependencies.
        """
        dependencies = []
        
        # Extract external references
        external_docs = spec.get('externalDocs', {})
        if isinstance(external_docs, dict) and 'url' in external_docs:
            dependencies.append({
                "type": "documentation",
                "path": external_docs['url'],
                "description": external_docs.get('description', 'External documentation'),
            })
        
        return dependencies

    def extract_sample_data(self, content: bytes, max_records: int = 10) -> List[Dict[str, Any]]:
        """Extract sample data from OpenAPI/Swagger schema content.
        
        Note: OpenAPI/Swagger schema doesn't contain sample data, so this method returns
        API structure information instead.
        
        Args:
            content: OpenAPI/Swagger schema content.
            max_records: Maximum number of records to extract.
            
        Returns:
            List[Dict[str, Any]]: Sample data records.
            
        Raises:
            ValueError: If content cannot be parsed as OpenAPI/Swagger schema.
        """
        try:
            # Parse OpenAPI/Swagger schema
            spec = self._parse_content(content)
            
            # Create a sample record based on the API info
            sample_records = [{
                "api_title": self._extract_title(spec),
                "api_version": self._extract_api_version(spec),
                "spec_version": self._extract_spec_version(spec),
                "servers": self._extract_servers(spec),
                "paths": [],
            }]
            
            # Add paths information
            paths = spec.get('paths', {})
            if isinstance(paths, dict):
                for path, path_item in list(paths.items())[:min(len(paths), max_records)]:
                    if not isinstance(path_item, dict):
                        continue
                        
                    path_info = {
                        "path": path,
                        "operations": [],
                    }
                    
                    # HTTP methods
                    http_methods = ["get", "post", "put", "delete", "options", "head", "patch"]
                    
                    for method in http_methods:
                        if method in path_item and isinstance(path_item[method], dict):
                            operation = path_item[method]
                            
                            operation_info = {
                                "method": method.upper(),
                                "summary": operation.get('summary', ''),
                                "description": operation.get('description', ''),
                                "operationId": operation.get('operationId', ''),
                                "produces": operation.get('produces', []),
                                "consumes": operation.get('consumes', []),
                            }
                            
                            # Add parameters if present
                            params = operation.get('parameters', [])
                            if isinstance(params, list) and params:
                                operation_info["parameters"] = []
                                
                                for param in params:
                                    if isinstance(param, dict):
                                        param_info = {
                                            "name": param.get('name', ''),
                                            "in": param.get('in', ''),
                                            "required": param.get('required', False),
                                            "type": param.get('type', '') or (param.get('schema', {}) or {}).get('type', ''),
                                        }
                                        
                                        operation_info["parameters"].append(param_info)
                            
                            # Add responses if present
                            responses = operation.get('responses', {})
                            if isinstance(responses, dict) and responses:
                                operation_info["responses"] = []
                                
                                for status_code, response in responses.items():
                                    if isinstance(response, dict):
                                        response_info = {
                                            "status_code": status_code,
                                            "description": response.get('description', ''),
                                        }
                                        
                                        operation_info["responses"].append(response_info)
                            
                            path_info["operations"].append(operation_info)
                    
                    sample_records[0]["paths"].append(path_info)
            
            # Add components information
            components = self._extract_components(spec)
            if components:
                sample_records[0]["components"] = []
                
                for component_name, component_schema in list(components.items())[:min(len(components), max_records)]:
                    component_info = {
                        "name": component_name,
                        "type": component_schema.get('type', 'object'),
                        "description": component_schema.get('description', ''),
                    }
                    
                    # Add properties if present
                    if component_schema.get('type') == 'object' and 'properties' in component_schema:
                        properties = component_schema['properties']
                        if isinstance(properties, dict):
                            component_info["properties"] = []
                            
                            for prop_name, prop_schema in properties.items():
                                if isinstance(prop_schema, dict):
                                    prop_info = {
                                        "name": prop_name,
                                        "type": prop_schema.get('type', 'unknown'),
                                        "description": prop_schema.get('description', ''),
                                    }
                                    
                                    component_info["properties"].append(prop_info)
                    
                    sample_records[0]["components"].append(component_info)
            
            return sample_records
            
        except Exception as e:
            logger.error(f"Error extracting sample data: {str(e)}")
            raise ValueError(f"Error extracting sample data: {str(e)}")


# Register the plugin
def register_plugin():
    """Register the OpenAPI/Swagger schema parser plugin."""
    return {
        "format_id": "openapi",
        "parser": OpenAPIParser(),
        "format_info": {
            "id": "openapi",
            "name": "OpenAPI/Swagger",
            "description": "OpenAPI/Swagger API Definition",
            "mime_types": ["application/json", "application/yaml", "text/yaml"],
            "extensions": [".yaml", ".yml", ".json", ".openapi.json", ".swagger.json"],
            "capabilities": {
                "schema_extraction": True,
                "type_inference": True,
                "relationship_detection": True,
                "streaming": False,
            },
            "examples": ["swagger: ", "openapi: ", "paths:", "components:"],
            "schema_type": "api",
            "version": "3.0",
        }
    }
