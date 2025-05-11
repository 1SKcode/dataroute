#!/usr/bin/env python3
from dataroute import DataRoute

# Тест для проверки глобальных переменных
code_with_globals = """
sourse=dict

# Глобальные переменные различных типов
$myVar1 = "Тестовая строка"
$myVar2 = 42
$myVar3 = 12.34
$myVar4 = True

target1=dict("target_new")

target1:
    [name] -> |*normalize_name| -> [norm_name](str)
    [age] -> |*check_age($myVar2)| -> [norm_age](int)
    [score] -> |*validate_score($myVar3)| -> [valid_score](bool)
"""

def test_globals():
    """Тестирует обработку глобальных переменных"""
    print("\n=== Тест: Глобальные переменные ===")
    dtrt = DataRoute(code_with_globals, debug=True, lang="ru", color=True)
    result = dtrt.go()
    dtrt.print_json()
    
    # Проверяем наличие глобальных переменных в результате
    global_vars = result.get("global_vars", {})
    
    # Проверяем количество объявленных переменных
    vars_count = len(global_vars)
    print(f"\nОбъявлено переменных: {vars_count}")
    
    # Проверяем типы переменных
    print("\nТипы переменных:")
    for var_name, var_data in global_vars.items():
        print(f"${var_name}: {var_data.get('type')} = {var_data.get('value')}")
    
    # Проверяем использование переменных в параметрах функций
    routes = result.get("target_new", {}).get("routes", {})
    age_pipeline = routes.get("age", {}).get("pipeline", {}).get("1", {})
    score_pipeline = routes.get("score", {}).get("pipeline", {}).get("1", {})
    
    print("\nИспользование переменных в пайплайнах:")
    print(f"age_pipeline param: {age_pipeline.get('param')}")
    print(f"score_pipeline param: {score_pipeline.get('param')}")
    
    # Проверяем правильность
    success = (vars_count == 4 and 
               age_pipeline.get('param') == "$myVar2" and 
               score_pipeline.get('param') == "$myVar3")
    
    if success:
        print("\n✓ Тест успешно пройден: глобальные переменные обработаны правильно")
    else:
        print("\n✗ Тест провален: ошибка в обработке глобальных переменных")
    
    return result

# Тест на проверку ошибки дублирования имен переменных
code_with_duplicate = """
sourse=dict

$myVar1 = "Первое значение"
$myVar1 = "Дублирующееся значение"

target1=dict("target_new")

target1:
    [name] -> |*test| -> [result](str)
"""

def test_duplicate_error():
    """Тестирует ошибку с дублированием имен переменных"""
    print("\n=== Тест: Ошибка дублирования переменных ===")
    try:
        dtrt = DataRoute(code_with_duplicate, debug=True, lang="ru", color=True)
        result = dtrt.go()
        print("ОШИБКА: Тест должен был завершиться исключением!")
        return False
    except SystemExit:
        print("Тест успешно вызвал ошибку дублирования переменных, как и ожидалось.")
        return True

if __name__ == "__main__":
    test_globals()
    print("\n" + "-" * 50 + "\n")
    test_duplicate_error() 