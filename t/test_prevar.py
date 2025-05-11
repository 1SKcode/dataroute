#!/usr/bin/env python3
from dataroute import DataRoute

# Тест для проверки пре-переменных 
# Должно корректно распознавать $^name для доступа к исходным значениям
code_with_prevars = """
sourse=dict

target1=dict("target_new")

target1:
    [name] -> |*normalize_name| -> [norm_name](str)
    [score] -> |*validate_score($^name)| -> [valid_score](bool)
"""

def test_prevars():
    """Тестирует обработку пре-переменных"""
    print("\n=== Тест: Пре-переменные ===")
    dtrt = DataRoute(code_with_prevars, debug=True, lang="ru", color=True)
    result = dtrt.go()
    dtrt.print_json()
    
    routes = result.get("target_new", {}).get("routes", {})
    
    # Проверяем второй пайплайн с параметром $^name
    score_route = routes.get("score", {})
    score_pipeline = score_route.get("pipeline", {}).get("1", {})
    
    # Выводим результаты проверки
    print("\nПроверка пре-переменных:")
    print(f"score_pipeline param: {score_pipeline.get('param')}")
    print(f"is_pre_var: {score_pipeline.get('is_pre_var')}")
    
    # Проверяем правильность параметров
    success = (score_pipeline.get('param') == "$^name" and 
               score_pipeline.get('is_pre_var') == True)
    
    if success:
        print("\n✓ Тест успешно пройден: пре-переменные обработаны правильно")
    else:
        print("\n✗ Тест провален: ошибка в обработке пре-переменных")
    
    return result

if __name__ == "__main__":
    test_prevars() 