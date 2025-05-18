import pytest
import json
from dataroute import DataRoute
from dataroute.localization import Messages, Localization
import re
import tempfile
import shutil
import os


class TestBaseDSL:

    @staticmethod
    def get_message(message_dict, lang="ru", folder=None):
        """Вспомогательная функция для получения локализованного сообщения"""
        if folder:
            return message_dict.get(lang, message_dict.get("ru", ""))
        else:
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
        (
            "case_5",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [[pointA] -> [pointB](str)
            """
        ),
    ], ids=["case_1", "case_2", "case_3", "case_4", "case_5"])
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
        (
            "case_7",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> [pointB]( int )
            """
        ),
    ], ids=["case_1", "case_2", "case_3", "case_4", "case_5", "case_6", "case_7"])
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

class TestDuplicateTargetNameTypeError(TestBaseDSL):
    """Дублирующееся имя целевого блока (DUPLICATE_TARGET_NAME_TYPE)"""
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            '''
            source=dict/my_dict
            target1=postgres/my_new_dict
            target2=postgres/my_new_dict
            target1:
                [pointA] -> |*func1()| -> [$s](int)
            target2:
                [pointA] -> |*func1()| -> [$s](int)
            '''
        ),
    ], ids=["case_1"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys,
            test_case,
            Messages.Error.DUPLICATE_TARGET_NAME_TYPE,
            Messages.Hint.DUPLICATE_TARGET_NAME_TYPE,
            partial_error="Дублирующееся имя цели",
            partial_hint="Используйте уникальные имена целей для разных типов"
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
        (
            "case_2",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*func1($not_defined)| -> [pointB](int)
            """
        ),
        (
            "case_3",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |IF($not_defined): *func1| -> [pointB](int)
            """
        ),
        (
            "case_4",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |IF(1): *func1 ELSE: *func2($not_defined)| -> [pointB](int)
            """
        ),
        (
            "case_5",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |IF(1): *func1 ELIF(2): *func2 ELSE: *func3($not_defined)| -> [pointB](int)
            """
        ),
        (
            "case_6",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |IF(1): *func1 ELIF($not_defined): *func2 ELSE: *func3(343)| -> [pointB](int)
            """
        ),
        (
            "case_7",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            $defined=1
            target1:
                [pointA] -> |*func1($defined, $not_defined2)| -> [pointB](int)
            """
        ),
        (
            "case_8",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            $defined=1
            $defined2=2
            target1:
                [pointA] -> |*func1($defined, $defined2, $not_defined2)| -> [pointB](int)
            """
        ),        
        (
            "case_9",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*func1(1000, "sdfds", $not_defined3)| -> [pointB](int)
            """
        ),
        (
            "case_10",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> [pointB](int)
                [pointC] -> |*func1($pointB)| -> [pointD](int)
                [pointE] -> |*func1($pointB, $pointAAAAAAAAA)| -> [pointF](int)
            """
        ),
    ], ids=["case_1", "case_2", "case_3", "case_4", "case_5", "case_6", "case_7", "case_8", "case_9", "case_10"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys,
            test_case,
            Messages.Error.UNDEFINED_VAR,
            Messages.Hint.UNDEFINED_VAR,
            partial_error="не определена в текущем контексте",
            partial_hint="Переменная должна быть определена перед использованием"
        )

class TestNotValidUsadeVarError(TestBaseDSL):
    """Неопределённая переменная"""
    
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*func1($s)| -> [$s](int)
            """
        ),
    ], ids=["case_1"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys,
            test_case,
            Messages.Error.INVALID_VAR_USAGE,
            Messages.Hint.INVALID_VAR_USAGE,
            partial_error="Некорректное использование переменной",
            partial_hint="Обратите внимание на место определения"
        )


