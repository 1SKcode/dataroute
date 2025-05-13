import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """Фикстура для настройки окружения перед всеми тестами"""
    yield