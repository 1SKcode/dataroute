#!/usr/bin/env python3
from dataroute import DataRoute

# Тест для проверки параметров в пайплайнах
# Должно корректно обрабатывать переменные в параметрах функций
code_with_params = """
sourse=dict

target1=dict("target_new")

target1:
    [name] -> |*normalize_name| -> [norm_name](str)
    [age] -> |*check_age($this)| -> [norm_age](int)
    [score] -> |*validate_score($age)| -> [valid_score](bool)
"""

def test_params():
    """Тестирует обработку параметров функций с переменными"""
    print("\n=== Тест: Параметры функций с переменными ===")
    dtrt = DataRoute(code_with_params, debug=True, lang="ru", color=True)
    result = dtrt.go()
    dtrt.print_json()
    
    routes = result.get("target_new", {}).get("routes", {})
    
    # Проверяем первый пайплайн (по умолчанию должен быть $this)
    name_route = routes.get("name", {})
    name_pipeline = name_route.get("pipeline", {}).get("1", {})
    
    # Проверяем второй пайплайн (явный $this)
    age_route = routes.get("age", {})
    age_pipeline = age_route.get("pipeline", {}).get("1", {})
    
    # Проверяем третий пайплайн (переменная $age)
    score_route = routes.get("score", {})
    score_pipeline = score_route.get("pipeline", {}).get("1", {})
    
    # Выводим результаты проверок
    print("\nПроверка параметров:")
    print(f"1. name_pipeline param: {name_pipeline.get('param')}")
    print(f"2. age_pipeline param: {age_pipeline.get('param')}")
    print(f"3. score_pipeline param: {score_pipeline.get('param')}")
    
    # Проверяем правильность параметров
    success = (name_pipeline.get('param') == "$this" and 
               age_pipeline.get('param') == "$this" and 
               score_pipeline.get('param') == "$age")
    
    if success:
        print("\n✓ Тест успешно пройден: параметры обработаны правильно")
    else:
        print("\n✗ Тест провален: ошибка в обработке параметров")
    
    return result

if __name__ == "__main__":
    test_params() 