class TestLeftPartAsVarError(TestBaseDSL):
    """Поле из левой части нельзя использовать как переменную"""

    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*func1| -> [pointB](int)
                [pointC] -> |*func2($pointA)| -> [pointD](int)
            """
        ),
    ], ids=["case_1"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys,
            test_case,
            Messages.Error.SRC_FIELD_AS_VAR,
            Messages.Hint.SRC_FIELD_AS_VAR,
            partial_error="нельзя использовать как переменную",
            partial_hint="Создайте отдельный маршрут для сохранения поля в переменную"
        )

class TestVarsFolderNotFound:
    """Папка с внешними переменными не найдена"""
    def test_vars_folder_not_found(self, capsys):
        test_input = """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*func1| -> [pointB](int)
                [pointC] -> |*func2($pointA)| -> [pointD](int)
        """
        with pytest.raises(SystemExit):
            dtrt = DataRoute(test_input, vars_folder="tests/ext_varsssssssss", debug=True, lang="ru", color=False)
            dtrt.go()
        output = capsys.readouterr().out + capsys.readouterr().err
        assert "Папка с внешними переменными не найдена" in output

class TestExternalVarPathNotFound:
    """Путь не найден во внешней переменной"""
    def test_external_var_path_not_found(self, capsys):
        test_input = """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*func1($$myvars.itemssssssssssss)| -> [pointB](int)
        """
        with pytest.raises(SystemExit):
            dtrt = DataRoute(test_input, vars_folder="tests/ext_vars", debug=True, lang="ru", color=False)
            dtrt.go()
        output = capsys.readouterr().out + capsys.readouterr().err
        assert "Путь не найден во внешней переменной" in output

class TestVarFileNotFound:
    """Файл не найден"""
    def test_var_file_not_found(self, capsys):
        test_input = """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*func1($$myvarssssss.1)| -> [pointB](int)
        """
        with pytest.raises(SystemExit):
            dtrt = DataRoute(test_input, vars_folder="tests/ext_vars", debug=True, lang="ru", color=False)
            dtrt.go()
        output = capsys.readouterr().out + capsys.readouterr().err
        assert "Файл с внешними переменными не найден" in output

class TestElseWithoutIf(TestBaseDSL):
    """ELSE без IF"""
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |ELSE(true): *func1| -> [pointB](int)
            """
        ),
    ], ids=["case_1"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys,
            test_case,
            Messages.Error.CONDITION_MISSING_IF,
            Messages.Hint.CONDITION_MISSING_IF
        )

class TestIfWithoutParenthesis(TestBaseDSL):
    """IF и ELIF без скобок"""
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |IFtrue: *func1| -> [pointB](int)
            """
        ),
        (
            "case_2",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointC] -> |IF(1): *func1 ELIFtrue: *func2| -> [pointD](int)
            """
        ),
        (
            "case_3",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointE] -> |IFtrue: *func1 ELIF(2): *func2| -> [pointF](int)
            """
        ),
        (
            "case_4",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointG] -> |IFtrue: *func1 ELIFtrue: *func2 ELSE: *func3| -> [pointH](int)
            """
        ),
        (
            "case_5",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointI] -> |IF(1): *func1 ELIF(2): *func2 ELIFtrue: *func3 ELIF(4): *func4 ELSE: *func5| -> [pointJ](int)
            """
        ),
    ], ids=["case_1", "case_2", "case_3", "case_4", "case_5"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys,
            test_case,
            Messages.Error.CONDITION_MISSING_PARENTHESIS,
            Messages.Hint.CONDITION_MISSING_PARENTHESIS
        )

class TestIfEmptyExpression(TestBaseDSL):
    """Пустое выражение в IF или ELIF"""
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |IF(): *func1| -> [pointB](int)
            """
        ),
        (
            "case_2",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointC] -> |IF(1): *func1 ELIF(): *func2| -> [pointD](int)
            """
        ),
        (
            "case_3",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointE] -> |IF(): *func1 ELIF(2): *func2| -> [pointF](int)
            """
        ),
        (
            "case_4",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointG] -> |IF(): *func1 ELIF(): *func2 ELSE: *func3| -> [pointH](int)
            """
        ),
        (
            "case_5",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointI] -> |IF(1): *func1 ELIF(2): *s1 ELIF(3): *func1 ELIF(): *func1 ELSE: *s1| -> [pointJ](int)
            """
        ),
    ], ids=["case_1", "case_2", "case_3", "case_4", "case_5"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys,
            test_case,
            Messages.Error.CONDITION_EMPTY_EXPRESSION,
            Messages.Hint.CONDITION_EMPTY_EXPRESSION
        )

