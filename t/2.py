import json
import sys
from dataroute import DataRoute

class ExitIntercepted(Exception):
    pass

def fake_exit(code=1):
    raise ExitIntercepted()

def run_test(title, dsl_code):
    print(f"<<<---{title}--->>>")
    print("Результат:")
    real_exit = sys.exit
    sys.exit = fake_exit
    try:
        dtrt = DataRoute(dsl_code, debug=False, lang="ru", color=True)
        result = dtrt.go()
        dtrt.print_json()
        return True
    except ExitIntercepted:
        # Ошибка уже напечатана внутри DataRoute
        return False
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return False
    finally:
        sys.exit = real_exit

def main():
    # Корректный пример для сравнения
    correct_input = """
source=dict
target1=dict("target_new")

target1:
    [id] -> [external_id](str)
"""
    
    # 1. Ошибка символа направления потока (FLOW_DIRECTION)
    error_flow_direction = """
source=dict
target1=dict("target_new")

target1:
    [id] [external_id](str)
"""
    
    # 2. Отсутствие закрывающей черты пайплайна (PIPELINE_CLOSING_BAR)
    error_pipeline_closing_bar = """
source=dict
target1=dict("target_new")

target1:
    [id] -> | *transform [external_id](str)
"""
    
    # 3. Ошибка с квадратными скобками (BRACKET_MISSING)
    error_bracket_missing = """
source=dict
target1=dict("target_new")

target1:
    [id] -> external_id](str)
"""
    
    # 4. Ошибка финального типа (FINAL_TYPE)
    error_final_type = """
source=dict
target1=dict("target_new")

target1:
    [id] -> [external_id]
"""
    
    # 5. Ошибка синтаксиса источника (SYNTAX_SOURCE)
    error_syntax_source = """
source dict
target1=dict("target_new")

target1:
    [id] -> [external_id](str)
"""
    
    # 6. Ошибка синтаксиса цели (SYNTAX_TARGET)
    error_syntax_target = """
source=dict
target1=dict["target_new"]

target1:
    [id] -> [external_id](str)
"""
    
    # 7. Пустой пайплайн (PIPELINE_EMPTY)
    error_pipeline_empty = """
source=dict
target1=dict("target_new")

target1:
    [id] -> || -> [external_id](str)
"""
    
    # 8. Ошибка семантики маршрутов (SEMANTIC_ROUTES)
    error_semantic_routes = """
source=dict
target1=dict("target_new")
"""
    
    # 9. Ошибка семантики цели (SEMANTIC_TARGET)
    error_semantic_target = """
source=dict
target1=dict("target_new")

target2:
    [id] -> [external_id](str)
"""
    
    # 10. Ошибка указания типа для void-поля (VOID_TYPE)
    error_void_type = """
source=dict
target1=dict("target_new")

target1:
    [] -> |*lower| -> [](int)
"""
    
    # Запуск тестов
    run_test("0. Корректный пример", correct_input)
    run_test("1. Ошибка символа направления потока (FLOW_DIRECTION)", error_flow_direction)
    run_test("2. Отсутствие закрывающей черты пайплайна (PIPELINE_CLOSING_BAR)", error_pipeline_closing_bar)
    run_test("3. Ошибка с квадратными скобками (BRACKET_MISSING)", error_bracket_missing)
    run_test("4. Ошибка финального типа (FINAL_TYPE)", error_final_type)
    run_test("5. Ошибка синтаксиса источника (SYNTAX_SOURCE)", error_syntax_source)
    run_test("6. Ошибка синтаксиса цели (SYNTAX_TARGET)", error_syntax_target)
    run_test("7. Пустой пайплайн (PIPELINE_EMPTY)", error_pipeline_empty)
    run_test("8. Ошибка семантики маршрутов (SEMANTIC_ROUTES)", error_semantic_routes)
    run_test("9. Ошибка семантики цели (SEMANTIC_TARGET)", error_semantic_target)
    run_test("10. Ошибка указания типа для void-поля (VOID_TYPE)", error_void_type)


if __name__ == "__main__":
    main() 