#!/usr/bin/env python3
"""
Демонстрация всех нововведений в DataRoute:
- Внешние переменные ($$var)
- Пре-переменные ($^var)
- Глобальные переменные ($var)
"""

import os
import json
import tempfile
import shutil
from src.dataroute import DataRoute


def setup_vars_folder():
    """Создает временную папку с конфигурационными файлами для внешних переменных"""
    temp_dir = tempfile.mkdtemp()
    
    # Создаем конфигурационный файл app.json
    app_config = {
        "name": "TestApp",
        "version": "1.0.0",
        "settings": {
            "maxItems": 100,
            "debug": True,
            "environment": "dev"
        }
    }
    
    # Создаем конфигурационный файл database.json
    db_config = {
        "credentials": {
            "username": "admin",
            "password": "secret",
            "host": "localhost",
            "port": 5432
        },
        "pool": {
            "max_connections": 10,
            "timeout": 30
        }
    }
    
    # Записываем файлы
    with open(os.path.join(temp_dir, "app.json"), "w") as f:
        json.dump(app_config, f, indent=2)
    
    with open(os.path.join(temp_dir, "database.json"), "w") as f:
        json.dump(db_config, f, indent=2)
    
    print(f"Созданы конфигурационные файлы в папке: {temp_dir}")
    return temp_dir


def demonstrate_all_features(vars_folder):
    """Демонстрация всех возможностей DataRoute"""
    
    # Пример 1: Использование внешних переменных
    print("\n=== Пример 1: Внешние переменные ===")
    code1 = """
# Пример использования внешних переменных
source=dict
target_out=dict("output")

target_out:
    [name] -> |*normalize_name($$app.name)| -> [app_name](str)
    [version] -> |*get_version($$app.version)| -> [app_version](str)
    [max_items] -> |*check_limit($$app.settings.maxItems)| -> [limit](int)
    [username] -> |*transform_username($$database.credentials.username)| -> [user](str)
"""
    
    # Создаем экземпляр DataRoute и запускаем обработку
    dtrt1 = DataRoute(code1, vars_folder=vars_folder, debug=False, lang="ru", color=True)
    result1 = dtrt1.go()
    print("\nРезультат в JSON:")
    dtrt1.print_json()
    
    # Пример 2: Использование пре-переменных
    print("\n=== Пример 2: Пре-переменные ===")
    code2 = """
# Пример использования пре-переменных
source=dict
target_out=dict("output")

target_out:
    [first_name] -> |*normalize_name| -> [norm_first_name](str)
    [last_name] -> |*normalize_name| -> [norm_last_name](str)
    [full_name] -> |*combine_names($^norm_first_name, $^norm_last_name)| -> [full_name](str)
    [id] -> |*generate_id| -> [user_id](str)
    [meta] -> |*create_metadata($^user_id, $^full_name)| -> [metadata](dict)
"""
    
    # Создаем экземпляр DataRoute и запускаем обработку
    dtrt2 = DataRoute(code2, vars_folder=vars_folder, debug=False, lang="ru", color=True)
    result2 = dtrt2.go()
    print("\nРезультат в JSON:")
    dtrt2.print_json()
    
    # Пример 3: Использование глобальных переменных
    print("\n=== Пример 3: Глобальные переменные ===")
    code3 = """
# Пример использования глобальных переменных
source=dict
target_out=dict("output")

# Определяем глобальные переменные
$appPrefix = "APP_"
$dbPrefix = "DB_"
$separator = "::"
$defaultType = "string"

target_out:
    [name] -> |*add_prefix($appPrefix)| -> [prefixed_name](str)
    [db_name] -> |*add_prefix($dbPrefix)| -> [prefixed_db](str)
    [combined] -> |*combine_fields($prefixed_name, $prefixed_db, $separator)| -> [combined_value](str)
    [type] -> |*set_default($defaultType)| -> [value_type](str)
"""
    
    # Создаем экземпляр DataRoute и запускаем обработку
    dtrt3 = DataRoute(code3, vars_folder=vars_folder, debug=False, lang="ru", color=True)
    result3 = dtrt3.go()
    print("\nРезультат в JSON:")
    dtrt3.print_json()
    
    # Пример 4: Комбинированное использование всех типов переменных
    print("\n=== Пример 4: Комбинирование всех типов переменных ===")
    code4 = """
# Комбинированное использование всех типов переменных
source=dict
target_out=dict("output")

# Глобальные переменные
$prefix = "USER_"
$suffix = "_DATA"
$format = "json"

target_out:
    [username] -> |*transform_username($$database.credentials.username)| -> [user](str)
    [app_name] -> |*get_app_name($$app.name)| -> [app](str)
    [combined] -> |*format_combined($prefix, $^user, $^app, $suffix)| -> [result](str)
    [db_host] -> |*get_host($$database.credentials.host)| -> [host](str)
    [db_port] -> |*get_port($$database.credentials.port)| -> [port](int)
    [output_type] -> |*set_format($format)| -> [format](str)
"""
    
    # Создаем экземпляр DataRoute и запускаем обработку
    dtrt4 = DataRoute(code4, vars_folder=vars_folder, debug=False, lang="ru", color=True)
    result4 = dtrt4.go()
    print("\nРезультат в JSON:")
    dtrt4.print_json()
    
    return vars_folder


def cleanup(temp_dir):
    """Удаляет временную директорию"""
    shutil.rmtree(temp_dir)
    print(f"\nВременная директория удалена: {temp_dir}")


if __name__ == "__main__":
    # Настройка окружения
    vars_folder = setup_vars_folder()
    
    try:
        # Запуск демонстрации
        demonstrate_all_features(vars_folder)
    finally:
        # Очистка
        cleanup(vars_folder) 