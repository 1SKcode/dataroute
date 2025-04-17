"""
Файл setup.py для обратной совместимости с предыдущими версиями инструментов сборки.
Рекомендуется использовать pyproject.toml для настройки проекта.
"""

from setuptools import setup

setup(
    # Используйте pyproject.toml для настройки проекта
    name="dataroute",
    package_dir={"": "src"},
) 