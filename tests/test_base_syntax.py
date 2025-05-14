import pytest
import json
from dataroute import DataRoute
from dataroute.localization import Messages


class TestValidBaseSyntax():
    """Проверка корректного синтаксиса и результатов"""
    
    @pytest.mark.parametrize("test_id, test_case, expected_result", [
        (
            "simple_route",
            """
            source=dict
            target1=dict("target_new")
            target1:
                [pointA] -> [pointB](str)
            """,
            {
                "target_new": {
                    "sourse_type": "dict",
                    "target_type": "dict",
                    "routes": {
                        "pointA": {
                            "pipeline": None,
                            "final_type": "str",
                            "final_name": "pointB"
                        }
                    }
                }
            }
        ),
        (
            "with_pipeline",
            """
            source=dict
            target1=dict("target_new")
            target1:
                [pointA] -> |*func1| -> [pointB](str)
            """,
            {
                "target_new": {
                    "sourse_type": "dict",
                    "target_type": "dict",
                    "routes": {
                        "pointA": {
                            "pipeline": ["func1"],
                            "final_type": "str",
                            "final_name": "pointB"
                        }
                    }
                }
            }
        ),
        (
            "multiple_routes",
            """
            source=dict
            target1=dict("target_new")
            target1:
                [pointA] -> [pointB](str)
                [pointC] -> [pointD](int)
            """,
            {
                "target_new": {
                    "sourse_type": "dict",
                    "target_type": "dict",
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
                        }
                    }
                }
            }
        ),
        (
            "with_variables",
            """
            source=dict
            target1=dict("target_new")
            $var1 = "test"
            
            target1:
                [pointA] -> |*func1($var1)| -> [pointB](str)
                [pointC] -> [pointD](int)
            """,
            {
                "target_new": {
                    "sourse_type": "dict",
                    "target_type": "dict",
                    "routes": {
                        "pointA": {
                            "pipeline": ["func1('test')"],
                            "final_type": "str",
                            "final_name": "pointB"
                        },
                        "pointC": {
                            "pipeline": None,
                            "final_type": "int",
                            "final_name": "pointD"
                        }
                    }
                }
            }
        ),
    ])
    def test_valid_dsl(self, test_id, test_case, expected_result):
        """Проверка корректного DSL и генерации правильного JSON"""
        dtrt = DataRoute(test_case, debug=True, lang="ru", color=False)
        result = dtrt.go()
        
        # Получаем JSON и сравниваем с ожидаемым результатом
        assert result == expected_result, f"Неверный результат для теста: {test_id}"
        
        # Дополнительная проверка, что print_json не выдает ошибку
        dtrt.print_json()