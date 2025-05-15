import pytest
import json
from dataroute import DataRoute
from dataroute.localization import Messages


class TestBaseDSL:

    @staticmethod
    def get_message(message_dict, lang="ru"):
        """Вспомогательная функция для получения локализованного сообщения"""
        return message_dict.get(lang, message_dict.get("ru", ""))
    
    def run_test(self, capsys, test_case, error_msg, hint_msg, partial_error=None, partial_hint=None):
        """Общий метод для запуска и проверки тестов с ошибками DSL"""
        expected_error = self.get_message(error_msg, "ru") if not partial_error else None
        expected_hint = self.get_message(hint_msg, "ru") if (hint_msg and not partial_hint) else None
        # Удаляем ANSI-коды форматирования для получения чистого текста
        for code in [">R<", ">RS<", ">G<", ">GREEN<", ">Y<", ">RESET<", ">BOLD<"]:
            if expected_error:
                expected_error = expected_error.replace(code, "")
            if expected_hint:
                expected_hint = expected_hint.replace(code, "")
        
        with pytest.raises(SystemExit) as excinfo:
            dtrt = DataRoute(test_case, debug=True, lang="ru", color=False)
            dtrt.go()

        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        output = captured.out + captured.err
        
        # Проверяем наличие сообщения об ошибке и подсказки
        if partial_error:
            assert partial_error in output, f"Ожидаемое сообщение об ошибке не найдено: {partial_error}"
        else:
            assert expected_error in output, f"Ожидаемое сообщение об ошибке не найдено: {expected_error}"
        if partial_hint:
            assert partial_hint in output, f"Ожидаемая подсказка не найдена: {partial_hint}"
        elif expected_hint:
            assert expected_hint in output, f"Ожидаемая подсказка не найдена: {expected_hint}"


class TestFlowDirectionErrors(TestBaseDSL):
    """Нет символа направления"""
    
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA]  [pointB](str)
            """
        ),
        (
            "case_2",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] > [pointB](str)
                [pointC] [pointD](int)
            """
        ),
    ], ids=["case_1", "case_2"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys, 
            test_case, 
            Messages.Error.FLOW_DIRECTION,
            Messages.Hint.USE_FLOW_SYMBOL
        )


class TestPipelineSyntaxErrors(TestBaseDSL):
    """Закрывающая прямая черта пайплайна не найдена"""
    
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*func1 -> [pointB](str)
            """
        ),
        (
            "case_2",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*func1|*func2|*func3 -> [pointB](str)
                [pointC] -> [pointD](str)
            """
        ),
    ], ids=["case_1", "case_2"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys, 
            test_case, 
            Messages.Error.PIPELINE_CLOSING_BAR,
            Messages.Hint.ADD_CLOSING_BAR
        )


class TestBracketSyntaxErrors(TestBaseDSL):
    """Квадратная скобка определения сущности не найдена"""
    
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA -> [pointB](str)
            """
        ),
        (
            "case_2",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                pointA] -> [pointB](str)
            """
        ),
        (
            "case_3",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> pointB](str)
            """
        ),
        (
            "case_4",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> [pointB(str)
            """
        ),
    ], ids=["case_1", "case_2", "case_3", "case_4"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys, 
            test_case, 
            Messages.Error.BRACKET_MISSING,
            Messages.Hint.CHECK_BRACKETS
        )


class TestTypeSyntaxErrors(TestBaseDSL):
    """Финальный тип не задан или задан некорректно"""
    
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> [pointB]
            """
        ),
        (
            "case_2",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> [pointB](
            """
        ),
        (
            "case_3",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> [pointB])
            """
        ),
        (
            "case_4",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> [pointB](str
            """
        ),
        (
            "case_5",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> [pointB](bool(
            """
        ),
        (
            "case_6",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            $var1 = "test"

            target1:
                [pointA] -> |*func1($var1)| -> [pointB]
            """
        ),
    ], ids=["case_1", "case_2", "case_3", "case_4", "case_5", "case_6"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys, 
            test_case, 
            Messages.Error.FINAL_TYPE,
            Messages.Hint.SPECIFY_TYPE
        )


class TestVoidVarTypeErrors(TestBaseDSL):
    """Для пустого поля [] нельзя указывать тип"""
    
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointC] -> [](int)
            """
        ),
        (
            "case_2",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target2=dict/my_new_dict2
            target1:
                [pointA] -> [pointB](str)
                [pointC] -> [sdf](bool)

            target2:
                [pointA] -> [pointB](str)
                [pointC] -> [](bool)
            """
        ),

    ], ids=["case_1", "case_2"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys, 
            test_case, 
            Messages.Error.VOID_TYPE,
            Messages.Hint.VOID_NO_TYPE
        )

