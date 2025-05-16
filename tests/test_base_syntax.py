import pytest
import json
from dataroute import DataRoute
from dataroute.localization import Messages


class TestValidBaseSyntax():
    """Проверка корректного синтаксиса и результатов"""
    
    @pytest.mark.parametrize("test_id, test_case, expected_result", [
        (
            "case1",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> [pointB](str)
                [pointC] - [pointD](int)
                [pointE] > [pointF](bool)
                [pointG] >> [pointH](float)
                [pointI] => [pointJ](str)
            """,
            {
                "dict/my_new_dict": {
                    "sourse_type": {
                    "type": "dict",
                    "name": "my_dict"
                    },
                    "target_type": {
                    "type": "dict",
                    "name": "my_new_dict"
                    },
                    "routes": {
                        "pointA": {
                            "pipeline": None,
                            "final_type": "str",
                            "final_name": "pointB"
                        },
                        "pointC": {
                            "pipeline": None,
                            "final_type": "int",
                            "final_name": "pointD"
                        },
                        "pointE": {
                            "pipeline": None,
                            "final_type": "bool",
                            "final_name": "pointF"
                        },
                        "pointG": {
                            "pipeline": None,
                            "final_type": "float",
                            "final_name": "pointH"
                        },
                        "pointI": {
                            "pipeline": None,
                            "final_type": "str",
                            "final_name": "pointJ"
                        }
                    }
                }
            }
        ),
    ], ids=["case1"])
    def test_valid_dsl(self, test_id, test_case, expected_result):
        """Проверка корректного DSL и генерации правильного JSON"""
        dtrt = DataRoute(test_case, debug=True, lang="ru", color=True)
        result = dtrt.go()
        
        # Получаем JSON и сравниваем с ожидаемым результатом
        assert result == expected_result, f"Неверный результат для теста: {test_id}"
        
        # Дополнительная проверка, что print_json не выдает ошибку
        dtrt.print_json()


class TestDoubleTarget:
    """Простой двойной таргет: dict/my_new_dict и postgres/my_new_dict"""
    def test_case1(self):
        test_case = """
        source=dict/my_dict
        target2=postgres/my_new_dict
        target1=dict/my_new_dict
        target1:
            [pointA] -> |*func1()| -> [$s](int)
        target2:
            [pointA] -> |*func1()| -> [$s](int)
        """
        expected_result = {
            "dict/my_new_dict": {
                "sourse_type": {"type": "dict", "name": "my_dict"},
                "target_type": {"type": "dict", "name": "my_new_dict"},
                "routes": {
                    "pointA": {
                        "pipeline": {
                            "1": {
                                "type": "py_func",
                                "param": "",
                                "external_var": {"is_external_var": False, "value": None},
                                "full_str": "*func1()"
                            }
                        },
                        "final_type": "int",
                        "final_name": "$s"
                    }
                }
            },
            "postgres/my_new_dict": {
                "sourse_type": {"type": "dict", "name": "my_dict"},
                "target_type": {"type": "postgres", "name": "my_new_dict"},
                "routes": {
                    "pointA": {
                        "pipeline": {
                            "1": {
                                "type": "py_func",
                                "param": "",
                                "external_var": {"is_external_var": False, "value": None},
                                "full_str": "*func1()"
                            }
                        },
                        "final_type": "int",
                        "final_name": "$s"
                    }
                }
            }
        }
        dtrt = DataRoute(test_case, debug=True, lang="ru", color=True)
        result = dtrt.go()
        assert result == expected_result


class TestManyTargets:
    """Много целей с одинаковым именем, но разными типами"""
    def test_many_targets(self):
        test_case = """
        source=dict/my_dict
        target1=postgres1/my_new_dict
        target2=postgres2/my_new_dict
        target3=postgres3/my_new_dict
        target4=postgres4/my_new_dict
        target5=postgres5/my_new_dict
        target6=postgres6/my_new_dict
        target7=postgres7/my_new_dict
        target8=postgres8/my_new_dict
        target9=postgres9/my_new_dict
        target10=postgres10/my_new_dict
        target1:
            [pointA] -> |*func1()| -> [$s](int)
        target2:
            [pointA] -> |*func1()| -> [$s](int)
        target3:
            [pointA] -> |*func1()| -> [$s](int)
        target4:
            [pointA] -> |*func1()| -> [$s](int)
        target5:
            [pointA] -> |*func1()| -> [$s](int)
        target6:
            [pointA] -> |*func1()| -> [$s](int)
        target7:
            [pointA] -> |*func1()| -> [$s](int)
        target8:
            [pointA] -> |*func1()| -> [$s](int)
        target9:
            [pointA] -> |*func1()| -> [$s](int)
        target10:
            [pointA] -> |*func1()| -> [$s](int)
        """
        expected_result = {
            f"postgres{i}/my_new_dict": {
                "sourse_type": {"type": "dict", "name": "my_dict"},
                "target_type": {"type": f"postgres{i}", "name": "my_new_dict"},
                "routes": {
                    "pointA": {
                        "pipeline": {
                            "1": {
                                "type": "py_func",
                                "param": "",
                                "external_var": {"is_external_var": False, "value": None},
                                "full_str": "*func1()"
                            }
                        },
                        "final_type": "int",
                        "final_name": "$s"
                    }
                }
            } for i in range(1, 11)
        }
        dtrt = DataRoute(test_case, debug=True, lang="ru", color=True)
        result = dtrt.go()
        assert result == expected_result