class TestIfMissingColon(TestBaseDSL):
    """Условная конструкция без двоеточия"""
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |IF(1) *func1| -> [pointB](int)
            """
        ),
        (
            "case_2",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointC] -> |IF(1): *func1 ELSE *func2| -> [pointD](int)
            """
        ),
        (
            "case_3",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |IF(1): *func1| -> [pointB](int)
                [pointC] -> |IF(1): *func1 ELSE: *s1| -> [pointD](int)
                [pointE] -> |IF(1): *func1 ELIF(2): *s1 ELIF(3): *func1 ELIF(4) *s1 ELSE: *s1| -> [pointF](int)
            """
        ),
        (
            "case_4",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointE] -> |IF(1): *func1 ELIF(2): *func1 ELIF(3): *s1 ELIF(4) *func1 ELSE: *s1| -> [pointF](int)
            """
        ),
        (
            "case_5",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            $myvar = 1000
            target1:
                [A] -> |IF($$myvars.name == "test"): *func1($$myvars.items, $$myvars.name)|-> [B](str)
                [C] -> |IF("test"): *func1($$myvars.items, $$myvars.name) ELSE *s1($myvar)|-> [D](str)
            """
        ),
    ], ids=["case_1", "case_2", "case_3", "case_4", "case_5"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys,
            test_case,
            Messages.Error.CONDITION_MISSING_COLON,
            Messages.Hint.CONDITION_MISSING_COLON
        )

class TestConditionInvalidError(TestBaseDSL):
    """Недопустимое или неправильное условное выражение (CONDITION_INVALID)"""
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |IF(1):| -> [pointB](int)
            """
        ),
        (
            "case_2",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointB] -> |IF(1): *func1 ELIF(2):| -> [pointC](int)
            """
        ),
        (
            "case_3",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointC] -> |IF(1): *func1 ELIF(2): *s1 ELSE:| -> [pointD](int)
            """
        ),
    ], ids=["case_1", "case_2", "case_3"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys,
            test_case,
            Messages.Error.CONDITION_INVALID,
            Messages.Hint.CONDITION_INVALID,
            partial_error="Недопустимое или неправильное условное выражение",
            partial_hint="Проверьте правильность условного выражения и используйте конструкции"
        )

class TestSemanticTargetError(TestBaseDSL):
    """Маршрут для несуществующей цели (SEMANTIC_TARGET)"""
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            '''
            source=dict/my_dict
            target1=dict/my_new_dict
            target2:
                [pointA] -> [pointB](int)
            '''
        ),
    ], ids=["case_1"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys,
            test_case,
            Messages.Error.SEMANTIC_TARGET,
            Messages.Hint.TARGET_DEFINITION_MISSING,
            partial_error="Ошибка в определении цели",
            partial_hint="Определена карта маршрута"
        )

class TestSemanticRoutesError(TestBaseDSL):
    """Нет ни одного маршрута (SEMANTIC_ROUTES)"""
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            '''
            source=dict/my_dict
            target1=dict/my_new_dict
            '''
        ),
    ], ids=["case_1"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys,
            test_case,
            Messages.Error.SEMANTIC_ROUTES,
            Messages.Hint.ROUTES_MISSING,
            partial_error="Ошибка в определении маршрутов",
            partial_hint="Отсутствуют определения маршрутов"
        )

class TestDirectMappingWithoutStarWarning(TestBaseDSL):
    """Предупреждение: прямое отображение без звёздочки (DIRECT_MAPPING_WITHOUT_STAR)"""
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            '''
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |func1| -> [pointB](int)
            '''
        ),
    ], ids=["case_1"])
    def test_start(self, capsys, test_id, test_case):
        dtrt = DataRoute(test_case, debug=True, lang="ru", color=False)
        try:
            dtrt.go()
        except SystemExit:
            pass
        output = capsys.readouterr().out + capsys.readouterr().err
        # Удаляем ANSI-коды
        output_clean = re.sub(r"\x1b\[[0-9;]*m", "", output)
        # Получаем локализованный warning
        loc = Localization("ru")
        expected_warning = loc.get(Messages.Warning.DIRECT_MAPPING_WITHOUT_STAR, src="pointA", value="func1")
        # Удаляем маркеры форматирования
        for code in [">R<", ">RS<", ">G<", ">GREEN<", ">Y<", ">RESET<", ">BOLD<", ">O<"]:
            expected_warning = expected_warning.replace(code, "")
        assert expected_warning in output_clean

class TestFuncNotFoundError(TestBaseDSL):
    """Функция не найдена"""
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*notexistfunc| -> [pointB](int)
            """
        ),
        (
            "case_2",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*notexistfunc(123)| -> [pointB](int)
            """
        ),
        (
            "case_3",
            """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |IF(1): *notexistfunc()| -> [pointB](int)
            """
        ),
    ], ids=["case_1", "case_2", "case_3"])
    def test_start(self, capsys, test_id, test_case):
        temp_dir = tempfile.mkdtemp()
        try:
            # Передаём пустую папку как func_folder
            dtrt = DataRoute(test_case, func_folder=temp_dir, debug=True, lang="ru", color=False)
            with pytest.raises(SystemExit):
                dtrt.go()
            output = capsys.readouterr().out + capsys.readouterr().err
            assert "Функция не найдена" in output
            assert "Проверьте имя функции и наличие файла" in output
        finally:
            shutil.rmtree(temp_dir)

