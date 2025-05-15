import re
import sys
from typing import Optional

from .constants import ErrorType, ERROR_MESSAGE_MAP, ERROR_HINT_MAP, ALLOWED_TYPES
from .localization import Localization, Messages
from .config import Config


class DSLSyntaxError(Exception):
    """Базовый класс для всех синтаксических ошибок DSL"""
    
    def __init__(self, 
                 error_type: ErrorType,
                 line: str,
                 line_num: int,
                 position: Optional[int] = None,
                 suggestion: Optional[str] = None,
                 **kwargs):
        self.error_type = error_type
        self.line = line
        self.line_num = line_num
        self.position = position or self._guess_error_position(line)
        self.suggestion = suggestion
        self.lang = Config.get_lang()
        self.loc = Localization(self.lang)
        self.format_kwargs = kwargs or {}
        
        # Формируем сообщение об ошибке
        message = self._format_error_message()
        super().__init__(message)
    
    def _guess_error_position(self, line: str) -> int:
        """Пытается угадать позицию ошибки в строке"""
        return 0
    
    def _format_error_message(self) -> str:
        """Форматирует сообщение об ошибке"""
        # Получаем соответствующее сообщение об ошибке
        message = self.loc.get(ERROR_MESSAGE_MAP.get(self.error_type, Messages.Error.UNKNOWN), **self.format_kwargs)
        
        # Форматируем строку с указателем на позицию ошибки
        pointer = " " * self.position + "^"
        
        result = [
            self.loc.get(Messages.Error.LINE_PREFIX, line_num=self.line_num),
            f"{self.line}",
            f"{pointer}",
            f"{message}",
        ]
        
        # Если есть подсказка, добавляем её
        if self.suggestion:
            hint_label = self.loc.get(Messages.Hint.LABEL)
            result.append(f"{hint_label} {self.suggestion}")
        # Иначе пробуем использовать стандартную подсказку для данного типа ошибки
        elif ERROR_HINT_MAP.get(self.error_type):
            hint = self.loc.get(ERROR_HINT_MAP.get(self.error_type), 
                                target=self.line if self.error_type == ErrorType.SEMANTIC_TARGET else None,
                                **self.format_kwargs)
            if hint:
                hint_label = self.loc.get(Messages.Hint.LABEL)
                result.append(f"{hint_label} {hint}")
        
        return "\n".join(result)


