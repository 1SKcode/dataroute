import pytest
from dataroute import DataRoute
from dataroute.localization import Messages


class TestBaseDSL:

    @staticmethod
    def get_message(message_dict, lang="ru"):
        """Вспомогательная функция для получения локализованного сообщения"""
        return message_dict.get(lang, message_dict.get("ru", ""))
    
    def run_test(self, capsys, test_case, error_msg, hint_msg):
        """Общий метод для запуска и проверки тестов с ошибками DSL"""
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
        
        # Проверяем наличие сообщения об ошибке и подсказки
        assert expected_error in output, f"Ожидаемое сообщение об ошибке не найдено: {expected_error}"
        assert expected_hint in output, f"Ожидаемая подсказка не найдена: {expected_hint}"


class TestFlowDirection(TestBaseDSL):
    """Направление потока"""
    
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "missing_arrow",
            """
            source=dict
            target1=dict("target_new")
            target1:
                [pointA]  [pointB](str)
            """
        ),
        (
            "invalid_arrow",
            """
            source=dict
            target1=dict("target_new")
            target1:
                [pointA] > [pointB](str)
                [pointC] [pointD](int)
            """
        ),
    ])
    def test_flow_direction_errors(self, capsys, test_id, test_case):
        """Направление потока в DSL"""
        self.run_test(
            capsys, 
            test_case, 
            Messages.Error.FLOW_DIRECTION,
            Messages.Hint.USE_FLOW_SYMBOL
        )


class TestPipelineSyntax(TestBaseDSL):
    """Pipeline"""
    
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "missing_closing_bar_single",
            """
            source=dict
            target1=dict("target_new")
            target1:
                [pointA] -> |*func1 -> [pointB](str)
            """
        ),
        (
            "missing_closing_bar_multiple",
            """
            source=dict
            target1=dict("target_new")
            target1:
                [pointA] -> |*func1|*func2|*func3 -> [pointB](str)
            """
        ),
    ])
    def test_pipeline_errors(self, capsys, test_id, test_case):
        """pipeline в DSL"""
        self.run_test(
            capsys, 
            test_case, 
            Messages.Error.PIPELINE_CLOSING_BAR,
            Messages.Hint.ADD_CLOSING_BAR
        )


class TestBracketSyntax(TestBaseDSL):
    """Скобки"""
    
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "missing_closing_point_bracket",
            """
            source=dict
            target1=dict("target_new")
            target1:
                [pointA -> [pointB](str)
            """
        ),
        (
            "missing_opening_point_bracket",
            """
            source=dict
            target1=dict("target_new")
            target1:
                pointA] -> [pointB](str)
            """
        ),
        (
            "missing_opening_target_bracket",
            """
            source=dict
            target1=dict("target_new")
            target1:
                [pointA] -> pointB](str)
            """
        ),
        (
            "missing_closing_type_bracket",
            """
            source=dict
            target1=dict("target_new")
            target1:
                [pointA] -> [pointB(str)
            """
        ),
    ])
    def test_bracket_errors(self, capsys, test_id, test_case):
        """Тест на ошибки в скобках в DSL"""
        self.run_test(
            capsys, 
            test_case, 
            Messages.Error.BRACKET_MISSING,
            Messages.Hint.CHECK_BRACKETS
        )


class TestTypeSyntax(TestBaseDSL):
    """Типы"""
    
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "missing_type",
            """
            source=dict
            target1=dict("target_new")
            target1:
                [pointA] -> [pointB]
            """
        ),
        (
            "empty_type_open",
            """
            source=dict
            target1=dict("target_new")
            target1:
                [pointA] -> [pointB](
            """
        ),
        (
            "empty_type_close",
            """
            source=dict
            target1=dict("target_new")
            target1:
                [pointA] -> [pointB])
            """
        ),
        (
            "incomplete_type",
            """
            source=dict
            target1=dict("target_new")
            target1:
                [pointA] -> [pointB](str
            """
        ),
        (
            "malformed_complex_type",
            """
            source=dict
            target1=dict("target_new")
            target1:
                [pointA] -> [pointB](bool(
            """
        ),
        (
            "pipeline_missing_type",
            """
            source=dict
            target1=dict("target_new")
            $var1 = "test"

            target1:
                [pointA] -> |*func1($var1)| -> [pointB]
            """
        ),
    ])
    def test_type_errors(self, capsys, test_id, test_case):
        """Типы в DSL"""
        self.run_test(
            capsys, 
            test_case, 
            Messages.Error.FINAL_TYPE,
            Messages.Hint.SPECIFY_TYPE
        )


class TestExamples(TestBaseDSL):
    """Примеры и демонстрация вывода"""

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
        assert True