import pytest
import json
from dataroute import DataRoute
from dsl_compiler.localization import Messages


class TestValidBaseSyntax():
    """Проверка корректного синтаксиса и результатов"""
    
    @pytest.mark.parametrize("test_id, test_case, expected_result", [
        (
            "case1",
            """
            lang=py
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
                "lang": "py",
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
        lang=py
        source=dict/my_dict
        target2=postgres/my_new_dict
        target1=dict/my_new_dict
        target1:
            [pointA] -> |*func1()| -> [$s](int)
        target2:
            [pointA] -> |*func1()| -> [$s](int)
        """
        expected_result = {
            "lang": "py",
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
        lang=py
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
        expected_result = {f"postgres{i}/my_new_dict": {
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
        } for i in range(1, 11)}
        expected_result["lang"] = "py"
        dtrt = DataRoute(test_case, debug=True, lang="ru", color=True)
        result = dtrt.go()
        assert result == expected_result


class TestVoidField:
    """Проверка void-полей (пустые скобки)"""
    def test_void_field(self):
        test_case = """
        lang=py
        source=dict/my_dict
        target1=dict/my_new_dict
        target1:
            [] -> |*func1()| -> [$d](int)
            [] -> [A](int)
            [] -> [B](int)
        """
        expected_result = {
            "lang": "py",
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
        lang=py
        source=dict/my_dict
        target1=dict/my_new_dict
        target1:
            [A] -> []()
            [B] -> []
        """
        expected_result = {
            "lang": "py",
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
        lang=py
        source=dict/my_dict
        target1=dict/my_new_dict
        target1:
            [A] -> |*s1| -> [B](str)
            [C] -> |*s1($C)| -> [D](str)
            [E] -> |*s1($this)| -> [F](str)
        """
        expected_result = {
            "lang": "py",
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
        lang=py
        source=dict/my_dict
        target1=dict/my_new_dict
        target1:
            [A] -> |*func1($$myvars.items, $$myvars.name)|-> [B](str)
            [C] -> |*func1(\"test\", 1000, True)|-> [D](str)
        """
        expected_result = {
            "lang": "py",
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
        lang=py
        source=dict/my_dict
        target1=dict/my_new_dict
        $myvar = 1000
        $myvar2 = "test"
        target1:
            [a] -> |*func1($myvar)|-> [b](str)
            [A] -> |IF($myvar2 == "test"): *func1($myvar) ELSE: *s1($myvar2)|-> [B](str)
        """
        expected_result = {
            "lang": "py",
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


class TestComplexNormBlock:
    """Проверка сложного DSL для norm_data.norm_blocks"""
    def test_norm_block_dsl(self):
        test_case = """
        lang=py
        source=dict/my_dict
        norm=postgres/norm_data.norm_blocks
        $block9Floor=f49f5e6b-67f1-4596-a4f8-5f27f1f5f457
        norm:
            [block_uuid] -> [block_uuid](str)
            [is_euro] -> |*s1|IF($this IN $$mv.is_euro): *get(True) ELSE: *get(False)| -> [is_euro](bool)
            [rooms] -> |*s1|IF($block_uuid == $block9Floor AND $this == "9" OR $this == None): *get(0)| -> [rooms](str)
            [] -> |*get(\"Свободна\")| -> [status](str)
            [section] -> |*s1|IF($this == None): *get(\"Нет секции\")| -> [section_name](str)
            [price_sale] -> |*s1| -> [$price_sale](int)
            [price_base] -> |*s1|IF($price_sale != None OR $price_sale != \"0\"): *get($price_sale)| -> [price](int)
            [type] -> |*get_tag_by_type($this)| -> [tags](str)
            [area_total] -> [area_total](float)
            [area_given] -> [area_given](float)
            [area_kitchen] -> [area_kitchen](float)
            [number] -> |IF($this == None): *get(\"-\")| -> [number](str)                
            [windows] -> [windows](str)
            [window_view] -> [window_view](str)
            [view_places] -> [view_places](str)
            [floor] -> |*s1|IF($this == None): *get(0)| -> [floor_of_flat](int)   
            [floors_in_section] -> [floors_in_section](int)
            [comment] -> [comment](str)
            [plan_url] -> [plan_url](str)
            [floor_plan_url] -> [floor_plan_url](str)
            [finising] -> |*get_finishing($this)| -> [finishing](str)
            [uuid] -> [flats_uuid](str)
            [] -> |*get_flats_type_uuid($block_uuid, $rooms, $tags)| -> [flats_type_uuid](str)
            [building_uuid] -> [building_uuid](str)
            [] -> |*get_uuid_real_estate_type($tags)| -> [uuid_real_estate_type](str)
        """
        expected_result = {
            "lang": "py",
            "postgres/norm_data.norm_blocks": {
                "sourse_type": {
                    "type": "dict",
                    "name": "my_dict"
                },
                "target_type": {
                    "type": "postgres",
                    "name": "norm_data.norm_blocks"
                },
                "routes": {
                    "block_uuid": {
                        "pipeline": None,
                        "final_type": "str",
                        "final_name": "block_uuid"
                    },
                    "is_euro": {
                        "pipeline": {
                            "1": {
                                "type": "py_func",
                                "param": "$this",
                                "full_str": "*s1"
                            },
                            "2": {
                                "type": "condition",
                                "sub_type": "if_else",
                                "full_str": "IF($this IN $$mv.is_euro): *get(True) ELSE: *get(False)",
                                "if": {
                                    "exp": {
                                        "type": "cond_exp",
                                        "full_str": "$this IN [\"1\", \"true\", \"True\"]"
                                    },
                                    "do": {
                                        "type": "py_func",
                                        "param": "True",
                                        "full_str": "*get(True)"
                                    }
                                },
                                "else": {
                                    "do": {
                                        "type": "py_func",
                                        "param": "False",
                                        "full_str": "*get(False)"
                                    }
                                }
                            }
                        },
                        "final_type": "bool",
                        "final_name": "is_euro"
                    },
                    "rooms": {
                        "pipeline": {
                            "1": {
                                "type": "py_func",
                                "param": "$this",
                                "full_str": "*s1"
                            },
                            "2": {
                                "type": "condition",
                                "sub_type": "if",
                                "full_str": "IF($block_uuid == $block9Floor AND $this == \"9\" OR $this == None): *get(0)",
                                "if": {
                                    "exp": {
                                        "type": "cond_exp",
                                        "full_str": "$block_uuid == f49f5e6b-67f1-4596-a4f8-5f27f1f5f457 AND $this == \"9\" OR $this == None"
                                    },
                                    "do": {
                                        "type": "py_func",
                                        "param": "0",
                                        "full_str": "*get(0)"
                                    }
                                }
                            }
                        },
                        "final_type": "str",
                        "final_name": "rooms"
                    },
                    "__void1": {
                        "pipeline": {
                            "1": {
                                "type": "py_func",
                                "param": "\"Свободна\"",
                                "full_str": "*get(\"Свободна\")"
                            }
                        },
                        "final_type": "str",
                        "final_name": "status"
                    },
                    "section": {
                        "pipeline": {
                            "1": {
                                "type": "py_func",
                                "param": "$this",
                                "full_str": "*s1"
                            },
                            "2": {
                                "type": "condition",
                                "sub_type": "if",
                                "full_str": "IF($this == None): *get(\"Нет секции\")",
                                "if": {
                                    "exp": {
                                        "type": "cond_exp",
                                        "full_str": "$this == None"
                                    },
                                    "do": {
                                        "type": "py_func",
                                        "param": "\"Нет секции\"",
                                        "full_str": "*get(\"Нет секции\")"
                                    }
                                }
                            }
                        },
                        "final_type": "str",
                        "final_name": "section_name"
                    },
                    "price_sale": {
                        "pipeline": {
                            "1": {
                                "type": "py_func",
                                "param": "$this",
                                "full_str": "*s1"
                            }
                        },
                        "final_type": "int",
                        "final_name": "$price_sale"
                    },
                    "price_base": {
                        "pipeline": {
                            "1": {
                                "type": "py_func",
                                "param": "$this",
                                "full_str": "*s1"
                            },
                            "2": {
                                "type": "condition",
                                "sub_type": "if",
                                "full_str": "IF($price_sale != None OR $price_sale != \"0\"): *get($price_sale)",
                                "if": {
                                    "exp": {
                                        "type": "cond_exp",
                                        "full_str": "$price_sale != None OR $price_sale != \"0\""
                                    },
                                    "do": {
                                        "type": "py_func",
                                        "param": "$price_sale",
                                        "full_str": "*get($price_sale)"
                                    }
                                }
                            }
                        },
                        "final_type": "int",
                        "final_name": "price"
                    },
                    "type": {
                        "pipeline": {
                            "1": {
                                "type": "py_func",
                                "param": "$this",
                                "full_str": "*get_tag_by_type($this)"
                            }
                        },
                        "final_type": "str",
                        "final_name": "tags"
                    },
                    "area_total": {
                        "pipeline": None,
                        "final_type": "float",
                        "final_name": "area_total"
                    },
                    "area_given": {
                        "pipeline": None,
                        "final_type": "float",
                        "final_name": "area_given"
                    },
                    "area_kitchen": {
                        "pipeline": None,
                        "final_type": "float",
                        "final_name": "area_kitchen"
                    },
                    "number": {
                        "pipeline": {
                            "1": {
                                "type": "condition",
                                "sub_type": "if",
                                "full_str": "IF($this == None): *get(\"-\")",
                                "if": {
                                    "exp": {
                                        "type": "cond_exp",
                                        "full_str": "$this == None"
                                    },
                                    "do": {
                                        "type": "py_func",
                                        "param": "\"-\"",
                                        "full_str": "*get(\"-\")"
                                    }
                                }
                            }
                        },
                        "final_type": "str",
                        "final_name": "number"
                    },
                    "windows": {
                        "pipeline": None,
                        "final_type": "str",
                        "final_name": "windows"
                    },
                    "window_view": {
                        "pipeline": None,
                        "final_type": "str",
                        "final_name": "window_view"
                    },
                    "view_places": {
                        "pipeline": None,
                        "final_type": "str",
                        "final_name": "view_places"
                    },
                    "floor": {
                        "pipeline": {
                            "1": {
                                "type": "py_func",
                                "param": "$this",
                                "full_str": "*s1"
                            },
                            "2": {
                                "type": "condition",
                                "sub_type": "if",
                                "full_str": "IF($this == None): *get(0)",
                                "if": {
                                    "exp": {
                                        "type": "cond_exp",
                                        "full_str": "$this == None"
                                    },
                                    "do": {
                                        "type": "py_func",
                                        "param": "0",
                                        "full_str": "*get(0)"
                                    }
                                }
                            }
                        },
                        "final_type": "int",
                        "final_name": "floor_of_flat"
                    },
                    "floors_in_section": {
                        "pipeline": None,
                        "final_type": "int",
                        "final_name": "floors_in_section"
                    },
                    "comment": {
                        "pipeline": None,
                        "final_type": "str",
                        "final_name": "comment"
                    },
                    "plan_url": {
                        "pipeline": None,
                        "final_type": "str",
                        "final_name": "plan_url"
                    },
                    "floor_plan_url": {
                        "pipeline": None,
                        "final_type": "str",
                        "final_name": "floor_plan_url"
                    },
                    "finising": {
                        "pipeline": {
                            "1": {
                                "type": "py_func",
                                "param": "$this",
                                "full_str": "*get_finishing($this)"
                            }
                        },
                        "final_type": "str",
                        "final_name": "finishing"
                    },
                    "uuid": {
                        "pipeline": None,
                        "final_type": "str",
                        "final_name": "flats_uuid"
                    },
                    "__void2": {
                        "pipeline": {
                            "1": {
                                "type": "py_func",
                                "param": "$block_uuid, $rooms, $tags",
                                "full_str": "*get_flats_type_uuid($block_uuid, $rooms, $tags)"
                            }
                        },
                        "final_type": "str",
                        "final_name": "flats_type_uuid"
                    },
                    "building_uuid": {
                        "pipeline": None,
                        "final_type": "str",
                        "final_name": "building_uuid"
                    },
                    "__void3": {
                        "pipeline": {
                            "1": {
                                "type": "py_func",
                                "param": "$tags",
                                "full_str": "*get_uuid_real_estate_type($tags)"
                            }
                        },
                        "final_type": "str",
                        "final_name": "uuid_real_estate_type"
                    }
                }
            },
            "global_vars": {
                "block9Floor": {
                    "type": "str",
                    "value": "f49f5e6b-67f1-4596-a4f8-5f27f1f5f457"
                }
            }
        }
        dtrt = DataRoute(test_case, debug=True, func_folder="tests/ext_funcs", vars_folder="tests/ext_vars", lang="ru", color=True)
        result = dtrt.go()
        assert result == expected_result, f"Неверный результат для сложного norm_block DSL!\n{result}"
        dtrt.print_json()
        

class TestLangDirectiveSuccess:
    """Успешная обработка lang"""
    def test_lang_in_json(self):
        test_case = """
        lang=py
        source=dict/my_dict
        target1=dict/my_new_dict
        target1:
            [field] -> [field](str)
        """
        dtrt = DataRoute(test_case, debug=False, lang="ru", color=False)
        result = dtrt.go()
        assert result.get('lang') == 'py'
