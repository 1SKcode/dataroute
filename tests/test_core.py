"""
Тесты для модуля core.
"""

import pytest

from dataroute import DataRoute


def test_data_route_initialization():
    """Тест инициализации класса DataRoute."""
    route = DataRoute()
    assert route.config == {}

    custom_config = {"param": "value"}
    route_with_config = DataRoute(config=custom_config)
    assert route_with_config.config == custom_config


def test_process_data():
    """Тест метода process_data."""
    route = DataRoute()
    
    # Тест с Dict
    test_data = {"key": "value"}
    result = route.process_data(test_data)
    assert result["status"] == "success"
    assert result["processed_data"] == test_data
    
    # Тест с List[Dict]
    test_data_list = [{"key1": "value1"}, {"key2": "value2"}]
    result = route.process_data(test_data_list)
    assert result["status"] == "success"
    assert result["processed_data"] == test_data_list 