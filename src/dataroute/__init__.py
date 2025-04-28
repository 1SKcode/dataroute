"""
DataRoute - библиотека для [описание назначения].
"""

from dataroute.dataroute import (
    parse_dsl,
    parse_dsl_file,
    parse_dsl_to_json,
    parse_dsl_file_to_json,
    DataRouteParser
)
from dataroute.localization import set_language

__version__ = "0.2.0"
__all__ = [
    "parse_dsl",
    "parse_dsl_file",
    "parse_dsl_to_json", 
    "parse_dsl_file_to_json",
    "DataRouteParser",
    "set_language"
] 