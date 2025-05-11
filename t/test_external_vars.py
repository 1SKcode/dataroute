#!/usr/bin/env python3
from dataroute import DataRoute
import os
import json
import tempfile
import shutil

# Тест для проверки внешних переменных ($$)
code_with_external = """
sourse=dict

target1=dict("target_new")

target1:
    [name] -> |*normalize_name($$config.app.name)| -> [norm_name](str)
    [age] -> |*check_age($$config.app.settings.maxItems)| -> [norm_age](int)
    [score] -> |*validate_score($$config.app.settings.debug)| -> [valid_score](bool)
    [data] -> |*transform_data($$config.database.credentials.username)| -> [user_data](str)
"""

# Создаем временную папку с тестовыми JSON файлами
def create_test_vars():
    temp_dir = tempfile.mkdtemp()
    
    # Создаем тестовый JSON файл
    config_data = {
        "app": {
            "name": "TestApp",
            "version": "1.0.0",
            "settings": {
                "debug": True,
                "maxItems": 100,
                "features": ["search", "filter", "sort"]
            }
        },
        "database": {
            "host": "localhost",
            "port": 5432,
            "credentials": {
                "username": "admin",
                "password": "secret"
            }
        }
    }
    
    with open(os.path.join(temp_dir, "config.json"), "w") as f:
        json.dump(config_data, f)
    
    return temp_dir

def test_external_vars():
    """Тестирует обработку внешних переменных"""
    print("\n=== Тест: Внешние переменные ===")
    
    # Создаем временную папку с тестовыми данными
    vars_folder = create_test_vars()
    
    try:
        # Создаем экземпляр DataRoute с путем к папке переменных
        dtrt = DataRoute(code_with_external, vars_folder=vars_folder, debug=True, lang="ru", color=True)
        result = dtrt.go()
        dtrt.print_json()
        
        # Проверяем наличие параметров с переменными
        routes = result.get("target_new", {}).get("routes", {})
        
        print("\nПроверка использования внешних переменных в пайплайнах:")
        for field, route_info in routes.items():
            pipeline = route_info.get("pipeline", {})
            for step, step_info in pipeline.items():
                param = step_info.get("param", "")
                is_external = step_info.get("is_external_var", False)
                print(f"Поле: {field}, шаг: {step}, параметр: {param}, внешняя: {is_external}")
        
        # Проверяем правильность флагов и параметров
        name_pipeline = routes.get("name", {}).get("pipeline", {}).get("1", {})
        age_pipeline = routes.get("age", {}).get("pipeline", {}).get("1", {})
        score_pipeline = routes.get("score", {}).get("pipeline", {}).get("1", {})
        data_pipeline = routes.get("data", {}).get("pipeline", {}).get("1", {})
        
        success = (
            name_pipeline.get("param") == "$$config.app.name" and 
            name_pipeline.get("is_external_var") == True and
            age_pipeline.get("param") == "$$config.app.settings.maxItems" and 
            age_pipeline.get("is_external_var") == True and
            score_pipeline.get("param") == "$$config.app.settings.debug" and 
            score_pipeline.get("is_external_var") == True and
            data_pipeline.get("param") == "$$config.database.credentials.username" and 
            data_pipeline.get("is_external_var") == True
        )
        
        if success:
            print("\n✓ Тест успешно пройден: внешние переменные обработаны правильно")
        else:
            print("\n✗ Тест провален: ошибка в обработке внешних переменных")
        
        return result
    finally:
        # Удаляем временную папку
        shutil.rmtree(vars_folder)

if __name__ == "__main__":
    test_external_vars() 