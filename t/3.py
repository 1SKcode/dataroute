import json
from dataroute import DataRoute


def main():
    test_input = """
        lang=py
        source=dict/my_dict
        target1=postgres/dtrt_test.newtable
        target1:
            [A] -> [B](str)
            [C] -> |IF($this == 1): *s1| -> [D](str)
            [E] -> |IF($D == "1"): ROLLBACK("Такое будем роллбэкать")| -> [F](str)
            [G] -> |IF($D == "1"): *func1 ELSE: SKIP("Произошел пропуск")| -> [H](str)
            [K] -> |IF($D == "1"): *func1 ELIF($D == "3"): *s1 ELSE: NOTIFY("Прсто уведомление")| -> [L](str)
        """
    dtrt = DataRoute(test_input, vars_folder="t/my_vars", func_folder="t/my_funcs", debug=True, lang="ru", color=True)
    result = dtrt.compile_ic()
    print(json.dumps(result, indent=2, ensure_ascii=False))

    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
if __name__ == "__main__":
    main()