class SyntaxErrorHandler:
    """Обработчик синтаксических ошибок DSL"""
    
    def __init__(self):
        # Паттерны для частичных совпадений
        self.patterns = {
            # Для проверки открытого пайплайна без закрытия
            "pipeline_open": r'\|[^|]*(?!\|)[^|]*$',
            
            # Для проверки пустого пайплайна
            "pipeline_empty": r'\|\|',
            
            # Для проверки последовательных пайплайнов
            "pipeline_sequential": r'\|[^|]*\|\s*(?:->|=>|-|>)\s*\|',
            
            # Для проверки неправильных скобок
            "brackets_missing_open": r'(?<!\[)\w+\]',
            "brackets_missing_close": r'\[[^\]]*$',
            
            # Для проверки корректности символов направления
            "direction_missing": r'\]\s*(?!(?:->|=>|-|>))[^\s]',
            
            # Для проверки корректности финального типа
            "final_type_missing": r'\]\s*$|\]\s*(?!\()',
            
            # Для проверки синтаксиса источника
            "source_syntax": r'source\s+\w+',
            
            # Для проверки синтаксиса цели
            "target_syntax": r'=\s*\w+\s*\[\s*["\'](.*?)["\']'
        }
    
    def analyze(self, line: str, line_num: int) -> DSLSyntaxError:
        """Анализирует строку и возвращает соответствующую ошибку"""
        # Проверка на пустой пайплайн
        if re.search(self.patterns["pipeline_empty"], line):
            pos = re.search(self.patterns["pipeline_empty"], line).start() + 1
            return PipelineEmptyError(line, line_num, pos)
        
        # Проверка на последовательные пайплайны
        if re.search(self.patterns["pipeline_sequential"], line):
            pos = re.search(self.patterns["pipeline_sequential"], line).end() - 1
            return DSLSyntaxError(ErrorType.PIPELINE_EMPTY, line, line_num, pos, Messages.Hint.SEQUENTIAL_PIPELINES)
        
        # Проверка синтаксиса определения источника и цели
        if re.match(self.patterns["source_syntax"], line):
            pos = line.find('source') + len('source')
            return DSLSyntaxError(ErrorType.SYNTAX_SOURCE, line, line_num, pos, None)
        
        if re.search(self.patterns["target_syntax"], line):
            pos = line.find('[')
            return DSLSyntaxError(ErrorType.SYNTAX_TARGET, line, line_num, pos, None)
        
        # Проверка на конечное поле с типом
        if "->" in line and "]" in line:
            # Проверка полей без типа - поиск шаблона [field_name] без скобок типа после
            field_match = re.search(r'\[\s*([a-zA-Z0-9_]+)\s*\]', line)
            if field_match:
                field_pos = field_match.end()
                # Проверяем, что после закрывающей скобки нет открывающей скобки для типа
                if field_pos < len(line) and '(' not in line[field_pos:]:
                    # Если после скобки есть текст, и это не пустые скобки []
                    if field_match.group(1):  # Есть имя внутри скобок
                        # Убедимся, что это финальная часть строки (после ->)
                        arrow_pos = line.rfind('->')
                        if arrow_pos != -1 and field_pos > arrow_pos:
                            return FinalTypeError(line, line_num, field_pos)
            
            # Проверяем, есть ли после последней "]" скобок типа "(" и ")"
            last_bracket_pos = line.rfind(']')
            if last_bracket_pos != -1:
                after_bracket = line[last_bracket_pos:]
                
                # Проверка на неверный тип данных
                type_match = re.search(r'\(([a-zA-Z0-9_]+)\)', after_bracket)
                if type_match:
                    data_type = type_match.group(1)
                    if data_type not in ALLOWED_TYPES:
                        return InvalidTypeError(line, line_num, data_type, last_bracket_pos + after_bracket.find('(') + 1)
                
                # Если после скобки есть текст, но нет открывающей скобки типа или тип пустой ()
                if '(' in after_bracket and ')' in after_bracket and \
                   after_bracket.find('(') < after_bracket.find(')') and \
                   len(after_bracket[after_bracket.find('(')+1:after_bracket.find(')')].strip()) == 0:
                    # Проверяем содержимое скобок
                    bracket_content = line[line.rfind('[')+1:last_bracket_pos].strip()
                    if not bracket_content:  # Пустое поле с типом - ошибка
                        return VoidTypeError(line, line_num, last_bracket_pos + 1)
                    else:  # Непустое поле с пустым типом - ошибка
                        return FinalTypeError(line, line_num, after_bracket.find('(') + 1)
        
        # Проверка на символ направления
        direction_missing = False
        direction_pos = 0
        
        if ']' in line and '[' in line:
            # Найдем все вхождения закрывающей скобки
            for match in re.finditer(r'\]', line):
                end_pos = match.end()
                # Если после скобки нет стрелки, и это не последняя скобка в строке
                if end_pos < len(line) - 1 and not re.match(r'\s*(?:->|=>|-|>|\()', line[end_pos:]):
                    # Если после этого есть еще квадратная скобка
                    if '[' in line[end_pos:]:
                        direction_missing = True
                        direction_pos = end_pos
                        break
        
        if direction_missing:
            return FlowDirectionError(line, line_num, direction_pos)
        
        # Проверка на незакрытый пайплайн
        pipe_count = line.count('|')
        if pipe_count > 0 and pipe_count % 2 != 0:
            # Найти позицию последней вертикальной черты
            last_pipe_pos = line.rfind('|')
            return PipelineClosingBarError(line, line_num, last_pipe_pos)
        
        # Проверка на неправильные скобки
        if line.count('[') != line.count(']'):
            if line.count('[') > line.count(']'):
                # Если открывающих скобок больше
                for match in re.finditer(r'\[', line):
                    start_pos = match.start()
                    # Проверяем, есть ли для этой скобки закрывающая
                    remaining = line[start_pos+1:]
                    if ']' not in remaining:
                        return BracketMissingError(line, line_num, start_pos)
            else:
                # Если закрывающих скобок больше
                for match in re.finditer(r'\]', line):
                    end_pos = match.start()
                    preceding = line[:end_pos]
                    if preceding.count('[') < preceding.count(']') + 1:
                        return BracketMissingError(line, line_num, end_pos)
        
        # Проверка отсутствия открывающей скобки
        opening_bracket_missing = re.search(r'(?<!\[)(\w+)\]', line)
        if opening_bracket_missing:
            pos = opening_bracket_missing.start(1)
            return BracketMissingError(line, line_num, pos)
        
        # Если не удалось определить конкретную ошибку
        return DSLSyntaxError(ErrorType.UNKNOWN, line, line_num, 0, None)


