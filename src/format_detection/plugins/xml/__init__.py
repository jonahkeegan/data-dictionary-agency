"""
XML format parser plugin with support for both XML and XSD schemas.
"""
import logging
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from src.format_detection.models import (
    DataType,
    FieldConstraint,
    FieldInfo,
    FormatType,
    SchemaDetails,
)

logger = logging.getLogger(__name__)

# XML/XSD type to normalized data type mapping
XML_TYPE_MAPPING = {
    # XSD simple types
    "xs:string": DataType.STRING,
    "xsd:string": DataType.STRING,
    "xs:integer": DataType.INTEGER,
    "xsd:integer": DataType.INTEGER,
    "xs:int": DataType.INTEGER,
    "xsd:int": DataType.INTEGER,
    "xs:long": DataType.INTEGER,
    "xsd:long": DataType.INTEGER,
    "xs:float": DataType.FLOAT,
    "xsd:float": DataType.FLOAT,
    "xs:double": DataType.FLOAT,
    "xsd:double": DataType.FLOAT,
    "xs:decimal": DataType.FLOAT,
    "xsd:decimal": DataType.FLOAT,
    "xs:boolean": DataType.BOOLEAN,
    "xsd:boolean": DataType.BOOLEAN,
    "xs:date": DataType.DATE,
    "xsd:date": DataType.DATE,
    "xs:dateTime": DataType.DATETIME,
    "xsd:dateTime": DataType.DATETIME,
    "xs:time": DataType.STRING,
    "xsd:time": DataType.STRING,
    "xs:binary": DataType.BINARY,
    "xsd:binary": DataType.BINARY,
    "xs:base64Binary": DataType.BINARY,
    "xsd:base64Binary": DataType.BINARY,
    "xs:hexBinary": DataType.BINARY,
    "xsd:hexBinary": DataType.BINARY,
    "xs:anyURI": DataType.STRING,
    "xsd:anyURI": DataType.STRING,
    "xs:ID": DataType.UUID,
    "xsd:ID": DataType.UUID,
    "xs:IDREF": DataType.STRING,
    "xsd:IDREF": DataType.STRING,
}

# XML Dialect namespaces and indicators
XML_DIALECT_INDICATORS = {
    "XHTML": {
        "namespaces": ["http://www.w3.org/1999/xhtml"],
        "root_elements": ["html", "xhtml:html"],
        "patterns": ["<!DOCTYPE html>", "<html xmlns="],
    },
    "SOAP": {
        "namespaces": ["http://schemas.xmlsoap.org/soap/envelope/", "http://www.w3.org/2003/05/soap-envelope"],
        "root_elements": ["Envelope", "soap:Envelope"],
        "patterns": ["<soap:Envelope", "<SOAP-ENV:Envelope"],
    },
    "RSS": {
        "namespaces": ["http://purl.org/rss/1.0/"],
        "root_elements": ["rss", "feed"],
        "patterns": ["<rss version=", "<feed xmlns="],
    },
    "SVG": {
        "namespaces": ["http://www.w3.org/2000/svg"],
        "root_elements": ["svg", "svg:svg"],
        "patterns": ["<svg ", "<svg\n", "<svg xmlns="],
    },
    "Office Open XML": {
        "namespaces": [
            "http://schemas.openxmlformats.org/",
            "http://schemas.microsoft.com/office/",
        ],
        "root_elements": ["workbook", "document", "presentation"],
        "patterns": ["Content_Types", "rels", "document.xml"],
    },
    "OpenDocument": {
        "namespaces": ["urn:oasis:names:tc:opendocument"],
        "root_elements": ["office:document", "office:document-content"],
        "patterns": ["<office:document", "<office:document-content"],
    },
    "BPEL": {
        "namespaces": [
            "http://schemas.xmlsoap.org/ws/2003/03/business-process/",
            "http://docs.oasis-open.org/wsbpel/2.0/process/executable",
        ],
        "root_elements": ["process", "bpel:process"],
        "patterns": ["<bpel:", "<process xmlns"],
    },
    "HL7": {
        "namespaces": ["urn:hl7-org:", "http://hl7.org"],
        "root_elements": ["ClinicalDocument", "Message"],
        "patterns": ["<ClinicalDocument", "<hl7:"],
    },
    "FpML": {
        "namespaces": ["http://www.fpml.org"],
        "root_elements": ["FpML", "fpml:FpML", "dataDocument"],
        "patterns": ["<fpml:", "<FpML "],
    },
}


