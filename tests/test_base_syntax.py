import pytest
from dataroute import DataRoute
from dataroute.localization import Messages


class TestBaseSyntax:
    """Тесты на проверку базового синтаксиса DSL"""

    @staticmethod
    def get_message(message_dict, lang="ru"):
        """Вспомогательная функция для получения локализованного сообщения"""
        return message_dict.get(lang, message_dict.get("ru", ""))

    @pytest.mark.parametrize(
        "test_case, error_msg, hint_msg", 
        [
            (
                """
                source=dict
                target1=dict("target_new")
                target1:
                    [pointA]  [pointB](str)
                """, 
                Messages.Error.FLOW_DIRECTION,
                Messages.Hint.USE_FLOW_SYMBOL
            ),
            (
                """
                source=dict
                target1=dict("target_new")
                target1:
                    [pointA] > [pointB](str)
                    [pointC] [pointD](int)
                """, 
                Messages.Error.FLOW_DIRECTION,
                Messages.Hint.USE_FLOW_SYMBOL
            ),
            (
                """
                source=dict
                target1=dict("target_new")
                target1:
                    [pointA] -> |*func1 -> [pointB](str)
                """, 
                Messages.Error.PIPELINE_CLOSING_BAR,
                Messages.Hint.ADD_CLOSING_BAR
            ),
            (
                """
                source=dict
                target1=dict("target_new")
                target1:
                    [pointA] -> |*func1|*func2|*func3 -> [pointB](str)
                """, 
                Messages.Error.PIPELINE_CLOSING_BAR,
                Messages.Hint.ADD_CLOSING_BAR
            ),
            (
                """
                source=dict
                target1=dict("target_new")
                target1:
                    [pointA -> [pointB](str)
                """, 
                Messages.Error.BRACKET_MISSING,
                Messages.Hint.CHECK_BRACKETS
            ),
            (
                """
                source=dict
                target1=dict("target_new")
                target1:
                    pointA] -> [pointB](str)
                """, 
                Messages.Error.BRACKET_MISSING,
                Messages.Hint.CHECK_BRACKETS
            ),
            (
                """
                source=dict
                target1=dict("target_new")
                target1:
                    [pointA] -> pointB](str)
                """, 
                Messages.Error.BRACKET_MISSING,
                Messages.Hint.CHECK_BRACKETS
            ),
            (
                """
                source=dict
                target1=dict("target_new")
                target1:
                    [pointA] -> [pointB(str)
                """, 
                Messages.Error.BRACKET_MISSING,
                Messages.Hint.CHECK_BRACKETS
            ),
            (
                """
                source=dict
                target1=dict("target_new")
                target1:
                    [pointA] -> [pointB]
                """, 
                Messages.Error.FINAL_TYPE,
                Messages.Hint.SPECIFY_TYPE
            ),
            (
                """
                source=dict
                target1=dict("target_new")
                target1:
                    [pointA] -> [pointB](
                """, 
                Messages.Error.FINAL_TYPE,
                Messages.Hint.SPECIFY_TYPE
            ),
            (
                """
                source=dict
                target1=dict("target_new")
                target1:
                    [pointA] -> [pointB])
                """, 
                Messages.Error.FINAL_TYPE,
                Messages.Hint.SPECIFY_TYPE
            ),
            (
                """
                source=dict
                target1=dict("target_new")
                target1:
                    [pointA] -> [pointB](str
                """, 
                Messages.Error.FINAL_TYPE,
                Messages.Hint.SPECIFY_TYPE
            ),
            (
                """
                source=dict
                target1=dict("target_new")
                target1:
                    [pointA] -> [pointB](bool(
                """, 
                Messages.Error.FINAL_TYPE,
                Messages.Hint.SPECIFY_TYPE
            )
        ],
        ids=["missing_direction1", "missing_direction2",
            "missing_pipeline_closing_bar1", "missing_pipeline_closing_bar2", 
            "bracket_missing1", "bracket_missing2", "bracket_missing3", "bracket_missing4",
            "final_type1", "final_type2", "final_type3", "final_type4", "final_type5"]
    )
    def test_dsl_errors(self, capsys, test_case, error_msg, hint_msg):
        """Тест на различные вариации ошибок в DSL"""
        # Получаем ожидаемые сообщения на русском
        expected_error = self.get_message(error_msg, "ru")
        expected_hint = self.get_message(hint_msg, "ru")
        
        # Удаляем ANSI-коды форматирования для получения чистого текста
        for code in [">R<", ">RS<", ">G<", ">GREEN<", ">Y<", ">RESET<", ">BOLD<"]:
            expected_error = expected_error.replace(code, "")
            expected_hint = expected_hint.replace(code, "")
        
        with pytest.raises(SystemExit) as excinfo:
            dtrt = DataRoute(test_case, debug=True, lang="ru", color=False)
            dtrt.go()

        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        output = captured.out + captured.err
        
        # Выводим захваченный вывод для отладки
        print("\n----- Вывод программы: -----")
        print(output)
        print("----- Конец вывода -----\n")
        
        # Проверяем наличие сообщения об ошибке и подсказки
        assert expected_error in output, f"Ожидаемое сообщение об ошибке не найдено: {expected_error}"
        assert expected_hint in output, f"Ожидаемая подсказка не найдена: {expected_hint}"

    def test_show_actual_error_example(self, capsys):
        """Тест для демонстрации фактического вывода программы"""
        test_input = """
        source=dict
        target1=dict("target_new")
        target1:
            [pointA] -> [pointB]
        """
        
        try:
            dtrt = DataRoute(test_input, debug=True, lang="ru", color=False)
            dtrt.go()
        except SystemExit:
            pass  # Игнорируем исключение для демонстрации вывода
            
        captured = capsys.readouterr()
        print("\n===== ФАКТИЧЕСКИЙ ВЫВОД ПРОГРАММЫ =====")
        print(captured.out)
        print("===== ВЫВОД ОШИБОК =====")
        print(captured.err)
        print("===== КОНЕЦ ВЫВОДА =====")
        
        # Этот тест всегда проходит, его цель - просто показать вывод
        assert True