# Конкретные классы ошибок с специфичной логикой определения позиции

class PipelineClosingBarError(DSLSyntaxError):
    """Ошибка отсутствия закрывающей черты пайплайна"""
    
    def __init__(self, line: str, line_num: int, position: Optional[int] = None):
        super().__init__(ErrorType.PIPELINE_CLOSING_BAR, line, line_num, position, None)
    
    def _guess_error_position(self, line: str) -> int:
        # Находим последний символ '|' и предполагаем, что ошибка после него
        last_bar_pos = line.rfind('|')
        if last_bar_pos != -1:
            return last_bar_pos + 1
        # Если не нашли '|', ищем '[' и ']'
        bracket_pos = line.find('[')
        if bracket_pos != -1:
            return bracket_pos
        return 0


class BracketMissingError(DSLSyntaxError):
    """Ошибка отсутствия или неправильного использования квадратных скобок"""
    
    def __init__(self, line: str, line_num: int, position: Optional[int] = None):
        super().__init__(ErrorType.BRACKET_MISSING, line, line_num, position, None)
    
    def _guess_error_position(self, line: str) -> int:
        # Проверяем несоответствие открывающих и закрывающих скобок
        open_brackets = line.count('[')
        close_brackets = line.count(']')
        
        if open_brackets > close_brackets:
            # Ищем последнюю открывающую скобку без пары
            pos = len(line) - 1
            while pos >= 0:
                if line[pos] == '[':
                    close_pos = line.find(']', pos)
                    if close_pos == -1:
                        return pos
                pos -= 1
        elif close_brackets > open_brackets:
            # Ищем первую закрывающую скобку без пары
            for pos, char in enumerate(line):
                if char == ']':
                    if line[:pos].count('[') <= line[:pos].count(']'):
                        return pos
        
        # Если не можем найти проблему со скобками, ищем первое использование скобок
        bracket_pos = line.find('[')
        if bracket_pos != -1:
            return bracket_pos
        
        return 0


class FlowDirectionError(DSLSyntaxError):
    """Ошибка символа направления потока"""
    
    def __init__(self, line: str, line_num: int, position: Optional[int] = None):
        super().__init__(ErrorType.FLOW_DIRECTION, line, line_num, position, None)
    
    def _guess_error_position(self, line: str) -> int:
        # Ищем позицию после ']', где должна быть стрелка
        bracket_close_pos = line.find(']')
        if bracket_close_pos != -1:
            return bracket_close_pos + 1
        return 0


class FinalTypeError(DSLSyntaxError):
    """Ошибка финального типа"""
    
    def __init__(self, line: str, line_num: int, position: Optional[int] = None):
        super().__init__(ErrorType.FINAL_TYPE, line, line_num, position, None)
    
    def _guess_error_position(self, line: str) -> int:
        # Ищем последнюю скобку ']' и затем проверяем наличие '('
        last_bracket_pos = line.rfind(']')
        if last_bracket_pos != -1:
            return last_bracket_pos + 1
        return len(line) - 1