class XMLParser:
    """Parser for XML and XSD schema files."""
    
    def can_parse(self, filename: str, content: bytes) -> bool:
        """
        Check if the file content can be parsed as XML or XSD.
        
        Args:
            filename: Name of the file
            content: File content
            
        Returns:
            bool: True if the content appears to be XML or XSD, False otherwise
        """
        if not content:
            return False
            
        try:
            # Check file extensions
            if filename:
                extension = filename.lower().split('.')[-1]
                if extension in ['xml', 'xsd', 'svg', 'xhtml', 'rss', 'soap', 'wsdl', 'kml', 'gpx', 'plist']:
                    return True
            
            # Try to decode a sample of the content
            sample = content[:2000].decode('utf-8', errors='ignore')
            
            # Look for XML declaration
            if re.search(r'<\?xml\s+version\s*=\s*["\']', sample):
                return True
                
            # Look for DOCTYPE declaration
            if re.search(r'<!DOCTYPE\s+[^>]+>', sample):
                return True
                
            # Look for common XML patterns like tags with attributes
            if re.search(r'<[a-zA-Z][a-zA-Z0-9_:-]*(\s+[a-zA-Z][a-zA-Z0-9_:-]*\s*=\s*["\'"][^"\']*["\'"])+\s*>', sample):
                return True
                
            # Look for XML Schema patterns
            if re.search(r'<xs:schema|<xsd:schema', sample):
                return True
                
            # Look for XML namespace declarations
            if re.search(r'xmlns\s*=\s*["\']', sample):
                return True
                
            # Look for basic XML element structure
            if re.search(r'<[a-zA-Z][a-zA-Z0-9_:-]*>.*</[a-zA-Z][a-zA-Z0-9_:-]*>', sample, re.DOTALL):
                return True
                
            return False
                
        except UnicodeDecodeError:
            # Not a text file, unlikely to be XML
            return False

    def get_format_type(self) -> FormatType:
        """
        Get the format type handled by this parser.
        
        Returns:
            FormatType: The format type for XML
        """
        return FormatType.XML

    def parse_schema(self, filename: str, content: bytes) -> SchemaDetails:
        """
        Parse XML or XSD schema file and extract schema details.
        
        Args:
            filename: Name of the file
            content: File content
            
        Returns:
            SchemaDetails: Extracted schema details
        """
        logger.info(f"Parsing XML schema from file: {filename}")
        
        try:
            # Decode content
            text = content.decode('utf-8', errors='replace')
            
            # Determine if this is an XSD schema or regular XML
            is_xsd = self._is_xsd_schema(text, filename)
            is_dtd = self._has_dtd(text)
            
            # Parse the XML
            try:
                root = ET.fromstring(text)
                
                # Get root element namespaces
                namespaces = self._extract_namespaces(root)
                
                # Detect XML dialect
                dialect = self._detect_xml_dialect(root, text, namespaces)
                
                # Get schema metadata
                metadata = {
                    "schema_type": "xml",
                    "source_file": filename,
                    "root_element": root.tag,
                    "namespaces": namespaces,
                    "dialect": dialect,
                    "has_xsd_schema": is_xsd,
                    "has_dtd": is_dtd,
                }
                
                # Extract fields and constraints based on the type
                fields = []
                primary_keys = []
                unique_constraints = []
                
                if is_xsd:
                    # Extract schema from XSD
                    fields, primary_keys, unique_constraints = self._extract_xsd_schema(root, namespaces)
                elif is_dtd:
                    # Extract schema from DTD
                    fields, primary_keys = self._extract_dtd_schema(root, text)
                else:
                    # Infer schema from XML structure
                    fields, primary_keys = self._infer_schema_from_xml(root)
                
                return SchemaDetails(
                    fields=fields,
                    primary_keys=primary_keys,
                    unique_constraints=unique_constraints,
                    metadata=metadata
                )
            
            except Exception as e:
                logger.error(f"Error parsing XML: {str(e)}")
                return SchemaDetails(
                    fields=[],
                    metadata={
                        "schema_type": "xml",
                        "source_file": filename,
                        "error": str(e)
                    }
                )
                
        except Exception as e:
            logger.error(f"Error parsing XML schema: {str(e)}")
            # Return an empty schema in case of error
            return SchemaDetails(
                fields=[],
                metadata={
                    "schema_type": "xml",
                    "source_file": filename,
                    "error": str(e)
                }
            )

    def extract_sample_data(self, filename: str, content: bytes, max_records: int = 10) -> List[Dict[str, Any]]:
        """
        Extract sample data from XML content.
        
        Args:
            filename: Name of the file
            content: File content
            max_records: Maximum number of records to extract
            
        Returns:
            List[Dict[str, Any]]: Sample record structures
        """
        try:
            # Decode content
            text = content.decode('utf-8', errors='replace')
            
            # Parse the XML
            root = ET.fromstring(text)
            
            # Try to identify record elements (elements that repeat and likely represent data records)
            record_elements = self._identify_record_elements(root)
            
            samples = []
            
            if record_elements:
                # We found potential record elements
                for i, element in enumerate(record_elements[:max_records]):
                    sample = self._element_to_dict(element)
                    if sample:  # Only add non-empty samples
                        samples.append(sample)
            else:
                # No clear record elements found, use root level elements as samples
                samples.append(self._element_to_dict(root))
            
            return samples
            
        except Exception as e:
            logger.error(f"Error extracting sample data: {str(e)}")
            return [{"error": str(e)}]

    def _is_xsd_schema(self, content: str, filename: str = None) -> bool:
        """
        Check if content is an XSD schema.
        
        Args:
            content: XML content
            filename: Optional filename
            
        Returns:
            bool: True if content is an XSD schema
        """
        # Check filename extension
        if filename and filename.lower().endswith('.xsd'):
            return True
            
        # Look for XSD schema indicators in content
        xsd_indicators = [
            '<xs:schema', 
            '<xsd:schema',
            'xmlns:xs="http://www.w3.org/2001/XMLSchema"',
            'xmlns:xsd="http://www.w3.org/2001/XMLSchema"',
            '<schema xmlns="http://www.w3.org/2001/XMLSchema"'
        ]
        
        for indicator in xsd_indicators:
            if indicator in content:
                return True
                
        return False

    def _has_dtd(self, content: str) -> bool:
        """
        Check if XML has DTD definitions.
        
        Args:
            content: XML content
            
        Returns:
            bool: True if DTD is present
        """
        # Look for DOCTYPE declaration
        if re.search(r'<!DOCTYPE\s+[^>]+>', content):
            return True
            
        # Look for DTD element declarations
        if re.search(r'<!ELEMENT\s+[^>]+>', content):
            return True
            
        # Look for DTD attribute declarations
        if re.search(r'<!ATTLIST\s+[^>]+>', content):
            return True
            
        return False

    def _extract_namespaces(self, root) -> Dict[str, str]:
        """
        Extract namespaces from XML element.
        
        Args:
            root: XML root element
            
        Returns:
            Dict[str, str]: Namespace prefix to URI mapping
        """
        namespaces = {}
        
        # Check if element has nsmap attribute (lxml)
        if hasattr(root, 'nsmap'):
            for prefix, uri in root.nsmap.items():
                namespaces[prefix or "_default_"] = uri
        else:
            # Standard ElementTree doesn't expose namespaces directly
            # Extract from attributes
            for key, value in root.attrib.items():
                if key.startswith('xmlns:'):
                    prefix = key.split(':')[1]
                    namespaces[prefix] = value
                elif key == 'xmlns':
                    namespaces["_default_"] = value
        
        return namespaces

    def _detect_xml_dialect(self, root, content: str, namespaces: Dict[str, str]) -> Optional[str]:
        """
        Detect XML dialect based on content, namespaces and patterns.
        
        Args:
            root: XML root element
            content: XML content
            namespaces: Namespace mapping
            
        Returns:
            Optional[str]: Detected dialect name or None
        """
        root_tag = root.tag
        if '}' in root_tag:
            # Handle namespace in tag
            root_tag = root_tag.split('}', 1)[1]
        
        # Check each dialect's indicators
        for dialect_name, indicators in XML_DIALECT_INDICATORS.items():
            # Check namespaces
            for ns in indicators["namespaces"]:
                if any(ns in uri for uri in namespaces.values()):
                    return dialect_name
            
            # Check root elements
            if root_tag in indicators["root_elements"]:
                return dialect_name
                
            # Check patterns
            for pattern in indicators["patterns"]:
                if pattern in content:
                    return dialect_name
        
        return None

    def _extract_xsd_schema(self, root, namespaces: Dict[str, str]) -> Tuple[List[FieldInfo], List[str], List[List[str]]]:
        """
        Extract schema details from XSD schema.
        
        Args:
            root: XML root element (XSD schema)
            namespaces: Namespace mapping
            
        Returns:
            Tuple[List[FieldInfo], List[str], List[List[str]]]: Fields, primary keys, and unique constraints
        """
        fields = []
        primary_keys = []
        unique_constraints = []
        
        # Define namespace prefixes for XSD
        ns_prefixes = []
        for prefix, uri in namespaces.items():
            if "XMLSchema" in uri:
                ns_prefixes.append(prefix if prefix != "_default_" else "")
        
        if not ns_prefixes:
            ns_prefixes = ["xs", "xsd", ""]  # Default prefixes to try
        
        # Helper to check if an element matches one of the XSD namespace prefixes
        def matches_ns(tag: str, name: str) -> bool:
            return any(tag.endswith(f":{name}") for prefix in ns_prefixes if prefix) or \
                   (tag == name) or \
                   any(tag == f"{{{uri}}}{name}" for uri in namespaces.values())
        
        # Process simple and complex types
        self._process_xsd_elements(root, "", fields, primary_keys, unique_constraints, matches_ns)
        
        return fields, primary_keys, unique_constraints

    def _process_xsd_elements(self, element, parent_path: str, fields: List[FieldInfo], 
                             primary_keys: List[str], unique_constraints: List[List[str]], 
                             matches_ns) -> None:
        """
        Process XSD elements recursively.
        
        Args:
            element: Current XML element
            parent_path: Path to parent element
            fields: List to append fields to
            primary_keys: List to append primary keys to
            unique_constraints: List to append unique constraints to
            matches_ns: Function to check if tag matches namespace
        """
        # Process XSD elements (element, attribute, simpleType, complexType)
        for child in element:
            tag = child.tag
            
            # Process element declarations
            if matches_ns(tag, "element"):
                name = child.get("name")
                if not name:
                    continue
                    
                field_path = f"{parent_path}.{name}" if parent_path else name
                is_required = child.get("minOccurs", "0") != "0"
                field_type = child.get("type")
                
                # Handle in-line types
                if field_type is None:
                    # Look for inline type definitions
                    for type_child in child:
                        if matches_ns(type_child.tag, "simpleType") or matches_ns(type_child.tag, "complexType"):
                            field_type = "inline"
                            break
                
                # Map the XSD type to normalized data type
                data_type = self._map_xsd_type(field_type) if field_type else DataType.STRING
                
                # Check if this is a key field
                is_key = False
                for key_def in element.findall(".//*[@name='ID']") + element.findall(".//*[@type='xs:ID']") + \
                           element.findall(".//*[@type='xsd:ID']"):
                    if key_def.get("name") == name:
                        is_key = True
                        if name not in primary_keys:
                            primary_keys.append(name)
                            
                # Extract constraints
                constraints = []
                
                # Required constraint
                if is_required:
                    constraints.append(
                        FieldConstraint(
                            type="required",
                            value=True,
                            description="Field is required (minOccurs > 0)"
                        )
                    )
                
                # Check for uniqueness constraints
                if child.get("unique") == "true" or any(attr.endswith(":unique") and val == "true" 
                                                      for attr, val in child.attrib.items()):
                    constraints.append(
                        FieldConstraint(
                            type="unique",
                            value=True,
                            description="Field must be unique"
                        )
                    )
                    unique_constraints.append([field_path])
                
                # Create field info
                field_info = FieldInfo(
                    name=name,
                    path=field_path,
                    data_type=data_type,
                    nullable=not is_required,
                    description=None,  # We could extract annotations here if needed
                    constraints=constraints,
                    metadata={
                        "xsd_type": field_type,
                        "is_element": True,
                    }
                )
                
                fields.append(field_info)
                
                # Recursively process children if this is a complex type
                self._process_xsd_elements(child, field_path, fields, primary_keys, unique_constraints, matches_ns)
                
            # Process attribute declarations  
            elif matches_ns(tag, "attribute"):
                name = child.get("name")
                if not name:
                    continue
                    
                field_path = f"{parent_path}@{name}" if parent_path else f"@{name}"
                is_required = child.get("use") == "required"
                field_type = child.get("type")
                
                # Map the XSD type to normalized data type
                data_type = self._map_xsd_type(field_type) if field_type else DataType.STRING
                
                # Extract constraints
                constraints = []
                
                # Required constraint
                if is_required:
                    constraints.append(
                        FieldConstraint(
                            type="required",
                            value=True,
                            description="Attribute is required (use='required')"
                        )
                    )
                
                # Create field info
                field_info = FieldInfo(
                    name=name,
                    path=field_path,
                    data_type=data_type,
                    nullable=not is_required,
                    description=None,
                    constraints=constraints,
                    metadata={
                        "xsd_type": field_type,
                        "is_attribute": True,
                    }
                )
                
                fields.append(field_info)
                
            # Recursively process other elements
            else:
                self._process_xsd_elements(child, parent_path, fields, primary_keys, unique_constraints, matches_ns)

    def _map_xsd_type(self, xsd_type: Optional[str]) -> DataType:
        """
        Map XSD type to normalized data type.
        
        Args:
            xsd_type: XSD type string
            
        Returns:
            DataType: Normalized data type
        """
        if not xsd_type:
            return DataType.STRING
            
        # Check direct mapping
        if xsd_type in XML_TYPE_MAPPING:
            return XML_TYPE_MAPPING[xsd_type]
        
        # Handle namespaced types
        for xml_type, data_type in XML_TYPE_MAPPING.items():
            if xsd_type.endswith(xml_type.split(':')[-1]):
                return data_type
        
        # Default mappings based on common patterns
        if "string" in xsd_type.lower():
            return DataType.STRING
        elif "int" in xsd_type.lower():
            return DataType.INTEGER
        elif "float" in xsd_type.lower() or "double" in xsd_type.lower() or "decimal" in xsd_type.lower():
            return DataType.FLOAT
        elif "bool" in xsd_type.lower():
            return DataType.BOOLEAN
        elif "date" in xsd_type.lower() and "time" in xsd_type.lower():
            return DataType.DATETIME
        elif "date" in xsd_type.lower():
            return DataType.DATE
        elif "binary" in xsd_type.lower():
            return DataType.BINARY
        
        # Default to string for unknown types
        return DataType.STRING

    def _extract_dtd_schema(self, root, content: str) -> Tuple[List[FieldInfo], List[str]]:
        """
        Extract schema details from DTD.
        
        Args:
            root: XML root element
            content: XML content with DTD
            
        Returns:
            Tuple[List[FieldInfo], List[str]]: Fields and primary keys
        """
        fields = []
        primary_keys = []
        
        # Extract DOCTYPE declaration
        doctype_match = re.search(r'<!DOCTYPE\s+(\w+)([^>]*)>', content)
        if not doctype_match:
            return fields, primary_keys
        
        # Get the root element name from DOCTYPE
        root_element_name = doctype_match.group(1)
        
        # Extract ELEMENT declarations
        element_matches = re.finditer(r'<!ELEMENT\s+(\w+)\s+([^>]+)>', content)
        elements = {}
        
        for match in element_matches:
            element_name = match.group(1)
            element_content = match.group(2).strip()
            elements[element_name] = element_content
            
            # Create field info for each element
            field_path = element_name
            
            # Determine if element is required
            is_required = True  # Default to required in DTD
            
            # Infer data type from content model
            data_type = DataType.STRING  # Default to string
            if element_content == "EMPTY":
                data_type = DataType.NULL
            elif element_content.startswith("(#PCDATA"):
                data_type = DataType.STRING
            elif element_content.startswith("("):
                data_type = DataType.OBJECT  # Complex element
            
            field_info = FieldInfo(
                name=element_name,
                path=field_path,
                data_type=data_type,
                nullable=not is_required,
                description=None,
                constraints=[],
                metadata={
                    "dtd_content": element_content,
                    "is_element": True,
                }
            )
            
            fields.append(field_info)
        
        # Extract ATTLIST declarations
        attlist_matches = re.finditer(r'<!ATTLIST\s+(\w+)\s+([^>]+)>', content)
        
        for match in attlist_matches:
            element_name = match.group(1)
            attr_content = match.group(2).strip()
            
            # Parse attribute definitions
            attr_defs = re.finditer(r'(\w+)\s+(CDATA|ID|IDREF|IDREFS|NMTOKEN|NMTOKENS|ENTITY|ENTITIES|NOTATION|enumeration)\s+([^>]+)', attr_content)
            
            for attr_def in attr_defs:
                attr_name = attr_def.group(1)
                attr_type = attr_def.group(2)
                attr_default = attr_def.group(3).strip()
                
                field_path = f"{element_name}@{attr_name}"
                
                # Determine if attribute is required
                is_required = attr_default == "#REQUIRED"
                
                # Map DTD attribute type to data type
                if attr_type == "CDATA":
                    data_type = DataType.STRING
                elif attr_type == "ID":
                    data_type = DataType.UUID
                    if attr_name not in primary_keys:
                        primary_keys.append(attr_name)
                elif attr_type in ["IDREF", "IDREFS"]:
                    data_type = DataType.STRING
                elif attr_type in ["NMTOKEN", "NMTOKENS"]:
                    data_type = DataType.STRING
                else:
                    data_type = DataType.STRING
                
                # Extract constraints
                constraints = []
                
                # Required constraint
                if is_required:
                    constraints.append(
                        FieldConstraint(
                            type="required",
                            value=True,
                            description="Attribute is required (#REQUIRED)"
                        )
                    )
                
                # Default value constraint
                if attr_default and attr_default not in ["#REQUIRED", "#IMPLIED", "#FIXED"]:
                    # Strip quotes from default value
                    default_value = attr_default.strip('"\'')
                    constraints.append(
                        FieldConstraint(
                            type="default",
                            value=default_value,
                            description=f"Default value: {default_value}"
                        )
                    )
                
                field_info = FieldInfo(
                    name=attr_name,
                    path=field_path,
                    data_type=data_type,
                    nullable=not is_required,
                    description=None,
                    constraints=constraints,
                    metadata={
                        "dtd_type": attr_type,
                        "is_attribute": True,
                        "parent_element": element_name,
                    }
                )
                
                fields.append(field_info)
        
        return fields, primary_keys

    def _infer_schema_from_xml(self, root) -> Tuple[List[FieldInfo], List[str]]:
        """
        Infer schema from XML structure.
        
        Args:
            root: XML root element
            
        Returns:
            Tuple[List[FieldInfo], List[str]]: Fields and primary keys
        """
        fields = []
        primary_keys = []
        processed_paths = set()
        
        # Helper function to determine element path
        def get_element_path(element, parent_path=""):
            tag = element.tag
            if '}' in tag:
                tag = tag.split('}', 1)[1]
            if parent_path:
                return f"{parent_path}.{tag}"
            return tag
        
        # Helper function to infer data type
        def infer_type(value: str) -> DataType:
            if not value or value.strip() == "":
                return DataType.STRING
            
            # Try to infer type from the value
            try:
                int(value)
                return DataType.INTEGER
            except ValueError:
                try:
                    float(value)
                    return DataType.FLOAT
                except ValueError:
                    if value.lower() in ('true', 'false'):
                        return DataType.BOOLEAN
                    
                    # Check for date/datetime patterns
                    if re.match(r'\d{4}-\d{2}-\d{2}$', value):
                        return DataType.DATE
                    
                    if re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', value):
                        return DataType.DATETIME
                    
                    return DataType.STRING
        
        # Process all elements in the tree
        elements_to_process = [(root, "")]
        
        while elements_to_process:
            element, parent_path = elements_to_process.pop()
            element_path = get_element_path(element, parent_path)
            
            # Skip if already processed this path
            if element_path in processed_paths:
                continue
            
            processed_paths.add(element_path)
            
            # Process element text
            if element.text and element.text.strip():
                data_type = infer_type(element.text.strip())
                
                # Add field for element text
                fields.append(FieldInfo(
                    name=element.tag.split('}')[-1] if '}' in element.tag else element.tag,
                    path=element_path,
                    data_type=data_type,
                    nullable=True,
                    description=f"Element text content",
                    constraints=[],
                    metadata={
                        "is_element": True,
                        "has_children": len(element) > 0,
                    },
                    sample_values=[element.text.strip()],
                ))
            
            # Process attributes
            for attr_name, attr_value in element.attrib.items():
                # Handle namespaced attributes
                if '}' in attr_name:
                    attr_name = attr_name.split('}', 1)[1]
                    
                attr_path = f"{element_path}@{attr_name}"
                data_type = infer_type(attr_value)
                
                # Check if this could be a primary key
                is_key = attr_name.lower() in ['id', 'key', 'primarykey', 'primary_key'] or \
                         (attr_name.lower().endswith('id') and len(attr_name) > 2)
                if is_key and attr_name not in primary_keys:
                    primary_keys.append(attr_name)
                
                # Add field for attribute
                fields.append(FieldInfo(
                    name=attr_name,
                    path=attr_path,
                    data_type=data_type,
                    nullable=False,  # Attributes are generally not nullable
                    description=f"Attribute of element {element_path}",
                    constraints=[],
                    metadata={
                        "is_attribute": True,
                        "parent_element": element_path,
                    },
                    sample_values=[attr_value],
                ))
            
            # Queue child elements for processing
            for child in element:
                elements_to_process.append((child, element_path))
        
        return fields, primary_keys

    def _identify_record_elements(self, root) -> List[Any]:
        """
        Identify record elements in XML.
        
        Args:
            root: XML root element
            
        Returns:
            List[Any]: List of record elements
        """
        # Find potential record elements by looking for repeated elements with the same tag
        element_counts = defaultdict(int)
        parent_map = {}
        
        # Build parent map and count elements by tag
        for parent in root.findall('.//*'):
            for child in parent:
                element_counts[child.tag] += 1
                parent_map[child] = parent
        
        # Find the most frequent element tags
        if not element_counts:
            return []
            
        # Sort by frequency
        sorted_elements = sorted(element_counts.items(), key=lambda x: x[1], reverse=True)
        most_common_tag, count = sorted_elements[0]
        
        if count < 2:
            # No repeated elements found
            return []
        
        # Find elements with the most common tag
        record_elements = root.findall(f'.//*[@tag="{most_common_tag}"]')
        if not record_elements:
            # Try a different approach for ElementTree
            record_elements = []
            for element in root.findall('.//*'):
                if element.tag == most_common_tag:
                    record_elements.append(element)
        
        return record_elements

    def _element_to_dict(self, element) -> Dict[str, Any]:
        """
        Convert XML element to dictionary.
        
        Args:
            element: XML element
            
        Returns:
            Dict[str, Any]: Dictionary representation of the element
        """
        result = {}
        
        # Add tag
        tag = element.tag
        if '}' in tag:
            tag = tag.split('}', 1)[1]
        result['_tag'] = tag
        
        # Add attributes
        for attr_name, attr_value in element.attrib.items():
            # Handle namespaced attributes
            if '}' in attr_name:
                attr_name = attr_name.split('}', 1)[1]
            result[f'@{attr_name}'] = attr_value
        
        # Add text content if present
        if element.text and element.text.strip():
            result['_text'] = element.text.strip()
        
        # Group child elements by tag
        children_by_tag = defaultdict(list)
        for child in element:
            child_tag = child.tag
            if '}' in child_tag:
                child_tag = child_tag.split('}', 1)[1]
            children_by_tag[child_tag].append(child)
        
        # Process children by tag
        for tag, children in children_by_tag.items():
            if len(children) == 1:
                # Single child element with this tag
                child_dict = self._element_to_dict(children[0])
                if child_dict:  # Only add non-empty children
                    result[tag] = child_dict
            else:
                # Multiple child elements with same tag - make a list
                result[tag] = [self._element_to_dict(child) for child in children]
        
        return result


# Register the plugin
def register_plugin():
    """Register the XML parser plugin."""
    return {
        "format_id": "xml",
        "parser": XMLParser(),
        "priority": 40,  # Medium priority
        "description": "XML and XSD schema parser",
        "format_info": {
            "id": "xml",
            "name": "XML",
            "description": "eXtensible Markup Language",
            "mime_types": ["application/xml", "text/xml", "application/xsd"],
            "extensions": [".xml", ".xsd", ".svg", ".rss", ".xhtml", ".kml"],
            "capabilities": {
                "schema_extraction": True,
                "type_inference": True,
                "relationship_detection": True,
                "streaming": False,
            },
            "examples": ["<?xml", "<root>", "<!DOCTYPE", "<xs:schema"],
            "schema_type": "hierarchical",
            "version": "1.0",
        }
    }
