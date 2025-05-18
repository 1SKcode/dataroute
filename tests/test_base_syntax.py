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
    """Много целей с одинаковым именем"""
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


class TestVoidField:
    """Проверка void-полей (пустые скобки)"""
    def test_void_field(self):
        test_case = """
        source=dict/my_dict
        target1=dict/my_new_dict
        target1:
            [] -> |*func1()| -> [$d](int)
            [] -> [A](int)
            [] -> [B](int)
        """
        expected_result = {
            "dict/my_new_dict": {
                "sourse_type": {"type": "dict", "name": "my_dict"},
                "target_type": {"type": "dict", "name": "my_new_dict"},
                "routes": {
                    "__void1": {
                        "pipeline": {
                            "1": {
                                "type": "py_func",
                                "param": "",
                                "full_str": "*func1()"
                            }
                        },
                        "final_type": "int",
                        "final_name": "$d"
                    },
                    "__void2": {
                        "pipeline": None,
                        "final_type": "int",
                        "final_name": "A"
                    },
                    "__void3": {
                        "pipeline": None,
                        "final_type": "int",
                        "final_name": "B"
                    }
                }
            }
        }
        dtrt = DataRoute(test_case, debug=True, lang="ru", color=True)
        result = dtrt.go()
        assert result == expected_result


class TestVoidTargetField:
    """Проверка маршрутов с пустым target-полем ([]() и [])"""
    def test_void_target_field(self):
        test_case = """
        source=dict/my_dict
        target1=dict/my_new_dict
        target1:
            [A] -> []()
            [B] -> []
        """
        expected_result = {
            "dict/my_new_dict": {
                "sourse_type": {"type": "dict", "name": "my_dict"},
                "target_type": {"type": "dict", "name": "my_new_dict"},
                "routes": {
                    "A": {
                        "pipeline": None,
                        "final_type": None,
                        "final_name": None
                    },
                    "B": {
                        "pipeline": None,
                        "final_type": None,
                        "final_name": None
                    }
                }
            }
        }
        dtrt = DataRoute(test_case, debug=True, lang="ru", color=True)
        result = dtrt.go()
        assert result == expected_result


class TestParamThisEquivalence:
    """Параметр $this для |*s1|, |*s1($C)|, |*s1($this)|"""
    def test_param_this_equivalence(self):
        test_case = """
        source=dict/my_dict
        target1=dict/my_new_dict
        target1:
            [A] -> |*s1| -> [B](str)
            [C] -> |*s1($C)| -> [D](str)
            [E] -> |*s1($this)| -> [F](str)
        """
        expected_result = {
            "dict/my_new_dict": {
                "sourse_type": {"type": "dict", "name": "my_dict"},
                "target_type": {"type": "dict", "name": "my_new_dict"},
                "routes": {
                    "A": {
                        "pipeline": {
                            "1": {
                                "type": "py_func",
                                "param": "$this",
                                "full_str": "*s1"
                            }
                        },
                        "final_type": "str",
                        "final_name": "B"
                    },
                    "C": {
                        "pipeline": {
                            "1": {
                                "type": "py_func",
                                "param": "$this",
                                "full_str": "*s1($C)"
                            }
                        },
                        "final_type": "str",
                        "final_name": "D"
                    },
                    "E": {
                        "pipeline": {
                            "1": {
                                "type": "py_func",
                                "param": "$this",
                                "full_str": "*s1($this)"
                            }
                        },
                        "final_type": "str",
                        "final_name": "F"
                    }
                }
            }
        }
        dtrt = DataRoute(test_case, debug=True, lang="ru", color=True)
        result = dtrt.go()
        assert result == expected_result, "param должен быть $this для всех трёх вариантов"


class TestExternalVarInPythonParams:
    """Проверка передачи внешних переменных и литералов в параметры python-функции"""
    def test_external_var_in_python_params(self):
        test_case = """
        source=dict/my_dict
        target1=dict/my_new_dict
        target1:
            [A] -> |*func1($$myvars.items, $$myvars.name)|-> [B](str)
            [C] -> |*func1(\"test\", 1000, True)|-> [D](str)
        """
        expected_result = {
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
                    "A": {
                        "pipeline": {
                            "1": {
                                "type": "py_func",
                                "param": '["one", "two", "three"], test',
                                "full_str": "*func1($$myvars.items, $$myvars.name)"
                            }
                        },
                        "final_type": "str",
                        "final_name": "B"
                    },
                    "C": {
                        "pipeline": {
                            "1": {
                                "type": "py_func",
                                "param": '\"test\", 1000, True',
                                "full_str": '*func1("test", 1000, True)'
                            }
                        },
                        "final_type": "str",
                        "final_name": "D"
                    }
                }
            }
        }
        dtrt = DataRoute(test_case, vars_folder="tests/ext_vars", debug=True, lang="ru", color=True)
        result = dtrt.go()
        assert result == expected_result


class TestGlobalVarInPythonParams:
    """Проверка подстановки глобальных переменных в параметры python-функций и условия"""
    def test_global_var_in_python_params(self):
        test_case = """
        source=dict/my_dict
        target1=dict/my_new_dict
        $myvar = 1000
        $myvar2 = "test"
        target1:
            [a] -> |*func1($myvar)|-> [b](str)
            [A] -> |IF($myvar2 == "test"): *func1($myvar) ELSE: *s1($myvar2)|-> [B](str)
        """
        expected_result = {
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
                    "a": {
                        "pipeline": {
                            "1": {
                                "type": "py_func",
                                "param": "1000",
                                "full_str": "*func1($myvar)"
                            }
                        },
                        "final_type": "str",
                        "final_name": "b"
                    },
                    "A": {
                        "pipeline": {
                            "1": {
                                "type": "condition",
                                "sub_type": "if_else",
                                "full_str": "IF($myvar2 == \"test\"): *func1($myvar) ELSE: *s1($myvar2)",
                                "if": {
                                    "exp": {
                                        "type": "cond_exp",
                                        "full_str": "test == \"test\""
                                    },
                                    "do": {
                                        "type": "py_func",
                                        "param": "1000",
                                        "full_str": "*func1($myvar)"
                                    }
                                },
                                "else": {
                                    "do": {
                                        "type": "py_func",
                                        "param": "test",
                                        "full_str": "*s1($myvar2)"
                                    }
                                }
                            }
                        },
                        "final_type": "str",
                        "final_name": "B"
                    }
                }
            },
            "global_vars": {
                "myvar": {
                    "type": "int",
                    "value": 1000
                },
                "myvar2": {
                    "type": "str",
                    "value": "test"
                }
            }
        }
        dtrt = DataRoute(test_case, debug=True, lang="ru", color=True)
        result = dtrt.go()
        assert result == expected_result, f"Неверный результат для теста с глобальными переменными!\n{result}"