class InvalidTypeError(DSLSyntaxError):
    """Ошибка неверного типа данных"""
    
    def __init__(self, line: str, line_num: int, data_type: str, position: Optional[int] = None):
        self.data_type = data_type
        super().__init__(ErrorType.INVALID_TYPE, line, line_num, position, None)
    
    def _guess_error_position(self, line: str) -> int:
        # Ищем позицию типа данных в скобках
        type_pattern = r'\(' + self.data_type + r'\)'
        type_match = re.search(type_pattern, line)
        if type_match:
            return type_match.start() + 1
        return super()._guess_error_position(line)
    
    def _format_error_message(self) -> str:
        """Форматирует сообщение об ошибке с указанием недопустимого типа данных"""
        # Получаем сообщение об ошибке с передачей типа данных в качестве параметра
        message = self.loc.get(ERROR_MESSAGE_MAP.get(self.error_type, Messages.Error.UNKNOWN), 
                              data_type=self.data_type)
        
        # Форматируем строку с указателем на позицию ошибки
        pointer = " " * self.position + "^"
        
        result = [
            self.loc.get(Messages.Error.LINE_PREFIX, line_num=self.line_num),
            f"{self.line}",
            f"{pointer}",
            f"{message}",
        ]
        
        # Добавляем подсказку для этого типа ошибки
        hint = self.loc.get(ERROR_HINT_MAP.get(self.error_type), 
                           allowed_types=", ".join(ALLOWED_TYPES))
        if hint:
            hint_label = self.loc.get(Messages.Hint.LABEL)
            result.append(f"{hint_label} {hint}")
        
        return "\n".join(result)


class PipelineEmptyError(DSLSyntaxError):
    """Ошибка пустого пайплайна"""
    
    def __init__(self, line: str, line_num: int, position: Optional[int] = None):
        super().__init__(ErrorType.PIPELINE_EMPTY, line, line_num, position, None)
    
    def _guess_error_position(self, line: str) -> int:
        # Находим позицию пустого пайплайна "||"
        empty_pipeline_match = re.search(r'\|\|', line)
        if empty_pipeline_match:
            return empty_pipeline_match.start() + 1
        return 0 


class VoidTypeError(DSLSyntaxError):
    """Ошибка указания типа для пустого поля"""
    
    def __init__(self, line: str, line_num: int, position: Optional[int] = None):
        # Будем использовать тип ошибки VOID_TYPE
        super().__init__(ErrorType.VOID_TYPE, line, line_num, position, None)
        # Заменяем стандартную подсказку на специальную для void-поля
        self.suggestion = self.loc.get(Messages.Hint.VOID_NO_TYPE)
    
    def _guess_error_position(self, line: str) -> int:
        # Ищем позицию после пустых квадратных скобок []
        empty_bracket_match = re.search(r'\[\]\s*\(', line)
        if empty_bracket_match:
            return empty_bracket_match.end() - 1  # Позиция на открывающей скобке (
        # Если не нашли, используем последнюю ]
        last_bracket_pos = line.rfind(']')
        if last_bracket_pos != -1:
            return last_bracket_pos + 1
        return len(line) - 1


class UnknownPipelineSegmentError(DSLSyntaxError):
    """Ошибка неизвестного сегмента в пайплайне"""
    
    def __init__(self, line: str, line_num: int, segment: str, position: Optional[int] = None):
        self.segment = segment
        super().__init__(ErrorType.UNKNOWN_PIPELINE_SEGMENT, line, line_num, position, None)
    
    def _guess_error_position(self, line: str) -> int:
        # Ищем позицию сегмента в строке
        if self.segment and self.segment in line:
            return line.find(self.segment)
        
        # Ищем сегмент между вертикальными чертами
        pipe_pos = line.find('|')
        if pipe_pos != -1:
            next_pipe_pos = line.find('|', pipe_pos + 1)
            if next_pipe_pos != -1:
                return pipe_pos + 1
        
        return 0


class UndefinedVarError(DSLSyntaxError):
    """Ошибка неопределенной переменной"""
    
    def __init__(self, line: str, line_num: int, var_name: str, position: Optional[int] = None):
        self.var_name = var_name
        super().__init__(ErrorType.UNDEFINED_VAR, line, line_num, position, None)
        
    def _guess_error_position(self, line: str) -> int:
        """Определяет позицию ошибки в строке"""
        # Ищем позицию переменной в строке
        var_pos = line.find('$' + self.var_name)
        if var_pos != -1:
            return var_pos
        
        # Ищем позицию внутри пайплайна
        pipe_pos = line.find('|')
        if pipe_pos != -1:
            next_pipe_pos = line.find('|', pipe_pos + 1)
            if next_pipe_pos != -1:
                return pipe_pos + 1
        
        return 0
        
    def _format_error_message(self) -> str:
        """Форматирует сообщение об ошибке с учетом имени переменной"""
        # Получаем соответствующее сообщение об ошибке
        message = self.loc.get(ERROR_MESSAGE_MAP.get(self.error_type, Messages.Error.UNKNOWN), var_name=self.var_name)
        
        # Форматируем строку с указателем на позицию ошибки
        pointer = " " * self.position + "^"
        
        result = [
            self.loc.get(Messages.Error.LINE_PREFIX, line_num=self.line_num),
            f"{self.line}",
            f"{pointer}",
            f"{message}",
        ]
        
        # Добавляем подсказку для этого типа ошибки
        hint = self.loc.get(ERROR_HINT_MAP.get(self.error_type))
        if hint:
            hint_label = self.loc.get(Messages.Hint.LABEL)
            result.append(f"{hint_label} {hint}")
        
        return "\n".join(result)


