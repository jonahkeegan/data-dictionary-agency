"""
Format detection plugins registry.
"""
import logging
from typing import Dict, List, Type

# Import all plugins
from src.format_detection.plugins.avro import register_plugin as register_avro
from src.format_detection.plugins.csv import register_plugin as register_csv
from src.format_detection.plugins.json import register_plugin as register_json
from src.format_detection.plugins.sql import register_plugin as register_sql
from src.format_detection.plugins.xml import register_plugin as register_xml
from src.format_detection.plugins.yaml import register_plugin as register_yaml

# Import new plugins
from src.format_detection.plugins.graphql import register_plugin as register_graphql
from src.format_detection.plugins.json_schema import register_plugin as register_json_schema
from src.format_detection.plugins.openapi import register_plugin as register_openapi
from src.format_detection.plugins.parquet import register_plugin as register_parquet
from src.format_detection.plugins.protobuf import register_plugin as register_protobuf
from src.format_detection.plugins.orc import register_plugin as register_orc

logger = logging.getLogger(__name__)

def register_plugins() -> Dict:
    """Register all format detection plugins.
    
    Returns:
        Dict: A dictionary mapping format IDs to parser instances.
    """
    plugins = {}
    
    # Register each plugin
    plugin_registrars = [
        # Existing parsers
        register_avro,
        register_csv,
        register_json,
        register_sql,
        register_xml,
        register_yaml,
        
        # New parsers
        register_graphql,
        register_json_schema,
        register_openapi,
        register_parquet,
        register_protobuf,
        register_orc,
    ]
    
    for register_func in plugin_registrars:
        try:
            plugin_info = register_func()
            format_id = plugin_info["format_id"]
            
            if format_id in plugins:
                logger.warning(f"Duplicate plugin registration for format: {format_id}. Overwriting.")
            
            plugins[format_id] = plugin_info
            logger.info(f"Registered plugin for format: {format_id}")
        except Exception as e:
            logger.error(f"Failed to register plugin {register_func.__name__}: {str(e)}")
    
    logger.info(f"Registered {len(plugins)} format detection plugins")
    return plugins
