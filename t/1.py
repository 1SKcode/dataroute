import json
from dataroute import DataRoute


def main():
    test_input = """
                source=dict
                target1=dict("target_new")
                target1:
                    [pointA] -> [pointB](str)
                """
    dtrt = DataRoute(test_input, vars_folder="my_vars", debug=True, lang="ru", color=True)
    result = dtrt.go()
    print("\nСгенерированная JSON структура:")
    dtrt.print_json()

if __name__ == "__main__":
    main()
    