class InvalidVarUsageError(DSLSyntaxError):
    """Ошибка неправильного использования переменной"""
    
    def __init__(self, line: str, line_num: int, var_name: str, position: Optional[int] = None):
        self.var_name = var_name
        super().__init__(ErrorType.INVALID_VAR_USAGE, line, line_num, position, None)
        
    def _guess_error_position(self, line: str) -> int:
        """Определяет позицию ошибки в строке"""
        # Ищем позицию переменной в строке
        var_pos = line.find('$' + self.var_name)
        if var_pos != -1:
            return var_pos
        
        # Ищем позицию внутри пайплайна
        pipe_pos = line.find('|')
        if pipe_pos != -1:
            next_pipe_pos = line.find('|', pipe_pos + 1)
            if next_pipe_pos != -1:
                return pipe_pos + 1
        
        return 0
        
    def _format_error_message(self) -> str:
        """Форматирует сообщение об ошибке с учетом имени переменной"""
        # Получаем соответствующее сообщение об ошибке
        message = self.loc.get(ERROR_MESSAGE_MAP.get(self.error_type, Messages.Error.UNKNOWN), var_name=self.var_name)
        
        # Форматируем строку с указателем на позицию ошибки
        pointer = " " * self.position + "^"
        
        result = [
            self.loc.get(Messages.Error.LINE_PREFIX, line_num=self.line_num),
            f"{self.line}",
            f"{pointer}",
            f"{message}",
        ]
        
        # Добавляем подсказку для этого типа ошибки
        hint = self.loc.get(ERROR_HINT_MAP.get(self.error_type))
        if hint:
            hint_label = self.loc.get(Messages.Hint.LABEL)
            result.append(f"{hint_label} {hint}")
        
        return "\n".join(result)


class SrcFieldAsVarError(DSLSyntaxError):
    """Ошибка использования поля из левой части как переменной"""
    
    def __init__(self, line: str, line_num: int, var_name: str, position: Optional[int] = None):
        self.var_name = var_name
        super().__init__(ErrorType.SRC_FIELD_AS_VAR, line, line_num, position, None)
        
    def _guess_error_position(self, line: str) -> int:
        """Определяет позицию ошибки в строке"""
        # Ищем позицию переменной в строке
        var_pos = line.find('$' + self.var_name)
        if var_pos != -1:
            return var_pos
        
        # Ищем позицию внутри пайплайна
        pipe_pos = line.find('|')
        if pipe_pos != -1:
            next_pipe_pos = line.find('|', pipe_pos + 1)
            if next_pipe_pos != -1:
                return pipe_pos + 1
        
        return 0
        
    def _format_error_message(self) -> str:
        """Форматирует сообщение об ошибке с учетом имени переменной"""
        # Получаем соответствующее сообщение об ошибке
        message = self.loc.get(ERROR_MESSAGE_MAP.get(self.error_type, Messages.Error.UNKNOWN), var_name=self.var_name)
        
        # Форматируем строку с указателем на позицию ошибки
        pointer = " " * self.position + "^"
        
        result = [
            self.loc.get(Messages.Error.LINE_PREFIX, line_num=self.line_num),
            f"{self.line}",
            f"{pointer}",
            f"{message}",
        ]
        
        # Добавляем подсказку для этого типа ошибки
        hint = self.loc.get(ERROR_HINT_MAP.get(self.error_type))
        if hint:
            hint_label = self.loc.get(Messages.Hint.LABEL)
            result.append(f"{hint_label} {hint}")
        
        return "\n".join(result)


