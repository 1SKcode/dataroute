import json
from dataroute import DataRoute


def main():
    correct_input = """
source=dict

target1=dict("target_new")
target2=postgres("parser.norm_data")

target1:
    [id] -> [external_id]()
    [name] => |*lower|*upper|*func1|*func2| - [low_name](str)
    [age] - |*check_age| -> []
    [score] - |*validate_score| -> []()
    [test1] -> [test_NORM](str)

target2:
    [id] -> |id| -> [id](str)
    [name] -> |*s1|*upper| -> [name](str)
    [] -> |*gen_rand_int| -> [score](int)
    [] -> |*gen_rand_int| -> [score2](int)
"""
# нужно сделать обработку для $ и $$ переменных в ф-иях
# Добавить разложение в json на более подробные структуры
    err1 = "ewrwe.dtrt"

    print("=== Тестирование пустых целевых полей ===")
    dtrt = DataRoute(correct_input, debug=False, lang="ru", color=True)
    result = dtrt.go()
    dtrt.print_json()

if __name__ == "__main__":
    main()
    