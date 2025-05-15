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
                "my_new_dict": {
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
    ], 
    ids=["case1"])
    def test_valid_dsl(self, test_id, test_case, expected_result):
        """Проверка корректного DSL и генерации правильного JSON"""
        dtrt = DataRoute(test_case, debug=True, lang="ru", color=True)
        result = dtrt.go()
        
        # Получаем JSON и сравниваем с ожидаемым результатом
        assert result == expected_result, f"Неверный результат для теста: {test_id}"
        
        # Дополнительная проверка, что print_json не выдает ошибку
        dtrt.print_json()


