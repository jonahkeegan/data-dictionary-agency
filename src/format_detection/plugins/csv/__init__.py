"""
CSV format parser plugin.
"""
import logging
import csv
import io
from typing import Any, Dict, List, Optional, Set, Tuple

from src.format_detection.models import (
    DataType,
    FieldConstraint,
    FieldInfo,
    FormatType,
    SchemaDetails,
)

logger = logging.getLogger(__name__)


class CSVParser:
    """Parser for CSV/TSV files."""
    
    def can_parse(self, filename: str, content: bytes) -> bool:
        """
        Check if the file content can be parsed as CSV.
        
        Args:
            filename: Name of the file
            content: File content
            
        Returns:
            bool: True if the content appears to be CSV, False otherwise
        """
        if not content:
            return False
            
        # Check file extension
        if filename:
            extension = filename.lower().split('.')[-1]
            if extension in ['csv', 'tsv', 'txt']:
                return True
        
        # Try to parse a sample
        try:
            sample = content[:4096].decode('utf-8', errors='ignore')
            
            # Check for common CSV patterns
            lines = sample.split('\n')
            if len(lines) > 1:
                # Check if it has a consistent number of delimiters per line
                comma_counts = [line.count(',') for line in lines if line.strip()]
                tab_counts = [line.count('\t') for line in lines if line.strip()]
                
                # Check if comma or tab separated
                if (len(comma_counts) > 1 and len(set(comma_counts[:3])) == 1 and comma_counts[0] > 0):
                    return True
                if (len(tab_counts) > 1 and len(set(tab_counts[:3])) == 1 and tab_counts[0] > 0):
                    return True
            
            return False
        except:
            return False

    def get_format_type(self) -> FormatType:
        """
        Get the format type handled by this parser.
        
        Returns:
            FormatType: The format type for CSV
        """
        return FormatType.CSV

    def parse_schema(self, filename: str, content: bytes) -> SchemaDetails:
        """
        Parse CSV content and extract schema details.
        
        Args:
            filename: Name of the file
            content: File content
            
        Returns:
            SchemaDetails: Extracted schema details
        """
        try:
            # Detect dialect and header
            text = content.decode('utf-8', errors='replace')
            dialect, has_header = self._detect_dialect(text)
            
            # Parse the content
            reader = csv.reader(io.StringIO(text), dialect=dialect)
            rows = list(reader)
            
            if not rows:
                return SchemaDetails(fields=[], metadata={"schema_type": "csv", "source_file": filename})
            
            # Extract headers and data
            headers = rows[0] if has_header else [f"col_{i+1}" for i in range(len(rows[0]))]
            data_rows = rows[1:] if has_header else rows
            
            # Create field info for each column
            fields = []
            for i, header in enumerate(headers):
                # Get column values
                column_values = [row[i] for row in data_rows if i < len(row)]
                
                # Infer data type
                data_type = self._infer_data_type(column_values)
                
                # Extract constraints
                constraints = []
                
                # Create field info
                field_info = FieldInfo(
                    name=header,
                    path=header,
                    data_type=data_type,
                    nullable=True,  # CSV fields are generally nullable
                    description=None,
                    constraints=constraints,
                    metadata={
                        "column_index": i,
                    },
                    sample_values=column_values[:5] if column_values else None
                )
                
                fields.append(field_info)
            
            # Get schema metadata
            metadata = {
                "schema_type": "csv",
                "source_file": filename,
                "has_header": has_header,
                "dialect": {
                    "delimiter": dialect.delimiter,
                    "quotechar": dialect.quotechar,
                    "escapechar": dialect.escapechar,
                    "doublequote": dialect.doublequote,
                    "skipinitialspace": dialect.skipinitialspace,
                },
                "row_count": len(rows),
                "column_count": len(headers),
            }
            
            return SchemaDetails(
                fields=fields,
                metadata=metadata
            )
                
        except Exception as e:
            logger.error(f"Error parsing CSV schema: {str(e)}")
            # Return an empty schema in case of error
            return SchemaDetails(
                fields=[],
                metadata={
                    "schema_type": "csv",
                    "source_file": filename,
                    "error": str(e)
                }
            )

    def extract_sample_data(self, filename: str, content: bytes, max_records: int = 10) -> List[Dict[str, Any]]:
        """
        Extract sample data from CSV content.
        
        Args:
            filename: Name of the file
            content: File content
            max_records: Maximum number of records to extract
            
        Returns:
            List[Dict[str, Any]]: Sample record structures
        """
        try:
            # Detect dialect and header
            text = content.decode('utf-8', errors='replace')
            dialect, has_header = self._detect_dialect(text)
            
            # Parse the content
            reader = csv.reader(io.StringIO(text), dialect=dialect)
            rows = list(reader)
            
            if not rows:
                return []
            
            # Extract headers and data
            headers = rows[0] if has_header else [f"col_{i+1}" for i in range(len(rows[0]))]
            data_rows = rows[1:] if has_header else rows
            
            # Create sample records
            samples = []
            for row in data_rows[:max_records]:
                record = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        record[header] = row[i]
                    else:
                        record[header] = None
                samples.append(record)
            
            return samples
            
        except Exception as e:
            logger.error(f"Error extracting CSV sample data: {str(e)}")
            return [{"error": str(e)}]

    def _detect_dialect(self, text: str) -> Tuple[csv.Dialect, bool]:
        """
        Detect CSV dialect and whether it has a header.
        
        Args:
            text: CSV text content
            
        Returns:
            Tuple[csv.Dialect, bool]: Detected dialect and header flag
        """
        # Use csv.Sniffer to detect dialect and header
        sniffer = csv.Sniffer()
        sample = text[:4096]  # Use a sample for performance
        
        try:
            dialect = sniffer.sniff(sample)
            has_header = sniffer.has_header(sample)
        except:
            # Fallback to default dialect
            dialect = csv.excel
            
            # Try to detect header by checking if first row looks like headers
            lines = sample.split('\n')
            has_header = False
            
            if len(lines) > 1:
                first_row = lines[0].split(dialect.delimiter)
                second_row = lines[1].split(dialect.delimiter) if len(lines) > 1 else []
                
                # Check if first row has string-like headers
                has_header = self._looks_like_header(first_row, second_row)
        
        return dialect, has_header

    def _looks_like_header(self, first_row: List[str], second_row: List[str]) -> bool:
        """
        Check if the first row looks like a header row.
        
        Args:
            first_row: First row of data
            second_row: Second row of data
            
        Returns:
            bool: True if first row looks like a header, False otherwise
        """
        if not first_row or not second_row:
            return False
            
        # Check if first row has more text-like values and second row has more numeric values
        first_numeric = sum(1 for cell in first_row if self._is_numeric(cell))
        second_numeric = sum(1 for cell in second_row if self._is_numeric(cell))
        
        # Check if header has more text and second row more numbers
        if first_numeric < second_numeric:
            return True
            
        # Check for header-like naming patterns
        header_patterns = ['id', 'name', 'key', 'date', 'code', 'type', 'category']
        matches = sum(1 for cell in first_row if any(pattern in cell.lower() for pattern in header_patterns))
        
        return matches > 0

    def _is_numeric(self, value: str) -> bool:
        """
        Check if a value is numeric.
        
        Args:
            value: String value to check
            
        Returns:
            bool: True if the value is numeric, False otherwise
        """
        try:
            float(value)
            return True
        except:
            return False

    def _infer_data_type(self, values: List[str]) -> DataType:
        """
        Infer the data type from a list of values.
        
        Args:
            values: List of string values
            
        Returns:
            DataType: Inferred data type
        """
        if not values:
            return DataType.STRING
            
        # Remove empty values for type inference
        values = [v for v in values if v]
        if not values:
            return DataType.STRING
            
        # Try to infer types
        int_count = sum(1 for v in values if self._is_integer(v))
        float_count = sum(1 for v in values if self._is_float(v) and not self._is_integer(v))
        bool_count = sum(1 for v in values if self._is_boolean(v))
        date_count = sum(1 for v in values if self._is_date(v))
        
        # Determine the most common type
        total = len(values)
        int_ratio = int_count / total if total > 0 else 0
        float_ratio = float_count / total if total > 0 else 0
        bool_ratio = bool_count / total if total > 0 else 0
        date_ratio = date_count / total if total > 0 else 0
        
        # Use a threshold for type assignment
        if int_ratio > 0.7:
            return DataType.INTEGER
        elif (int_ratio + float_ratio) > 0.7:
            return DataType.FLOAT
        elif bool_ratio > 0.7:
            return DataType.BOOLEAN
        elif date_ratio > 0.7:
            return DataType.DATE
            
        # Default to string
        return DataType.STRING

    def _is_integer(self, value: str) -> bool:
        """
        Check if a value is an integer.
        
        Args:
            value: String value to check
            
        Returns:
            bool: True if the value is an integer, False otherwise
        """
        try:
            int(value)
            return True
        except:
            return False

    def _is_float(self, value: str) -> bool:
        """
        Check if a value is a float.
        
        Args:
            value: String value to check
            
        Returns:
            bool: True if the value is a float, False otherwise
        """
        try:
            float(value)
            return True
        except:
            return False

    def _is_boolean(self, value: str) -> bool:
        """
        Check if a value is a boolean.
        
        Args:
            value: String value to check
            
        Returns:
            bool: True if the value is a boolean, False otherwise
        """
        return value.lower() in ('true', 'false', 'yes', 'no', '1', '0', 't', 'f', 'y', 'n')

    def _is_date(self, value: str) -> bool:
        """
        Check if a value is a date.
        
        Args:
            value: String value to check
            
        Returns:
            bool: True if the value is a date, False otherwise
        """
        import re
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # ISO format (yyyy-mm-dd)
            r'\d{2}/\d{2}/\d{4}',  # US format (mm/dd/yyyy)
            r'\d{2}\.\d{2}\.\d{4}',  # European format (dd.mm.yyyy)
        ]
        
        return any(re.match(pattern, value) for pattern in date_patterns)


# Register the plugin
def register_plugin():
    """Register the CSV parser plugin."""
    return {
        "format_id": "csv",
        "parser": CSVParser(),
        "priority": 50,  # Medium priority
        "description": "CSV/TSV parser",
        "format_info": {
            "id": "csv",
            "name": "CSV",
            "description": "Comma-Separated Values",
            "mime_types": ["text/csv", "text/tab-separated-values"],
            "extensions": [".csv", ".tsv", ".txt"],
            "capabilities": {
                "schema_extraction": True,
                "type_inference": True,
                "relationship_detection": False,
                "streaming": True,
            },
            "examples": [",", "comma-separated", "tabular data"],
            "schema_type": "tabular",
            "version": "1.0",
        }
    }
