import json
from dataroute import DataRoute


def main():
    test_input = """
            lang=python
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] ->  [pointB](str)
            """
    dtrt = DataRoute(test_input, vars_folder="my_vars", func_folder="my_funcs", debug=True, lang="ru", color=True)
    result = dtrt.go()
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()