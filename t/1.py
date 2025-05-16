import json
from dataroute import DataRoute


def main():
    test_input = """
        source=dict/my_dict
        target2=postgres/my_new_dict
        target1=dict/my_new_dict
        target1:
            [pointA] -> |IF(1): *func5()| -> [$s](int)
        target2:
            [pointA] -> |*func1()| -> [$s](int)
            
            """
    dtrt = DataRoute(test_input, vars_folder="my_vars", func_folder="my_funcs", debug=True, lang="ru", color=True)
    result = dtrt.go()
    print("\nСгенерированная JSON структура:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()




