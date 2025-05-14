import pytest
import sys
import os

@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """Фикстура для настройки окружения перед всеми тестами"""
    yield