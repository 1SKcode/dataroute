import json
from dataroute import DataRoute


def main():
    test_input = """
            lang=py
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> || -> [pointB](int)
        """
    dtrt = DataRoute(test_input, vars_folder="t/my_vars", func_folder="t/my_funcs", debug=True, lang="ru", color=True)
    result = dtrt.compile_ic()
    print(json.dumps(result, indent=2, ensure_ascii=False))

    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
if __name__ == "__main__":
    main()