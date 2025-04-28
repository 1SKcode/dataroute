import json
import sys
import os

# Добавляем родительский каталог в путь поиска модулей
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dataroute import parse_dsl


def main():
    correct_input = """
sourse=dict

target2=postgres("parser.norm_data")
target1=dict("target_new")

target1:
    [id] -> [external_id](str)
    [name] => |*lower| - [low_name](str)
    [age] - |*check_age| -> [age](int)
    [test1] -> [test_NORM](str)

target2:
    [id] -> |id| -> [id](str)
    [name] -> |*s1|*upper| -> [name](str)
    [] -> |*gen_rand_int| -> [score](int)
    [] -> |*gen_rand_int| -> [score2](int)
"""


    result = parse_dsl(correct_input, debug=True, lang="ru")

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main() 