class TestFuncConflictError:
    """Пользовательская функция уже определена в системной библиотеке"""
    def test_func_conflict(self, capsys):
        test_input = """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*func1| -> [pointB](int)
        """
        # Используем папку ext_func, где гарантированно есть конфликт
        with pytest.raises(SystemExit):
            dtrt = DataRoute(test_input, func_folder="tests/ext_func", debug=True, lang="ru", color=False)
            dtrt.go()
        output = capsys.readouterr().out + capsys.readouterr().err
        assert "Обнаружены имена функций, которые уже существуют в системной библиотеке!" in output
        assert "в пользовательской папке" in output

class TestFuncFolderNotFound:
    """Папка с пользовательскими функциями не найдена"""
    def test_func_folder_not_found(self, capsys):
        test_input = """
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [pointA] -> |*func1| -> [pointB](int)
        """
        with pytest.raises(SystemExit):
            dtrt = DataRoute(test_input, func_folder="tests/ext_func_not_exist", debug=True, lang="ru", color=False)
            dtrt.go()
        output = capsys.readouterr().out + capsys.readouterr().err
        assert "Папка с пользовательскими функциями не найдена" in output
        assert "Проверьте путь к папке с функциями" in output

class TestDuplicateFinalNameError(TestBaseDSL):
    """Дублирующееся финальное имя (final_name) внутри одного блока target"""
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            '''
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [A] -> [$A](int)
                [B] -> [$A](int)
            '''
        ),
        (
            "case_2",
            '''
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [A] -> [A](int)
                [B] -> [A](int)
            '''
        ),
    ], ids=["case_1", "case_2"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys,
            test_case,
            Messages.Error.DUPLICATE_FINAL_NAME,
            Messages.Hint.DUPLICATE_FINAL_NAME,
            partial_error="Дублирующееся имя финальной цели",
            partial_hint="Цель уже используется для записи"
        )

class TestExternalVarWriteError(TestBaseDSL):
    """Нельзя записывать во внешнюю переменную ($$)"""
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            '''
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [A] -> [$$name](int)
            '''
        ),
        (
            "case_2",
            '''
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [A] -> |*func1| -> [$$var](str)
            '''
        ),
    ], ids=["case_1", "case_2"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys,
            test_case,
            Messages.Error.EXTERNAL_VAR_WRITE,
            Messages.Hint.EXTERNAL_VAR_WRITE,
            partial_error="Нельзя записывать во внешнюю переменную",
            partial_hint="Используйте только локальные переменные"
        )

class TestGlobalVarWriteError(TestBaseDSL):
    """Нельзя записывать в глобальную переменную ($my_var)"""
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            '''
            source=dict/my_dict
            target1=dict/my_new_dict
            $my_var=1
            target1:
                [A] -> [$my_var](int)
            '''
        ),
        (
            "case_2",
            '''
            source=dict/my_dict
            target1=dict/my_new_dict
            $my_var2="test"
            target1:
                [A] -> |*func1| -> [$my_var2](str)
            '''
        ),
    ], ids=["case_1", "case_2"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys,
            test_case,
            Messages.Error.GLOBAL_VAR_WRITE,
            Messages.Hint.GLOBAL_VAR_WRITE,
            partial_error="Нельзя записывать в глобальную переменную",
            partial_hint="Используйте уникальное имя для переменной назначения"
        )

class TestUndefinedGlobalVarError(TestBaseDSL):
    """Глобальная переменная не определена"""
    @pytest.mark.parametrize("test_id, test_case", [
        (
            "case_1",
            '''
            source=dict/my_dict
            target1=dict/my_new_dict
            target1:
                [$my_var2] -> [A](int)
            '''
        ),
    ], ids=["case_1"])
    def test_start(self, capsys, test_id, test_case):
        self.run_test(
            capsys,
            test_case,
            Messages.Error.UNDEFINED_GLOBAL_VAR,
            Messages.Hint.UNDEFINED_GLOBAL_VAR,
            partial_error="Глобальная переменная",
            partial_hint="Определите глобальную переменную выше по коду"
        )