class ExternalVarsFolderNotFoundError(DSLSyntaxError):
    """Ошибка: папка с внешними переменными не найдена"""
    
    def __init__(self, folder_name: str, line: str = None, line_num: int = 0, position: int = None):
        self.folder_name = folder_name
        # Создаем фиктивные параметры для базового класса
        # т.к. эта ошибка не связана напрямую с конкретной строкой кода
        dummy_line = f"vars_folder=\"{folder_name}\"" if line is None else line
        super().__init__(ErrorType.UNKNOWN, dummy_line, line_num, position or 0, None)
        
    def _format_error_message(self) -> str:
        """Форматирует сообщение об ошибке для папки с внешними переменными"""
        message = self.loc.get(Messages.Error.VARS_FOLDER_NOT_FOUND, folder=self.folder_name)
        hint = self.loc.get(Messages.Hint.VARS_FOLDER_NOT_FOUND)
        hint_label = self.loc.get(Messages.Hint.LABEL)
        
        # Если есть информация о строке и номере строки, формируем сообщение с указателем
        if self.line_num > 0:
            # Форматируем строку с указателем на позицию ошибки
            pointer = " " * self.position + "^"
            
            result = [
                self.loc.get(Messages.Error.LINE_PREFIX, line_num=self.line_num),
                f"{self.line}",
                f"{pointer}",
                f"{message}",
                f"{hint_label} {hint}"
            ]
        else:
            # Если информации о строке нет, возвращаем базовое сообщение
            result = [
                message,
                f"{hint_label} {hint}"
            ]
        
        return "\n".join(result)


class ExternalVarFileNotFoundError(DSLSyntaxError):
    """Ошибка: файл с внешними переменными не найден"""
    
    def __init__(self, file_name: str, line: str = None, line_num: int = 0, position: int = None, node_value: str = None):
        self.file_name = file_name
        # Создаем фиктивные параметры для базового класса
        dummy_line = f"$$file_name..." if line is None else line
        
        # Если передан узел, из которого можно извлечь информацию о позиции
        if node_value and position is None:
            if "$$" + file_name in node_value:
                position = dummy_line.find("$$" + file_name)
            elif file_name in node_value:
                position = dummy_line.find(file_name)
        
        super().__init__(ErrorType.UNKNOWN, dummy_line, line_num, position or 0, None)
        
    def _format_error_message(self) -> str:
        """Форматирует сообщение об ошибке для файла с внешними переменными"""
        message = self.loc.get(Messages.Error.EXTERNAL_VAR_FILE_NOT_FOUND, file=self.file_name)
        hint = self.loc.get(Messages.Hint.EXTERNAL_VAR_FILE_NOT_FOUND)
        hint_label = self.loc.get(Messages.Hint.LABEL)
        
        # Если есть информация о строке и номере строки, формируем сообщение с указателем
        if self.line_num > 0:
            # Форматируем строку с указателем на позицию ошибки
            pointer = " " * self.position + "^"
            
            result = [
                self.loc.get(Messages.Error.LINE_PREFIX, line_num=self.line_num),
                f"{self.line}",
                f"{pointer}",
                f"{message}",
                f"{hint_label} {hint}"
            ]
        else:
            # Если информации о строке нет, возвращаем базовое сообщение
            result = [
                message,
                f"{hint_label} {hint}"
            ]
        
        return "\n".join(result)


