import json
from dataroute import DataRoute


def main():
    test_input = """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointD] -> |*func1($s)| -> [$pointB](int)
                [pointA] -> |*func1| -> [$pointC](int)
                """
    dtrt = DataRoute(test_input, vars_folder="my_vars", debug=True, lang="ru", color=True)
    result = dtrt.go()
    print("\nСгенерированная JSON структура:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()