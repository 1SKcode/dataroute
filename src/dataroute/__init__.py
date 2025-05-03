"""
dataroute - Гибкая ETL-система на Python с DSL для построения маршрутов и трансформаций данных.
"""

from .dataroute import parse_dsl, parse_dsl_file, parse_dsl_to_json, parse_dsl_file_to_json

__all__ = ['parse_dsl', 'parse_dsl_file', 'parse_dsl_to_json', 'parse_dsl_file_to_json']