class TestSyntaxSourceErrors(TestBaseDSL):
    """Неверный синтаксис определения источника"""
    
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            """
            source dict
            target1=dict("target_new")
            target1:
                [pointC] -> []()
            """
        ),
        (
            "case_2",
            """
            source=dict
            target1=dict/my_new_dict
            target1:
                [pointC] -> [pointD](int)
            """
        ),
        (
            "case_3",
            """
            source=postgres.norm.path
            target1=dict/my_new_dict
            target1:
                [pointC] -> []()
            """
        ),
        (
            "case_4",
            """
            target1=dict/my_new_dict
            target1:
                [pointC] -> []()
            """
        ),
    ], ids=["case_1", "case_2", "case_3", "case_4"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys, 
            test_case, 
            Messages.Error.SYNTAX_SOURCE,
            Messages.Hint.SOURCE_SYNTAX
        )

class TestSyntaxTargetErrors(TestBaseDSL):
    """Неверный синтаксис определения источника"""
    
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            """
            source=dict/my_new_dict
            target1=dict("target_new")
            target1:
                [pointC] -> []()
            """
        ),
        (
            "case_2",
            """
            source=dict/my_new_dict
            target1=
            target1:
                [pointC] -> []()
            """
        ),
        (
            "case_3",
            """
            source=dict/my_new_dict
            target1=dict
            target1:
                [pointC] -> []()
            """
        ),
    ], ids=["case_1", "case_2", "case_3"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys, 
            test_case, 
            Messages.Error.SYNTAX_TARGET,
            Messages.Hint.TARGET_SYNTAX
        )

class TestVoidPipelineErrors(TestBaseDSL):
    """Пустой пайплайн"""
    
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> || -> [pointB](str)
            """
        ),
        (
            "case_2",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*func1| -> [pointB](str)
                [pointC] -> || -> [pointD](int)
            """
        ),
        (
            "case_3",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*func1| -> [pointB](str)
                [pointC] -> |*func2||| -> [pointD](int)
            """
        ),
        (
            "case_4",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*func1| -> [pointB](str)
                [pointC] -> |||| -> [pointD](int)
                [pointE] -> |*func3| -> [pointF](bool)
            """
        ),
    ], ids=["case_1", "case_2", "case_3", "case_4"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys, 
            test_case, 
            Messages.Error.PIPELINE_EMPTY,
            Messages.Hint.PIPELINE_MUST_HAVE_CONTENT
        )

class TestUnknownTokenErrors(TestBaseDSL):
    """Неожиданный токен в коде"""
    
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            """
            dfsdf
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*func1| -> [pointB](str)
                [pointC] -> || -> [pointD](int)
            """
        ),
        (
            "case_2",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                dsfsdf
                [pointA] -> |*func1| -> [pointB](str)
                [pointC] -> || -> [pointD](int)
            """
        ),
    ], ids=["case_1", "case_2"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys,
            test_case,
            Messages.Error.UNKNOWN,
            ""
        )


class TestValueTypeErrors(TestBaseDSL):
    """Неверный тип данных"""
    
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*func1| -> [pointB](abc)
                
            """
        ),
        (
            "case_2",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*func1| -> [pointB](int)
                [pointC] -> |*func2| -> [pointD](abc)
            """
        ),
    ], ids=["case_1", "case_2"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys,
            test_case,
            Messages.Error.INVALID_TYPE,
            Messages.Hint.INVALID_TYPE,
            partial_error="Неверный тип данных",
            partial_hint="Используйте один из разрешённых типов данных"
        )

class TestDuplicateVarNameErrors(TestBaseDSL):
    """Дублирующееся имя переменной"""
    
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            $my_var="abc"
            $my_var="def"
            target1:
                [pointA] -> |*func1| -> [pointB](int)
            """
        ),
    ], ids=["case_1"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys,
            test_case,
            Messages.Error.DUPLICATE_VAR,
            Messages.Hint.DUPLICATE_VAR,
            partial_error="Дублирующееся имя переменной",
            partial_hint="Переменная уже определена на строке"
        )

class TestDuplicateTargetNameErrors(TestBaseDSL):
    """Дублирующееся имя цели"""
    
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*func1| -> [pointB](int)
                [pointA] -> |*func1| -> [pointB](int)
            """
        ),
        (
            "case_2",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*func1| -> [$pointB](int)
                [pointA] -> |*func1| -> [$pointB](int)
            """
        ),
        (
            "case_3",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*func1| -> [pointB](int)
                [pointA] -> |*func1| -> [$pointB](int)
            """
        ),
        (
            "case_4",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*func1| -> [pointB](int)
                [pointA] -> |*func1| -> [$pointB](int)
            """
        ),
    ], ids=["case_1", "case_2", "case_3", "case_4"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys,
            test_case,
            Messages.Error.DUPLICATE_FINAL_NAME,
            Messages.Hint.DUPLICATE_FINAL_NAME,
            partial_error="Дублирующееся имя финальной цели",
            partial_hint="Цель уже используется для записи"
        )


class TestNotDefinedVarErrors(TestBaseDSL):
    """Неопределённая переменная"""
    
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*func1($s)| -> [pointB](int)
                [pointA] -> |*func1| -> [pointC](int)
            """
        ),
    ], ids=["case_1"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys,
            test_case,
            Messages.Error.UNDEFINED_VAR,
            Messages.Hint.UNDEFINED_VAR,
            partial_error="не определена в текущем контексте",
            partial_hint="Переменная должна быть определена перед использованием"
        )