class ExternalVarPathNotFoundError(DSLSyntaxError):
    """Ошибка: путь не найден во внешней переменной"""
    
    def __init__(self, path: str, line: str = None, line_num: int = 0, position: int = None, node_value: str = None):
        self.path = path
        # Создаем фиктивные параметры для базового класса, если строка не передана
        dummy_line = f"$${path}" if line is None else line
        # Если передан узел, из которого можно извлечь информацию о позиции
        if node_value and position is None:
            if "$$" + path in node_value:
                position = dummy_line.find("$$" + path)
            elif path in node_value:
                position = dummy_line.find(path)
        
        super().__init__(ErrorType.UNKNOWN, dummy_line, line_num, position, None)
        
    def _format_error_message(self) -> str:
        """Форматирует сообщение об ошибке для пути во внешней переменной"""
        message = self.loc.get(Messages.Error.EXTERNAL_VAR_PATH_NOT_FOUND, path=self.path)
        hint = self.loc.get(Messages.Hint.EXTERNAL_VAR_PATH_NOT_FOUND)
        hint_label = self.loc.get(Messages.Hint.LABEL)
        
        # Если есть информация о строке и номере строки, формируем сообщение с указателем
        if self.line_num > 0:
            # Форматируем строку с указателем на позицию ошибки
            pointer = " " * self.position + "^"
            
            result = [
                self.loc.get(Messages.Error.LINE_PREFIX, line_num=self.line_num),
                f"{self.line}",
                f"{pointer}",
                f"{message}",
                f"{hint_label} {hint}"
            ]
        else:
            # Если информации о строке нет, возвращаем базовое сообщение
            result = [
                message,
                f"{hint_label} {hint}"
            ]
        
        return "\n".join(result)


class ConditionMissingIfError(DSLSyntaxError):
    """Ошибка: конструкция ELSE без IF"""
    
    def __init__(self, line: str, line_num: int, position: Optional[int] = None):
        super().__init__(ErrorType.CONDITION_MISSING_IF, line, line_num, position)
    
    def _guess_error_position(self, line: str) -> int:
        # Находим позицию ELSE в строке
        else_pos = line.lower().find("else")
        if else_pos != -1:
            return else_pos
        return 0
    
    def _format_error_message(self) -> str:
        """Форматирует сообщение об ошибке"""
        # Получаем соответствующее сообщение об ошибке
        message = self.loc.get(ERROR_MESSAGE_MAP.get(self.error_type, Messages.Error.CONDITION_MISSING_IF))
        
        # Форматируем строку с указателем на позицию ошибки
        pointer = " " * self.position + "^"
        
        result = [
            self.loc.get(Messages.Error.LINE_PREFIX, line_num=self.line_num),
            f"{self.line}",
            f"{pointer}",
            f"{message}",
        ]
        
        # Если есть подсказка в карте подсказок, добавляем её
        hint = self.loc.get(ERROR_HINT_MAP.get(self.error_type))
        if hint:
            hint_label = self.loc.get(Messages.Hint.LABEL)
            result.append(f"{hint_label} {hint}")
        
        return "\n".join(result)


class ConditionMissingColonError(DSLSyntaxError):
    """Ошибка: не найден знак завершения условного выражения (:)"""
    
    def __init__(self, line: str, line_num: int, position: Optional[int] = None):
        super().__init__(ErrorType.CONDITION_MISSING_COLON, line, line_num, position)
    
    def _guess_error_position(self, line: str) -> int:
        # Находим позицию после закрывающей скобки
        # или после IF/ELIF
        close_paren_pos = line.find(")")
        if close_paren_pos != -1:
            return close_paren_pos + 1
        
        # Если нет скобок, ищем после IF/ELIF
        for keyword in ["if", "elif"]:
            keyword_pos = line.lower().find(keyword)
            if keyword_pos != -1:
                return keyword_pos + len(keyword)
        
        return 0
    
    def _format_error_message(self) -> str:
        """Форматирует сообщение об ошибке"""
        # Получаем соответствующее сообщение об ошибке
        message = self.loc.get(ERROR_MESSAGE_MAP.get(self.error_type, Messages.Error.CONDITION_MISSING_COLON))
        
        # Форматируем строку с указателем на позицию ошибки
        pointer = " " * self.position + "^"
        
        result = [
            self.loc.get(Messages.Error.LINE_PREFIX, line_num=self.line_num),
            f"{self.line}",
            f"{pointer}",
            f"{message}",
        ]
        
        # Если есть подсказка в карте подсказок, добавляем её
        hint = self.loc.get(ERROR_HINT_MAP.get(self.error_type))
        if hint:
            hint_label = self.loc.get(Messages.Hint.LABEL)
            result.append(f"{hint_label} {hint}")
        
        return "\n".join(result)


