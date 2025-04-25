"""
SQL DDL format detection plugin.
"""
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from src.format_detection.models import DataType, FieldConstraint, FieldInfo, SchemaDetails

logger = logging.getLogger(__name__)

class SQLParser:
    """Parser for SQL DDL format."""

    def __init__(self):
        """Initialize the SQL DDL parser."""
        logger.debug("Initializing SQL DDL parser")
        
        # Common SQL keywords for DDL detection
        self.ddl_keywords = [
            "CREATE TABLE", "ALTER TABLE", "DROP TABLE",
            "CREATE VIEW", "CREATE INDEX", "CREATE SEQUENCE",
            "PRIMARY KEY", "FOREIGN KEY", "REFERENCES",
            "NOT NULL", "UNIQUE", "CHECK", "DEFAULT",
            "INT", "VARCHAR", "CHAR", "TEXT", "DATE", "TIMESTAMP", "NUMERIC", "DECIMAL", "BOOLEAN"
        ]
        
        # SQL data type mapping to our data types
        self.sql_type_mapping = {
            # Integer types
            "int": DataType.INTEGER,
            "integer": DataType.INTEGER,
            "smallint": DataType.INTEGER,
            "bigint": DataType.INTEGER,
            "tinyint": DataType.INTEGER,
            
            # Floating point types
            "float": DataType.FLOAT,
            "double": DataType.FLOAT,
            "real": DataType.FLOAT,
            "numeric": DataType.FLOAT,
            "decimal": DataType.FLOAT,
            
            # String types
            "char": DataType.STRING,
            "varchar": DataType.STRING,
            "text": DataType.STRING,
            "nvarchar": DataType.STRING,
            "nchar": DataType.STRING,
            "clob": DataType.STRING,
            
            # Boolean type
            "boolean": DataType.BOOLEAN,
            "bool": DataType.BOOLEAN,
            
            # Date and time types
            "date": DataType.DATE,
            "time": DataType.STRING,
            "timestamp": DataType.DATETIME,
            "datetime": DataType.DATETIME,
            
            # Binary types
            "blob": DataType.BINARY,
            "binary": DataType.BINARY,
            "varbinary": DataType.BINARY,
            
            # Array types
            "array": DataType.ARRAY,
            
            # Object types
            "object": DataType.OBJECT,
            "json": DataType.OBJECT,
            "jsonb": DataType.OBJECT,
        }

    def can_parse(self, content: bytes, filename: Optional[str] = None) -> Tuple[bool, float]:
        """Check if content can be parsed as SQL DDL.
        
        Args:
            content: File content.
            filename: Optional filename.
            
        Returns:
            Tuple[bool, float]: (can_parse, confidence)
        """
        # Check file extension first if filename is provided
        if filename and filename.lower().endswith(('.sql', '.ddl')):
            # High confidence based on extension
            return True, 0.9
        
        # Check content patterns
        try:
            # Try to decode the first part of the content as UTF-8
            sample = content[:10000].decode('utf-8', errors='strict').upper()
            
            # Look for SQL DDL patterns
            
            # Count SQL DDL keywords
            keyword_count = 0
            for keyword in self.ddl_keywords:
                if keyword.upper() in sample:
                    keyword_count += 1
            
            # Check for CREATE TABLE statements
            create_table_matches = re.findall(r'CREATE\s+TABLE\s+[`"\[]?(\w+)[`"\]]?', sample, re.IGNORECASE)
            
            # Check for column definitions
            column_definition = re.search(r'CREATE\s+TABLE[^(]*\(\s*\w+\s+\w+[^)]*\)', sample, re.IGNORECASE | re.DOTALL)
            
            if len(create_table_matches) > 0:
                return True, 0.95
            
            if column_definition:
                return True, 0.9
            
            if keyword_count >= 3:
                return True, 0.7
            
            if keyword_count >= 1:
                return True, 0.5
            
        except UnicodeDecodeError:
            # Not a UTF-8 text file, probably not SQL
            return False, 0.0
        
        return False, 0.0

    def parse_schema(self, content: bytes, filename: Optional[str] = None) -> SchemaDetails:
        """Extract schema information from SQL DDL content.
        
        Args:
            content: SQL DDL content.
            filename: Optional filename.
            
        Returns:
            SchemaDetails: Extracted schema details.
            
        Raises:
            ValueError: If content cannot be parsed as SQL DDL.
        """
        try:
            # Decode SQL content
            sql_content = content.decode('utf-8')
            
            # Parse tables and their schemas
            tables = self._extract_tables(sql_content)
            
            if not tables:
                logger.warning("No tables found in SQL DDL content")
                raise ValueError("No tables found in SQL DDL content")
            
            # Extract relationships between tables
            foreign_keys = self._extract_foreign_keys(sql_content, tables)
            
            # Convert tables to fields
            fields = []
            primary_keys = []
            unique_constraints = []
            indices = []
            
            # Process each table to extract its fields
            for table_name, table_info in tables.items():
                table_primary_keys = table_info.get('primary_keys', [])
                primary_keys.extend([f"{table_name}.{pk}" for pk in table_primary_keys])
                
                # Process each column in the table
                for column_name, column_info in table_info.get('columns', {}).items():
                    field_path = f"{table_name}.{column_name}"
                    
                    # Extract field constraints
                    constraints = []
                    
                    # Add NOT NULL constraint if applicable
                    if not column_info.get('nullable', True):
                        constraints.append(FieldConstraint(
                            type="not_null",
                            value=True,
                            description="NOT NULL constraint",
                        ))
                    
                    # Add DEFAULT constraint if applicable
                    default_value = column_info.get('default')
                    if default_value is not None:
                        constraints.append(FieldConstraint(
                            type="default",
                            value=default_value,
                            description=f"DEFAULT {default_value}",
                        ))
                    
                    # Add UNIQUE constraint if applicable
                    if column_info.get('unique', False):
                        constraints.append(FieldConstraint(
                            type="unique",
                            value=True,
                            description="UNIQUE constraint",
                        ))
                        
                        # Add to unique constraints list
                        unique_constraints.append([field_path])
                    
                    # Add CHECK constraint if applicable
                    check_constraint = column_info.get('check')
                    if check_constraint:
                        constraints.append(FieldConstraint(
                            type="check",
                            value=check_constraint,
                            description=f"CHECK ({check_constraint})",
                        ))
                    
                    # Add length constraint for string types
                    length = column_info.get('length')
                    if length is not None:
                        constraints.append(FieldConstraint(
                            type="length",
                            value=length,
                            description=f"Length: {length}",
                        ))
                    
                    # Add field to fields list
                    fields.append(FieldInfo(
                        name=column_name,
                        path=field_path,
                        data_type=column_info.get('data_type', DataType.UNKNOWN),
                        nullable=column_info.get('nullable', True),
                        description=column_info.get('description'),
                        constraints=constraints,
                        metadata={
                            "table": table_name,
                            "column": column_name,
                            "sql_type": column_info.get('sql_type'),
                            "is_primary_key": column_name in table_primary_keys,
                        },
                    ))
                
                # Add indexes to the indexes list
                for index_name, index_info in table_info.get('indexes', {}).items():
                    index_columns = index_info.get('columns', [])
                    indices.append({
                        "name": index_name,
                        "table": table_name,
                        "columns": index_columns,
                        "unique": index_info.get('unique', False),
                    })
            
            # Add metadata about the SQL schema
            metadata = {
                "tables_count": len(tables),
                "relationships_count": len(foreign_keys),
                "dialect": self._detect_sql_dialect(sql_content),
            }
            
            return SchemaDetails(
                fields=fields,
                primary_keys=primary_keys,
                foreign_keys=foreign_keys,
                unique_constraints=unique_constraints,
                indices=indices,
                metadata=metadata,
                dependencies=[],
            )
            
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode SQL content: {str(e)}")
            raise ValueError(f"Failed to decode SQL content: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing SQL DDL schema: {str(e)}")
            raise ValueError(f"Error parsing SQL DDL schema: {str(e)}")

    def _extract_tables(self, sql_content: str) -> Dict[str, Dict[str, Any]]:
        """Extract tables and their schemas from SQL DDL content.
        
        Args:
            sql_content: SQL DDL content.
            
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping table names to their schemas.
        """
        tables = {}
        
        # Extract CREATE TABLE statements
        create_table_pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"\[]?(\w+)[`"\]]?\s*\((.*?)\)(?:\s*ENGINE\s*=\s*\w+)?(?:\s*DEFAULT\s+CHARSET\s*=\s*\w+)?;'
        create_table_matches = re.finditer(create_table_pattern, sql_content, re.IGNORECASE | re.DOTALL)
        
        for match in create_table_matches:
            table_name = match.group(1)
            columns_definition = match.group(2)
            
            # Initialize table schema
            tables[table_name] = {
                'columns': {},
                'primary_keys': [],
                'indexes': {},
                'description': f"Table {table_name}",
            }
            
            # Extract column definitions
            self._extract_columns(columns_definition, tables[table_name])
        
        return tables

    def _extract_columns(self, columns_definition: str, table_info: Dict[str, Any]) -> None:
        """Extract column definitions from a CREATE TABLE statement.
        
        Args:
            columns_definition: Column definitions part of CREATE TABLE statement.
            table_info: Dictionary to update with column information.
        """
        # Split the columns definition by commas, but be careful with commas inside parentheses
        parts = []
        current_part = ""
        paren_level = 0
        
        for char in columns_definition:
            if char == '(' and not paren_level:
                paren_level += 1
                current_part += char
            elif char == ')' and paren_level:
                paren_level -= 1
                current_part += char
            elif char == ',' and not paren_level:
                parts.append(current_part.strip())
                current_part = ""
            else:
                current_part += char
        
        if current_part.strip():
            parts.append(current_part.strip())
        
        # Process each column or constraint definition
        for part in parts:
            # Check if it's a PRIMARY KEY constraint
            primary_key_match = re.match(r'PRIMARY\s+KEY\s*\(\s*([^)]+)\s*\)', part, re.IGNORECASE)
            if primary_key_match:
                primary_keys = [pk.strip(' `"[]') for pk in primary_key_match.group(1).split(',')]
                table_info['primary_keys'].extend(primary_keys)
                continue
            
            # Check if it's a UNIQUE constraint
            unique_match = re.match(r'UNIQUE(?:\s+KEY|\s+INDEX)?\s*(?:\w+)?\s*\(\s*([^)]+)\s*\)', part, re.IGNORECASE)
            if unique_match:
                unique_columns = [col.strip(' `"[]') for col in unique_match.group(1).split(',')]
                # Add unique constraint to each column
                for col in unique_columns:
                    if col in table_info['columns']:
                        table_info['columns'][col]['unique'] = True
                continue
            
            # Check if it's an INDEX definition
            index_match = re.match(r'(?:KEY|INDEX)\s+`?(\w+)`?\s*\(\s*([^)]+)\s*\)', part, re.IGNORECASE)
            if index_match:
                index_name = index_match.group(1)
                index_columns = [col.strip(' `"[]') for col in index_match.group(2).split(',')]
                table_info['indexes'][index_name] = {
                    'columns': index_columns,
                    'unique': False,
                }
                continue
            
            # Check if it's a FOREIGN KEY constraint
            foreign_key_match = re.match(r'FOREIGN\s+KEY\s*\(\s*([^)]+)\s*\)\s*REFERENCES\s+`?(\w+)`?\s*\(\s*([^)]+)\s*\)', part, re.IGNORECASE)
            if foreign_key_match:
                # Foreign keys will be handled in _extract_foreign_keys
                continue
            
            # Should be a column definition
            column_match = re.match(r'`?(\w+)`?\s+([^\s,]+)(?:\s*\(\s*(\d+)(?:\s*,\s*(\d+))?\s*\))?(?:\s+(.*))?', part, re.IGNORECASE)
            if column_match:
                column_name = column_match.group(1)
                sql_type = column_match.group(2).lower()
                length = column_match.group(3)
                scale = column_match.group(4)  # For numeric types like DECIMAL(10,2)
                constraints = column_match.group(5) or ""
                
                # Map SQL type to our data type
                data_type = self.sql_type_mapping.get(sql_type.lower(), DataType.UNKNOWN)
                
                # Parse column constraints
                nullable = "NOT NULL" not in constraints.upper()
                has_default = "DEFAULT" in constraints.upper()
                default_value = None
                
                if has_default:
                    default_match = re.search(r'DEFAULT\s+([^,\s]+)', constraints, re.IGNORECASE)
                    if default_match:
                        default_value = default_match.group(1)
                
                # Check for PRIMARY KEY constraint in column definition
                is_primary_key = "PRIMARY KEY" in constraints.upper()
                if is_primary_key:
                    table_info['primary_keys'].append(column_name)
                
                # Check for UNIQUE constraint in column definition
                is_unique = "UNIQUE" in constraints.upper()
                
                # Convert length to integer if present
                if length:
                    length = int(length)
                
                # Add column to table schema
                table_info['columns'][column_name] = {
                    'sql_type': sql_type,
                    'data_type': data_type,
                    'length': length,
                    'scale': scale,
                    'nullable': nullable,
                    'default': default_value,
                    'unique': is_unique,
                    'description': f"Column {column_name} of type {sql_type}",
                }

    def _extract_foreign_keys(self, sql_content: str, tables: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract foreign key relationships from SQL DDL content.
        
        Args:
            sql_content: SQL DDL content.
            tables: Dictionary mapping table names to their schemas.
            
        Returns:
            List[Dict[str, Any]]: List of foreign key relationships.
        """
        foreign_keys = []
        
        # Extract inline foreign key constraints from CREATE TABLE statements
        inline_fk_pattern = r'CREATE\s+TABLE\s+[`"\[]?(\w+)[`"\]]?.*?FOREIGN\s+KEY\s*\(\s*([^)]+)\s*\)\s*REFERENCES\s+[`"\[]?(\w+)[`"\]]?\s*\(\s*([^)]+)\s*\)'
        inline_fk_matches = re.finditer(inline_fk_pattern, sql_content, re.IGNORECASE | re.DOTALL)
        
        for match in inline_fk_matches:
            table_name = match.group(1)
            column_names = [col.strip(' `"[]') for col in match.group(2).split(',')]
            referenced_table = match.group(3)
            referenced_columns = [col.strip(' `"[]') for col in match.group(4).split(',')]
            
            # Add foreign key relationship
            foreign_keys.append({
                'table': table_name,
                'columns': column_names,
                'referenced_table': referenced_table,
                'referenced_columns': referenced_columns,
            })
        
        # Extract ALTER TABLE ADD FOREIGN KEY statements
        alter_fk_pattern = r'ALTER\s+TABLE\s+[`"\[]?(\w+)[`"\]]?\s+ADD\s+(?:CONSTRAINT\s+\w+\s+)?FOREIGN\s+KEY\s*\(\s*([^)]+)\s*\)\s*REFERENCES\s+[`"\[]?(\w+)[`"\]]?\s*\(\s*([^)]+)\s*\)'
        alter_fk_matches = re.finditer(alter_fk_pattern, sql_content, re.IGNORECASE | re.DOTALL)
        
        for match in alter_fk_matches:
            table_name = match.group(1)
            column_names = [col.strip(' `"[]') for col in match.group(2).split(',')]
            referenced_table = match.group(3)
            referenced_columns = [col.strip(' `"[]') for col in match.group(4).split(',')]
            
            # Add foreign key relationship
            foreign_keys.append({
                'table': table_name,
                'columns': column_names,
                'referenced_table': referenced_table,
                'referenced_columns': referenced_columns,
            })
        
        return foreign_keys

    def _detect_sql_dialect(self, sql_content: str) -> str:
        """Attempt to detect SQL dialect from content.
        
        Args:
            sql_content: SQL DDL content.
            
        Returns:
            str: Detected SQL dialect.
        """
        # MySQL specific patterns
        if re.search(r'ENGINE\s*=\s*(?:InnoDB|MyISAM|MEMORY)', sql_content, re.IGNORECASE):
            return "MySQL"
        
        # PostgreSQL specific patterns
        if re.search(r'SERIAL|BIGSERIAL|UUID|jsonb', sql_content, re.IGNORECASE):
            return "PostgreSQL"
        
        # SQLite specific patterns
        if re.search(r'PRAGMA|AUTOINCREMENT', sql_content, re.IGNORECASE):
            return "SQLite"
        
        # SQL Server specific patterns
        if re.search(r'IDENTITY\(\d+,\d+\)|NVARCHAR|NTEXT', sql_content, re.IGNORECASE):
            return "SQL Server"
        
        # Oracle specific patterns
        if re.search(r'NUMBER\(\d+,\d+\)|CLOB|BFILE|ROWID', sql_content, re.IGNORECASE):
            return "Oracle"
        
        # Default to standard SQL
        return "Standard SQL"

    def extract_sample_data(self, content: bytes, max_records: int = 10) -> List[Dict[str, Any]]:
        """Extract sample data from SQL DDL content.
        
        Note: SQL DDL doesn't typically contain sample data, so this method returns
        sample table structures instead.
        
        Args:
            content: SQL DDL content.
            max_records: Maximum number of records to extract.
            
        Returns:
            List[Dict[str, Any]]: Sample table structures.
            
        Raises:
            ValueError: If content cannot be parsed as SQL DDL.
        """
        try:
            # Decode SQL content
            sql_content = content.decode('utf-8')
            
            # Extract tables
            tables = self._extract_tables(sql_content)
            
            # Convert tables to sample records
            sample_records = []
            
            for table_name, table_info in list(tables.items())[:max_records]:
                # Create a sample record for each table
                table_record = {
                    "table_name": table_name,
                    "columns": {},
                    "primary_keys": table_info.get('primary_keys', []),
                    "indexes": list(table_info.get('indexes', {}).keys()),
                }
                
                # Add column information
                for column_name, column_info in table_info.get('columns', {}).items():
                    table_record["columns"][column_name] = {
                        "type": column_info.get('sql_type'),
                        "nullable": column_info.get('nullable', True),
                    }
                
                sample_records.append(table_record)
            
            return sample_records
            
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode SQL content: {str(e)}")
            raise ValueError(f"Failed to decode SQL content: {str(e)}")
        except Exception as e:
            logger.error(f"Error extracting sample data: {str(e)}")
            raise ValueError(f"Error extracting sample data: {str(e)}")


# Register the plugin
def register_plugin():
    """Register the SQL DDL parser plugin."""
    return {
        "format_id": "sql",
        "parser": SQLParser(),
        "format_info": {
            "id": "sql",
            "name": "SQL DDL",
            "description": "SQL Data Definition Language",
            "mime_types": ["application/sql", "text/sql"],
            "extensions": [".sql", ".ddl"],
            "capabilities": {
                "schema_extraction": True,
                "type_inference": True,
                "relationship_detection": True,
                "streaming": False,
            },
            "examples": ["CREATE TABLE", "ALTER TABLE", "PRIMARY KEY"],
            "schema_type": "relational",
            "version": "SQL-92",
        }
    }