class ConditionMissingParenthesisError(DSLSyntaxError):
    """Ошибка: условная конструкция должна содержать знак скобок"""
    
    def __init__(self, line: str, line_num: int, position: Optional[int] = None):
        super().__init__(ErrorType.CONDITION_MISSING_PARENTHESIS, line, line_num, position)
    
    def _guess_error_position(self, line: str) -> int:
        # Находим позицию после IF/ELIF
        for keyword in ["if", "elif"]:
            keyword_pos = line.lower().find(keyword)
            if keyword_pos != -1:
                return keyword_pos + len(keyword)
        
        return 0
    
    def _format_error_message(self) -> str:
        """Форматирует сообщение об ошибке"""
        # Получаем соответствующее сообщение об ошибке
        message = self.loc.get(ERROR_MESSAGE_MAP.get(self.error_type, Messages.Error.CONDITION_MISSING_PARENTHESIS))
        
        # Форматируем строку с указателем на позицию ошибки
        pointer = " " * self.position + "^"
        
        result = [
            self.loc.get(Messages.Error.LINE_PREFIX, line_num=self.line_num),
            f"{self.line}",
            f"{pointer}",
            f"{message}",
        ]
        
        # Если есть подсказка в карте подсказок, добавляем её
        hint = self.loc.get(ERROR_HINT_MAP.get(self.error_type))
        if hint:
            hint_label = self.loc.get(Messages.Hint.LABEL)
            result.append(f"{hint_label} {hint}")
        
        return "\n".join(result)


class ConditionEmptyExpressionError(DSLSyntaxError):
    """Ошибка: не найдено логическое выражение внутри условной конструкции"""
    
    def __init__(self, line: str, line_num: int, position: Optional[int] = None):
        super().__init__(ErrorType.CONDITION_EMPTY_EXPRESSION, line, line_num, position)
    
    def _guess_error_position(self, line: str) -> int:
        # Находим позицию внутри скобок
        open_paren_pos = line.find("(")
        close_paren_pos = line.find(")")
        
        if open_paren_pos != -1 and close_paren_pos != -1 and open_paren_pos < close_paren_pos:
            return open_paren_pos + 1
        
        return 0
    
    def _format_error_message(self) -> str:
        """Форматирует сообщение об ошибке"""
        # Получаем соответствующее сообщение об ошибке
        message = self.loc.get(ERROR_MESSAGE_MAP.get(self.error_type, Messages.Error.CONDITION_EMPTY_EXPRESSION))
        
        # Форматируем строку с указателем на позицию ошибки
        pointer = " " * self.position + "^"
        
        result = [
            self.loc.get(Messages.Error.LINE_PREFIX, line_num=self.line_num),
            f"{self.line}",
            f"{pointer}",
            f"{message}",
        ]
        
        # Если есть подсказка в карте подсказок, добавляем её
        hint = self.loc.get(ERROR_HINT_MAP.get(self.error_type))
        if hint:
            hint_label = self.loc.get(Messages.Hint.LABEL)
            result.append(f"{hint_label} {hint}")
        
        return "\n".join(result)


class ConditionInvalidError(DSLSyntaxError):
    """Ошибка: недопустимое или неправильное условное выражение"""
    
    def __init__(self, line: str, line_num: int, message: str, position: Optional[int] = None):
        self.custom_message = message
        super().__init__(ErrorType.CONDITION_INVALID, line, line_num, position)
    
    def _guess_error_position(self, line: str) -> int:
        # Находим позицию IF
        if_pos = line.lower().find("if")
        if if_pos != -1:
            return if_pos
        return 0
    
    def _format_error_message(self) -> str:
        """Форматирует сообщение об ошибке с кастомным сообщением"""
        # Используем пользовательское сообщение
        message = self.custom_message
        
        # Форматируем строку с указателем на позицию ошибки
        pointer = " " * self.position + "^"
        
        result = [
            self.loc.get(Messages.Error.LINE_PREFIX, line_num=self.line_num),
            f"{self.line}",
            f"{pointer}",
            f"{message}",
        ]
        
        # Если есть подсказка в карте подсказок, добавляем её
        hint = self.loc.get(ERROR_HINT_MAP.get(self.error_type))
        if hint:
            hint_label = self.loc.get(Messages.Hint.LABEL)
            result.append(f"{hint_label} {hint}")
        
        return "\n".join(result) 