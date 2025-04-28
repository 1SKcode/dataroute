import re
import json
import sys
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

# ==============================================================
# ЛОКАЛИЗАЦИЯ И СООБЩЕНИЯ
# ==============================================================

class MessageType(Enum):
    """Типы сообщений в системе"""
    ERROR = auto()        # Сообщения об ошибках
    WARNING = auto()      # Предупреждения
    INFO = auto()         # Информационные сообщения
    DEBUG = auto()        # Отладочные сообщения


class MessageId(Enum):
    """Идентификаторы сообщений"""
    # Общие сообщения
    INFO_TOKENIZATION_START = auto()
    INFO_TOKENIZATION_FINISH = auto()
    INFO_PARSING_START = auto()
    INFO_PARSING_FINISH = auto()
    INFO_NODES_CREATED = auto()
    INFO_JSON_GENERATED = auto()
    INFO_SET_SOURCE_TYPE = auto()
    INFO_ROUTE_PROCESSING = auto()
    INFO_ROUTE_ADDED = auto()
    INFO_TARGET_ADDED = auto()
    INFO_PROCESSING_START = auto()
    INFO_PROCESSING_FINISH = auto()
    INFO_PARSING_ROUTE_BLOCK = auto()
    
    # Предупреждения
    WARN_EMPTY_PIPELINE_SEGMENT = auto()
    
    # Сообщения об ошибках
    ERR_PIPELINE_CLOSING_BAR = auto()
    ERR_BRACKET_MISSING = auto()
    ERR_FLOW_DIRECTION = auto()
    ERR_FINAL_TYPE = auto()
    ERR_SYNTAX_SOURCE = auto()
    ERR_SYNTAX_TARGET = auto()
    ERR_SEMANTIC_TARGET = auto()
    ERR_SEMANTIC_ROUTES = auto()
    ERR_PIPELINE_EMPTY = auto()
    ERR_UNKNOWN = auto()
    ERR_GENERIC = auto()
    ERR_LINE_PREFIX = auto()
    
    # Подсказки/решения
    HINT_ADD_CLOSING_BAR = auto()
    HINT_CHECK_BRACKETS = auto()
    HINT_USE_FLOW_SYMBOL = auto()
    HINT_SPECIFY_TYPE = auto()
    HINT_SOURCE_SYNTAX = auto()
    HINT_TARGET_SYNTAX = auto()
    HINT_PIPELINE_MUST_HAVE_CONTENT = auto()
    HINT_SEQUENTIAL_PIPELINES = auto()
    HINT_TARGET_DEFINITION_MISSING = auto()
    HINT_ROUTES_MISSING = auto()
    HINT_LABEL = auto()
    
    # Отладочные сообщения
    DEBUG_TOKEN_CREATED = auto()
    DEBUG_PIPELINE_ITEM_ADDED = auto()
    DEBUG_ROUTE_LINE_CREATED = auto()


@dataclass
class LocMsg:
    """Сообщение на разных языках"""
    ru: str
    en: str


class Localization:
    """Класс для локализации сообщений"""
    
    def __init__(self, lang: str = "ru"):
        self.lang = lang
        self.messages = self._init_messages()
    
    def _init_messages(self) -> Dict[MessageId, LocMsg]:
        """Инициализация сообщений на разных языках"""
        return {
            # Общие сообщения
            MessageId.INFO_TOKENIZATION_START: LocMsg(
                ru="Начинаю токенизацию...",
                en="Starting tokenization..."
            ),
            MessageId.INFO_TOKENIZATION_FINISH: LocMsg(
                ru="Токенизация завершена. Создано токенов: {count}",
                en="Tokenization completed. Tokens created: {count}"
            ),
            MessageId.INFO_PARSING_START: LocMsg(
                ru="Начинаю синтаксический анализ...",
                en="Starting parsing..."
            ),
            MessageId.INFO_PARSING_FINISH: LocMsg(
                ru="Синтаксический анализ завершен. Создано узлов: {count}",
                en="Parsing completed. Nodes created: {count}"
            ),
            MessageId.INFO_NODES_CREATED: LocMsg(
                ru="Создано узлов: {count}",
                en="Nodes created: {count}"
            ),
            MessageId.INFO_JSON_GENERATED: LocMsg(
                ru="JSON сгенерирован. {count} целей",
                en="JSON generated. {count} targets"
            ),
            MessageId.INFO_SET_SOURCE_TYPE: LocMsg(
                ru="Установлен тип источника: {type}",
                en="Source type set: {type}"
            ),
            MessageId.INFO_ROUTE_PROCESSING: LocMsg(
                ru="Обработка маршрутов для цели: {target}",
                en="Processing routes for target: {target}"
            ),
            MessageId.INFO_ROUTE_ADDED: LocMsg(
                ru="Добавлен маршрут: {src} -> {dst}({type})",
                en="Route added: {src} -> {dst}({type})"
            ),
            MessageId.INFO_TARGET_ADDED: LocMsg(
                ru="Добавлена цель: {value} (тип: {type})",
                en="Target added: {value} (type: {type})"
            ),
            MessageId.INFO_PROCESSING_START: LocMsg(
                ru="=== Начало обработки DSL ===",
                en="=== DSL Processing Started ==="
            ),
            MessageId.INFO_PROCESSING_FINISH: LocMsg(
                ru="=== Обработка DSL завершена ===",
                en="=== DSL Processing Completed ==="
            ),
            MessageId.INFO_PARSING_ROUTE_BLOCK: LocMsg(
                ru="Разбор блока маршрутов для {target}",
                en="Parsing route block for {target}"
            ),
            
            # Предупреждения
            MessageId.WARN_EMPTY_PIPELINE_SEGMENT: LocMsg(
                ru="Предупреждение: Обнаружен пустой сегмент пайплайна",
                en="Warning: Empty pipeline segment detected"
            ),
            
            # Сообщения об ошибках
            MessageId.ERR_PIPELINE_CLOSING_BAR: LocMsg(
                ru="Закрывающая прямая черта пайплайна не найдена",
                en="Pipeline closing bar is missing"
            ),
            MessageId.ERR_BRACKET_MISSING: LocMsg(
                ru="Квадратная скобка определения сущности не найдена",
                en="Entity definition bracket is missing"
            ),
            MessageId.ERR_FLOW_DIRECTION: LocMsg(
                ru="Символ направляющего потока не найден. Используйте ->, =>, -, >",
                en="Flow direction symbol is missing. Use ->, =>, -, >"
            ),
            MessageId.ERR_FINAL_TYPE: LocMsg(
                ru="Финальный тип не задан или задан некорректно",
                en="Final type is not specified or incorrectly specified"
            ),
            MessageId.ERR_SYNTAX_SOURCE: LocMsg(
                ru="Неверный синтаксис определения источника",
                en="Invalid source definition syntax"
            ),
            MessageId.ERR_SYNTAX_TARGET: LocMsg(
                ru="Неверный синтаксис определения цели",
                en="Invalid target definition syntax"
            ),
            MessageId.ERR_SEMANTIC_TARGET: LocMsg(
                ru="Ошибка в определении цели",
                en="Error in target definition"
            ),
            MessageId.ERR_SEMANTIC_ROUTES: LocMsg(
                ru="Ошибка в определении маршрутов",
                en="Error in route definitions"
            ),
            MessageId.ERR_PIPELINE_EMPTY: LocMsg(
                ru="Пустой пайплайн обнаружен",
                en="Empty pipeline detected"
            ),
            MessageId.ERR_UNKNOWN: LocMsg(
                ru="Неизвестная синтаксическая ошибка",
                en="Unknown syntax error"
            ),
            MessageId.ERR_GENERIC: LocMsg(
                ru="Ошибка при обработке DSL: {message}",
                en="Error processing DSL: {message}"
            ),
            MessageId.ERR_LINE_PREFIX: LocMsg(
                ru="Ошибка в строке {line_num}:",
                en="Error in line {line_num}:"
            ),
            
            # Подсказки/решения
            MessageId.HINT_ADD_CLOSING_BAR: LocMsg(
                ru="Добавьте закрывающую вертикальную черту '|'",
                en="Add closing vertical bar '|'"
            ),
            MessageId.HINT_CHECK_BRACKETS: LocMsg(
                ru="Проверьте правильность открывающих и закрывающих скобок [field]",
                en="Check if brackets are properly opened and closed [field]"
            ),
            MessageId.HINT_USE_FLOW_SYMBOL: LocMsg(
                ru="Используйте один из символов направления: ->, =>, -, >",
                en="Use one of the flow direction symbols: ->, =>, -, >"
            ),
            MessageId.HINT_SPECIFY_TYPE: LocMsg(
                ru="Укажите тип в круглых скобках: [field](type)",
                en="Specify type in parentheses: [field](type)"
            ),
            MessageId.HINT_SOURCE_SYNTAX: LocMsg(
                ru="Используйте sourse=type",
                en="Use sourse=type"
            ),
            MessageId.HINT_TARGET_SYNTAX: LocMsg(
                ru="Используйте target=type(\"value\")",
                en="Use target=type(\"value\")"
            ),
            MessageId.HINT_PIPELINE_MUST_HAVE_CONTENT: LocMsg(
                ru="Пайплайн должен содержать хотя бы один символ между вертикальными чертами",
                en="Pipeline must contain at least one character between vertical bars"
            ),
            MessageId.HINT_SEQUENTIAL_PIPELINES: LocMsg(
                ru="Обнаружены последовательные пайплайны без данных между ними",
                en="Sequential pipelines detected without data between them"
            ),
            MessageId.HINT_TARGET_DEFINITION_MISSING: LocMsg(
                ru="Не найдено определение цели для маршрута {target}",
                en="Target definition not found for route {target}"
            ),
            MessageId.HINT_ROUTES_MISSING: LocMsg(
                ru="Отсутствуют определения маршрутов (target:)",
                en="Route definitions are missing (target:)"
            ),
            MessageId.HINT_LABEL: LocMsg(
                ru="Возможное решение:",
                en="Possible solution:"
            ),
            
            # Отладочные сообщения
            MessageId.DEBUG_TOKEN_CREATED: LocMsg(
                ru="Токен {type}: {value}",
                en="Token {type}: {value}"
            ),
            MessageId.DEBUG_PIPELINE_ITEM_ADDED: LocMsg(
                ru="Добавлен элемент пайплайна: {type} {value}",
                en="Pipeline item added: {type} {value}"
            ),
            MessageId.DEBUG_ROUTE_LINE_CREATED: LocMsg(
                ru="Создана строка маршрута: {src} -> ... -> {dst}",
                en="Route line created: {src} -> ... -> {dst}"
            ),
        }
    
    def get(self, message_id: MessageId, **kwargs) -> str:
        """Получение локализованного сообщения с подстановкой параметров"""
        if message_id not in self.messages:
            return f"[Missing message: {message_id}]"
        
        message = self.messages[message_id]
        text = message.ru if self.lang == "ru" else message.en
        
        # Подстановка параметров, если они есть
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError as e:
                return f"{text} (Missing parameter: {e})"
        
        return text

# ==============================================================
# ОБРАБОТКА ОШИБОК
# ==============================================================

class ErrorType(Enum):
    """Типы синтаксических ошибок в DSL"""
    PIPELINE_CLOSING_BAR = auto()  # Отсутствие закрывающей черты пайплайна
    BRACKET_MISSING = auto()       # Ошибка с квадратными скобками
    FLOW_DIRECTION = auto()        # Ошибка символа направления
    FINAL_TYPE = auto()            # Ошибка финального типа
    SYNTAX_SOURCE = auto()         # Ошибка синтаксиса источника
    SYNTAX_TARGET = auto()         # Ошибка синтаксиса цели
    SEMANTIC_TARGET = auto()       # Ошибка семантики цели
    SEMANTIC_ROUTES = auto()       # Ошибка семантики маршрутов
    PIPELINE_EMPTY = auto()        # Пустой пайплайн
    UNKNOWN = auto()               # Неизвестная ошибка


# Связь между ErrorType и MessageId для сообщений об ошибках
ERROR_MESSAGE_MAP = {
    ErrorType.PIPELINE_CLOSING_BAR: MessageId.ERR_PIPELINE_CLOSING_BAR,
    ErrorType.BRACKET_MISSING: MessageId.ERR_BRACKET_MISSING,
    ErrorType.FLOW_DIRECTION: MessageId.ERR_FLOW_DIRECTION,
    ErrorType.FINAL_TYPE: MessageId.ERR_FINAL_TYPE,
    ErrorType.SYNTAX_SOURCE: MessageId.ERR_SYNTAX_SOURCE,
    ErrorType.SYNTAX_TARGET: MessageId.ERR_SYNTAX_TARGET,
    ErrorType.SEMANTIC_TARGET: MessageId.ERR_SEMANTIC_TARGET,
    ErrorType.SEMANTIC_ROUTES: MessageId.ERR_SEMANTIC_ROUTES,
    ErrorType.PIPELINE_EMPTY: MessageId.ERR_PIPELINE_EMPTY,
    ErrorType.UNKNOWN: MessageId.ERR_UNKNOWN
}

# Связь между ErrorType и MessageId для подсказок
ERROR_HINT_MAP = {
    ErrorType.PIPELINE_CLOSING_BAR: MessageId.HINT_ADD_CLOSING_BAR,
    ErrorType.BRACKET_MISSING: MessageId.HINT_CHECK_BRACKETS,
    ErrorType.FLOW_DIRECTION: MessageId.HINT_USE_FLOW_SYMBOL,
    ErrorType.FINAL_TYPE: MessageId.HINT_SPECIFY_TYPE,
    ErrorType.SYNTAX_SOURCE: MessageId.HINT_SOURCE_SYNTAX,
    ErrorType.SYNTAX_TARGET: MessageId.HINT_TARGET_SYNTAX,
    ErrorType.PIPELINE_EMPTY: MessageId.HINT_PIPELINE_MUST_HAVE_CONTENT,
    ErrorType.SEMANTIC_TARGET: MessageId.HINT_TARGET_DEFINITION_MISSING,
    ErrorType.SEMANTIC_ROUTES: MessageId.HINT_ROUTES_MISSING,
    ErrorType.UNKNOWN: None
}


class DSLSyntaxError(Exception):
    """Базовый класс для всех синтаксических ошибок DSL"""
    
    def __init__(self, 
                 error_type: ErrorType,
                 line: str,
                 line_num: int,
                 position: Optional[int] = None,
                 suggestion: Optional[str] = None,
                 lang: str = "ru"):
        self.error_type = error_type
        self.line = line
        self.line_num = line_num
        self.position = position or self._guess_error_position(line)
        self.suggestion = suggestion
        self.lang = lang
        self.loc = Localization(lang)
        
        # Формируем сообщение об ошибке
        message = self._format_error_message()
        super().__init__(message)
    
    def _guess_error_position(self, line: str) -> int:
        """Пытается угадать позицию ошибки в строке"""
        # Это базовая реализация, в подклассах может быть более сложная логика
        return 0  
    
    def _format_error_message(self) -> str:
        """Форматирует сообщение об ошибке"""
        # Получаем соответствующее сообщение об ошибке
        message_id = ERROR_MESSAGE_MAP.get(self.error_type, MessageId.ERR_UNKNOWN)
        message = self.loc.get(message_id)
        
        # Форматируем строку с указателем на позицию ошибки
        pointer = " " * self.position + "^"
        
        result = [
            self.loc.get(MessageId.ERR_LINE_PREFIX, line_num=self.line_num),
            f"{self.line}",
            f"{pointer}",
            f"{message}",
        ]
        
        # Если есть подсказка, добавляем её
        if self.suggestion:
            hint_label = self.loc.get(MessageId.HINT_LABEL)
            result.append(f"{hint_label} {self.suggestion}")
        # Иначе пробуем использовать стандартную подсказку для данного типа ошибки
        elif ERROR_HINT_MAP.get(self.error_type):
            hint_id = ERROR_HINT_MAP.get(self.error_type)
            if hint_id:
                hint_label = self.loc.get(MessageId.HINT_LABEL)
                hint = self.loc.get(hint_id, target=self.line if self.error_type == ErrorType.SEMANTIC_TARGET else None)
                result.append(f"{hint_label} {hint}")
        
        return "\n".join(result)


class PipelineClosingBarError(DSLSyntaxError):
    """Ошибка отсутствия закрывающей черты пайплайна"""
    
    def __init__(self, line: str, line_num: int, position: Optional[int] = None, lang: str = "ru"):
        super().__init__(ErrorType.PIPELINE_CLOSING_BAR, line, line_num, position, None, lang)
    
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
    
    def __init__(self, line: str, line_num: int, position: Optional[int] = None, lang: str = "ru"):
        super().__init__(ErrorType.BRACKET_MISSING, line, line_num, position, None, lang)
    
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
    
    def __init__(self, line: str, line_num: int, position: Optional[int] = None, lang: str = "ru"):
        super().__init__(ErrorType.FLOW_DIRECTION, line, line_num, position, None, lang)
    
    def _guess_error_position(self, line: str) -> int:
        # Ищем позицию после ']', где должна быть стрелка
        bracket_close_pos = line.find(']')
        if bracket_close_pos != -1:
            return bracket_close_pos + 1
        return 0


class FinalTypeError(DSLSyntaxError):
    """Ошибка финального типа"""
    
    def __init__(self, line: str, line_num: int, position: Optional[int] = None, lang: str = "ru"):
        super().__init__(ErrorType.FINAL_TYPE, line, line_num, position, None, lang)
    
    def _guess_error_position(self, line: str) -> int:
        # Ищем последнюю скобку ']' и затем проверяем наличие '('
        last_bracket_pos = line.rfind(']')
        if last_bracket_pos != -1:
            return last_bracket_pos + 1
        return len(line) - 1


class PipelineEmptyError(DSLSyntaxError):
    """Ошибка пустого пайплайна"""
    
    def __init__(self, line: str, line_num: int, position: Optional[int] = None, lang: str = "ru"):
        super().__init__(ErrorType.PIPELINE_EMPTY, line, line_num, position, None, lang)
    
    def _guess_error_position(self, line: str) -> int:
        # Находим позицию пустого пайплайна "||"
        empty_pipeline_match = re.search(r'\|\|', line)
        if empty_pipeline_match:
            return empty_pipeline_match.start() + 1
        return 0


class SyntaxErrorHandler:
    """Обработчик синтаксических ошибок DSL"""
    
    def __init__(self, lang: str = "ru"):
        self.lang = lang
        self.loc = Localization(lang)
        
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
            "source_syntax": r'sourse\s+\w+',
            
            # Для проверки синтаксиса цели
            "target_syntax": r'=\s*\w+\s*\[\s*["\'](.*?)["\']'
        }
    
    def analyze(self, line: str, line_num: int) -> DSLSyntaxError:
        """Анализирует строку и возвращает соответствующую ошибку"""
        # Проверяем на различные типы ошибок
        
        # 0. Проверка на пустой пайплайн
        if re.search(self.patterns["pipeline_empty"], line):
            pos = re.search(self.patterns["pipeline_empty"], line).start() + 1
            return PipelineEmptyError(line, line_num, pos, self.lang)
        
        # 0.1 Проверка на последовательные пайплайны
        if re.search(self.patterns["pipeline_sequential"], line):
            pos = re.search(self.patterns["pipeline_sequential"], line).end() - 1
            return DSLSyntaxError(ErrorType.PIPELINE_EMPTY, line, line_num, pos, self.loc.get(MessageId.HINT_SEQUENTIAL_PIPELINES), self.lang)
        
        # 0.2 Проверка синтаксиса определения источника и цели
        if re.match(self.patterns["source_syntax"], line):
            # Отсутствует знак = в определении источника
            pos = line.find('sourse') + len('sourse')
            return DSLSyntaxError(ErrorType.SYNTAX_SOURCE, line, line_num, pos, None, self.lang)
        
        if re.search(self.patterns["target_syntax"], line):
            # Неверные скобки в определении цели
            pos = line.find('[')
            return DSLSyntaxError(ErrorType.SYNTAX_TARGET, line, line_num, pos, None, self.lang)
        
        # 1. Проверка на финальный тип
        if ']' in line and '->' in line:  # Убедимся, что это строка маршрута
            last_bracket_pos = line.rfind(']')
            # После последней ] должна быть (
            if last_bracket_pos != -1 and ('(' not in line[last_bracket_pos:]):
                return FinalTypeError(line, line_num, last_bracket_pos + 1, self.lang)
        
        # 2. Проверка на символ направления
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
            return FlowDirectionError(line, line_num, direction_pos, self.lang)
        
        # 3. Проверка на незакрытый пайплайн
        pipe_count = line.count('|')
        if pipe_count > 0 and pipe_count % 2 != 0:
            # Найти позицию последней вертикальной черты
            last_pipe_pos = line.rfind('|')
            return PipelineClosingBarError(line, line_num, last_pipe_pos, self.lang)
        
        # 4. Проверка на неправильные скобки
        if line.count('[') != line.count(']'):
            if line.count('[') > line.count(']'):
                # Если открывающих скобок больше
                for match in re.finditer(r'\[', line):
                    start_pos = match.start()
                    # Проверяем, есть ли для этой скобки закрывающая
                    remaining = line[start_pos+1:]
                    if ']' not in remaining:
                        return BracketMissingError(line, line_num, start_pos, self.lang)
            else:
                # Если закрывающих скобок больше
                for match in re.finditer(r'\]', line):
                    end_pos = match.start()
                    preceding = line[:end_pos]
                    if preceding.count('[') < preceding.count(']') + 1:
                        return BracketMissingError(line, line_num, end_pos, self.lang)
        
        # Проверка отсутствия открывающей скобки
        opening_bracket_missing = re.search(r'(?<!\[)(\w+)\]', line)
        if opening_bracket_missing:
            pos = opening_bracket_missing.start(1)
            return BracketMissingError(line, line_num, pos, self.lang)
        
        # Если не удалось определить конкретную ошибку
        return DSLSyntaxError(ErrorType.UNKNOWN, line, line_num, 0, None, self.lang)


# ==============================================================
# КОНСТАНТЫ И ПЕРЕЧИСЛЕНИЯ
# ==============================================================

class TokenType(Enum):
    """Типы токенов в языке DSL"""
    SOURCE = auto()      # Определение источника (sourse=dict)
    TARGET = auto()      # Определение цели (target1=dict("target1"))
    ROUTE_HEADER = auto() # Заголовок маршрута (target1:)
    ROUTE_LINE = auto()  # Строка маршрута ([id] -> |*s1| -> [name](type))
    CONDITION = auto()   # Условное выражение (if (exp) : (else))
    EVENT = auto()       # Событие (ROLLBACK, SKIP, NOTIFY)


class NodeType(Enum):
    """Типы узлов AST"""
    PROGRAM = auto()      # Корневой узел программы
    SOURCE = auto()       # Определение источника
    TARGET = auto()       # Определение цели
    ROUTE_BLOCK = auto()  # Блок маршрутов
    ROUTE_LINE = auto()   # Строка маршрута
    PIPELINE = auto()     # Конвейер обработки
    FIELD_SRC = auto()    # Исходное поле
    FIELD_DST = auto()    # Целевое поле
    CONDITION = auto()    # Условное выражение
    EVENT = auto()        # Событие
    FUNC_CALL = auto()    # Вызов функции
    DIRECT_MAP = auto()   # Прямое отображение


class PipelineItemType(Enum):
    """Типы элементов конвейера"""
    PY_FUNC = "py_func"   # Функция Python с *
    DIRECT = "direct"     # Прямое отображение
    CONDITION = "condition" # Условный оператор
    EVENT = "event"       # Событие


# ==============================================================
# РЕГУЛЯРНЫЕ ВЫРАЖЕНИЯ ДЛЯ ТОКЕНИЗАЦИИ
# ==============================================================

PATTERNS = {
    # Определение источника: sourse=dict
    TokenType.SOURCE: r'sourse\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)',
    
    # Определение цели: target1=dict("target1")
    TokenType.TARGET: r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*)\)',
    
    # Заголовок маршрута: target1:
    TokenType.ROUTE_HEADER: r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:',
    
    # Строка маршрута с отступом: [id] -> |*s1| -> [external_id](str))
    TokenType.ROUTE_LINE: r'^\s*\[([a-zA-Z0-9_]*)\]\s*(?:->|=>|-|>)\s*(?:(\|[^|]*(?:\|[^|]*)*\|)\s*(?:->|=>|-|>)\s*)?\[([a-zA-Z0-9_]+)\]\(([a-zA-Z0-9_]+)\)'
}


# ==============================================================
# БАЗОВЫЕ КЛАССЫ
# ==============================================================

@dataclass
class Token:
    """Токен, полученный при лексическом анализе"""
    type: TokenType
    value: Any
    position: int = 0
    
    def __repr__(self):
        return f"Token({self.type.name}, {self.value})"


class ASTNode(ABC):
    """Базовый класс для узла абстрактного синтаксического дерева"""
    node_type: NodeType
    
    @abstractmethod
    def accept(self, visitor):
        """Принимает посетителя для обхода дерева"""
        pass


class ASTVisitor(ABC):
    """Базовый класс для посетителя AST"""
    
    @abstractmethod
    def visit_program(self, node):
        pass
    
    @abstractmethod
    def visit_source(self, node):
        pass
    
    @abstractmethod
    def visit_target(self, node):
        pass
    
    @abstractmethod
    def visit_route_block(self, node):
        pass
    
    @abstractmethod
    def visit_route_line(self, node):
        pass
    
    @abstractmethod
    def visit_pipeline(self, node):
        pass
    
    @abstractmethod
    def visit_field_src(self, node):
        pass
    
    @abstractmethod
    def visit_field_dst(self, node):
        pass


class DataSourceStrategy(ABC):
    """Стратегия для работы с различными источниками данных"""
    
    @abstractmethod
    def read_field(self, field_name: str, data: Any) -> Any:
        """Чтение поля из источника данных"""
        pass


# ==============================================================
# КОНКРЕТНЫЕ УЗЛЫ AST
# ==============================================================

@dataclass
class ProgramNode(ASTNode):
    """Корневой узел программы"""
    children: List[ASTNode] = field(default_factory=list)
    node_type: NodeType = NodeType.PROGRAM
    
    def accept(self, visitor):
        return visitor.visit_program(self)


@dataclass
class SourceNode(ASTNode):
    """Узел определения источника данных"""
    source_type: str
    node_type: NodeType = NodeType.SOURCE
    
    def accept(self, visitor):
        return visitor.visit_source(self)


@dataclass
class TargetNode(ASTNode):
    """Узел определения цели"""
    name: str
    target_type: str
    value: str
    node_type: NodeType = NodeType.TARGET
    
    def accept(self, visitor):
        return visitor.visit_target(self)


@dataclass
class RouteBlockNode(ASTNode):
    """Блок маршрутов для конкретной цели"""
    target_name: str
    routes: List['RouteLineNode'] = field(default_factory=list)
    node_type: NodeType = NodeType.ROUTE_BLOCK
    
    def accept(self, visitor):
        return visitor.visit_route_block(self)


@dataclass
class FieldSrcNode(ASTNode):
    """Исходное поле"""
    name: str
    node_type: NodeType = NodeType.FIELD_SRC
    
    def accept(self, visitor):
        return visitor.visit_field_src(self)


@dataclass
class FieldDstNode(ASTNode):
    """Целевое поле"""
    name: str
    type_name: str
    node_type: NodeType = NodeType.FIELD_DST
    
    def accept(self, visitor):
        return visitor.visit_field_dst(self)


@dataclass
class PipelineItemNode(ASTNode):
    """Элемент конвейера обработки"""
    item_type: PipelineItemType
    value: str
    params: Dict[str, str] = field(default_factory=lambda: {"param": "$this"})
    
    def accept(self, visitor):
        if self.item_type == PipelineItemType.PY_FUNC:
            return visitor.visit_func_call(self)
        elif self.item_type == PipelineItemType.DIRECT:
            return visitor.visit_direct_map(self)
        elif self.item_type == PipelineItemType.CONDITION:
            return visitor.visit_condition(self)
        elif self.item_type == PipelineItemType.EVENT:
            return visitor.visit_event(self)


@dataclass
class PipelineNode(ASTNode):
    """Конвейер обработки"""
    items: List[PipelineItemNode] = field(default_factory=list)
    node_type: NodeType = NodeType.PIPELINE
    
    def accept(self, visitor):
        return visitor.visit_pipeline(self)


@dataclass
class RouteLineNode(ASTNode):
    """Строка маршрута"""
    src_field: FieldSrcNode
    pipeline: PipelineNode
    target_field: Optional[FieldDstNode] = None
    node_type: NodeType = NodeType.ROUTE_LINE
    
    def accept(self, visitor):
        return visitor.visit_route_line(self)


# ==============================================================
# ЛЕКСИЧЕСКИЙ АНАЛИЗАТОР
# ==============================================================

class Lexer:
    """Лексический анализатор для преобразования текста в токены"""
    
    def __init__(self, debug=False, lang="ru"):
        self.tokens = []
        self.debug = debug
        self.error_handler = SyntaxErrorHandler(lang)
        self.lang = lang
        self.loc = Localization(lang)

    def _strip_quotes(self, s):
        if len(s) >= 2 and s[0] == s[-1] and s[0] in {"'", '"'}:
            return s[1:-1]
        return s
    
    def tokenize(self, text: str) -> List[Token]:
        """Разбивает текст на токены"""
        self.tokens = []
        lines = text.strip().split('\n')
        
        if self.debug:
            print(self.loc.get(MessageId.INFO_TOKENIZATION_START))
        
        for line_num, line in enumerate(lines, 1):
            original_line = line
            line = line.strip()
            if not line:
                continue
            
            # Проверка на пустой пайплайн до токенизации
            if '||' in original_line:
                error = PipelineEmptyError(original_line, line_num, original_line.find('||') + 1, self.lang)
                print(error)
                sys.exit(1)
                
            # Анализируем строку на соответствие шаблонам
            matched = False
            
            # Определение источника (sourse=dict)
            if not matched:
                match = re.match(PATTERNS[TokenType.SOURCE], line)
                if match:
                    self.tokens.append(Token(TokenType.SOURCE, match.group(1), line_num))
                    if self.debug:
                        print(self.loc.get(MessageId.DEBUG_TOKEN_CREATED, type=TokenType.SOURCE.name, value=match.group(1)))
                    matched = True
            
            # Определение цели (target1=dict("target1"))
            if not matched:
                match = re.match(PATTERNS[TokenType.TARGET], line)
                if match:
                    target_info = {
                        'name': match.group(1),
                        'type': match.group(2),
                        'value': self._strip_quotes(match.group(3)) 
                    }
                    self.tokens.append(Token(TokenType.TARGET, target_info, line_num))
                    if self.debug:
                        print(self.loc.get(MessageId.DEBUG_TOKEN_CREATED, type=TokenType.TARGET.name, value=target_info))
                    matched = True
            
            # Заголовок маршрута (target1:)
            if not matched:
                match = re.match(PATTERNS[TokenType.ROUTE_HEADER], line)
                if match:
                    self.tokens.append(Token(TokenType.ROUTE_HEADER, match.group(1), line_num))
                    if self.debug:
                        print(self.loc.get(MessageId.DEBUG_TOKEN_CREATED, type=TokenType.ROUTE_HEADER.name, value=match.group(1)))
                    matched = True
            
            # Строка маршрута с отступом
            if not matched:
                match = re.match(PATTERNS[TokenType.ROUTE_LINE], original_line)
                if match:
                    route_info = {
                        'src_field': match.group(1),
                        'pipeline': match.group(2),
                        'target_field': match.group(3),
                        'target_field_type': match.group(4)
                    }
                    
                    self.tokens.append(Token(TokenType.ROUTE_LINE, route_info, line_num))
                    if self.debug:
                        print(self.loc.get(MessageId.DEBUG_TOKEN_CREATED, type=TokenType.ROUTE_LINE.name, value=route_info))
                    matched = True
            
            if not matched:
                # Вместо простого вывода ошибки, используем обработчик ошибок
                error = self.error_handler.analyze(line, line_num)
                # Выводим ошибку и прерываем выполнение
                print(error)
                sys.exit(1)
        
        if self.debug:
            print(self.loc.get(MessageId.INFO_TOKENIZATION_FINISH, count=len(self.tokens)))
        
        return self.tokens


# ==============================================================
# СИНТАКСИЧЕСКИЙ АНАЛИЗАТОР
# ==============================================================

class Parser:
    """Синтаксический анализатор для построения AST из токенов"""
    
    def __init__(self, debug=False, lang="ru"):
        self.tokens = []
        self.position = 0
        self.debug = debug
        self.targets = {}  # Сохраняем таргеты по имени
        self.lang = lang
        self.error_handler = SyntaxErrorHandler(lang)
        self.loc = Localization(lang)
    
    def parse(self, tokens: List[Token]) -> ProgramNode:
        """Создает AST из токенов"""
        self.tokens = tokens
        self.position = 0
        program = ProgramNode()
        if self.debug:
            print(self.loc.get(MessageId.INFO_PARSING_START))
        
        # Проверка на наличие хотя бы одного определения источника
        source_found = False
        for token in tokens:
            if token.type == TokenType.SOURCE:
                source_found = True
                break
        
        if not source_found:
            error_line = "sourse= (missing)"
            raise DSLSyntaxError(ErrorType.SYNTAX_SOURCE, error_line, 0, 0, None, self.lang)
        
        while self.position < len(self.tokens):
            token = self.tokens[self.position]
            if token.type == TokenType.SOURCE:
                program.children.append(self._parse_source())
            elif token.type == TokenType.TARGET:
                target_node = self._parse_target()
                self.targets[target_node.name] = target_node
            elif token.type == TokenType.ROUTE_HEADER:
                route_block = self._parse_route_block()
                
                # Проверка наличия определения цели для маршрута
                if route_block.target_name not in self.targets:
                    error_line = f"{route_block.target_name}:"
                    hint = self.loc.get(MessageId.HINT_TARGET_DEFINITION_MISSING, target=route_block.target_name)
                    raise DSLSyntaxError(ErrorType.SEMANTIC_TARGET, error_line, token.position, 0, hint, self.lang)
                
                program.children.append(route_block)
            else:
                self.position += 1
        
        # Сохраняем targets в program для дальнейшего использования
        program._targets = self.targets
        
        # Проверка на наличие хотя бы одного определения маршрута
        route_blocks = [node for node in program.children if node.node_type == NodeType.ROUTE_BLOCK]
        if not route_blocks:
            error_line = "target: (missing)"
            raise DSLSyntaxError(ErrorType.SEMANTIC_ROUTES, error_line, 0, 0, None, self.lang)
        
        if self.debug:
            print(self.loc.get(MessageId.INFO_PARSING_FINISH, count=len(program.children)))
        
        return program
    
    def _parse_source(self) -> SourceNode:
        """Создает узел источника данных"""
        token = self.tokens[self.position]
        self.position += 1
        return SourceNode(token.value)
    
    def _parse_target(self) -> TargetNode:
        """Создает узел цели"""
        token = self.tokens[self.position]
        self.position += 1
        return TargetNode(
            token.value['name'],
            token.value['type'],
            token.value['value']
        )
    
    def _parse_route_block(self) -> RouteBlockNode:
        """Создает блок маршрутов"""
        token = self.tokens[self.position]
        target_name = token.value
        self.position += 1
        
        route_block = RouteBlockNode(target_name)
        
        if self.debug:
            print(self.loc.get(MessageId.INFO_PARSING_ROUTE_BLOCK, target=target_name))
        
        # Собираем все строки маршрутов для этого блока
        while self.position < len(self.tokens) and self.tokens[self.position].type == TokenType.ROUTE_LINE:
            route_line = self._parse_route_line()
            route_block.routes.append(route_line)
        
        return route_block
    
    def _parse_route_line(self) -> RouteLineNode:
        """Создает строку маршрута"""
        token = self.tokens[self.position]
        route_data = token.value
        self.position += 1
        
        # Исходное поле
        src_field = FieldSrcNode(route_data['src_field'])
        
        # Конвейер обработки
        pipeline = self._parse_pipeline(route_data['pipeline'])
        
        # Целевое поле (может отсутствовать)
        target_field = None
        if route_data['target_field'] is not None:
            target_field = FieldDstNode(
                route_data['target_field'],
                route_data['target_field_type'] or 'str'
            )
        
        if self.debug:
            print(self.loc.get(MessageId.DEBUG_ROUTE_LINE_CREATED, 
                             src=src_field.name, 
                             dst=target_field.name if target_field else '-'))
        
        return RouteLineNode(src_field, pipeline, target_field)
    
    def _parse_pipeline(self, pipeline_str: str) -> PipelineNode:
        """Создает конвейер обработки"""
        if pipeline_str is None:
            return PipelineNode()
        
        # Удаляем начальный и конечный |
        if pipeline_str.startswith('|') and pipeline_str.endswith('|'):
            pipeline_content = pipeline_str[1:-1]
        else:
            pipeline_content = pipeline_str
        
        # Разбиваем на элементы
        pipeline = PipelineNode()
        
        if pipeline_content:
            # Проверка на пустое содержимое пайплайна
            segments = pipeline_content.split('|')
            
            for segment in segments:
                segment = segment.strip()
                if not segment and self.debug:
                    print(self.loc.get(MessageId.WARN_EMPTY_PIPELINE_SEGMENT))
                
                if not segment:
                    continue
                
                if segment.startswith('*'):
                    # Функция Python
                    pipeline.items.append(PipelineItemNode(
                        PipelineItemType.PY_FUNC,
                        segment
                    ))
                    if self.debug:
                        print(self.loc.get(MessageId.DEBUG_PIPELINE_ITEM_ADDED, 
                                         type=PipelineItemType.PY_FUNC.value, 
                                         value=segment))
                else:
                    # Прямое отображение
                    pipeline.items.append(PipelineItemNode(
                        PipelineItemType.DIRECT,
                        segment
                    ))
                    if self.debug:
                        print(self.loc.get(MessageId.DEBUG_PIPELINE_ITEM_ADDED, 
                                         type=PipelineItemType.DIRECT.value, 
                                         value=segment))
        
        return pipeline


# ==============================================================
# ПОСЕТИТЕЛИ AST
# ==============================================================

class JSONGenerator(ASTVisitor):
    """Посетитель для генерации JSON из AST"""
    
    def __init__(self, debug=False, lang="ru"):
        self.result = {}
        self.source_type = None
        self.current_target = None
        self.void_counters = {}
        self.target_name_map = {}
        self.target_info_map = {}  # Сохраняем инфу о таргетах
        self.debug = debug
        self.lang = lang
        self.loc = Localization(lang)
    
    def visit_program(self, node):
        """Обход корневого узла программы"""
        # Собираем карту таргетов (name -> TargetNode)
        self.target_info_map = getattr(node, '_targets', {})
        for name, target_node in self.target_info_map.items():
            self.target_name_map[name] = target_node.value
        for child in node.children:
            child.accept(self)
        if self.debug:
            print(self.loc.get(MessageId.INFO_JSON_GENERATED, count=len(self.result)))
        return self.result
    
    def visit_source(self, node):
        """Обход узла источника данных"""
        self.source_type = node.source_type
        if self.debug:
            print(self.loc.get(MessageId.INFO_SET_SOURCE_TYPE, type=self.source_type))
    
    def visit_target(self, node):
        # Не добавляем ключ в self.result, только сохраняем target_name_map
        self.target_name_map[node.name] = node.value
        if self.debug:
            print(self.loc.get(MessageId.INFO_TARGET_ADDED, value=node.value, type=node.target_type))
    
    def visit_route_block(self, node):
        """Обход блока маршрутов"""
        target_name = node.target_name
        # Получаем инфу о таргете
        target_node = self.target_info_map.get(target_name)
        if target_node:
            target_key = target_node.value
            self.target_name_map[target_name] = target_key
            # Если ключа ещё нет, создаём его (в нужном порядке)
            if target_key not in self.result:
                self.result[target_key] = {
                    "sourse_type": self.source_type,
                    "target_type": target_node.target_type,
                    "routes": {}
                }
            self.current_target = target_key
        else:
            # Фоллбек, если вдруг не нашли
            self.current_target = target_name
        if self.debug:
            print(self.loc.get(MessageId.INFO_ROUTE_PROCESSING, target=self.current_target))
        # Обрабатываем все маршруты
        for route in node.routes:
            route.accept(self)
    
    def visit_route_line(self, node):
        """Обход строки маршрута"""
        # Получаем данные о маршруте
        src_field = node.src_field.accept(self)
        pipeline = node.pipeline.accept(self)
        
        # Если целевое поле не указано, используем исходное
        if node.target_field:
            target_field, target_field_type = node.target_field.accept(self)
        else:
            target_field = src_field
            target_field_type = "str"
        
        # Для пустого исходного поля создаем специальный ключ
        route_key = src_field if src_field else self._get_void_key()
        
        # Добавляем маршрут в результат
        if self.current_target in self.result:
            self.result[self.current_target]["routes"][route_key] = {
                "pipeline": pipeline,
                "final_type": target_field_type,
                "final_name": target_field
            }
            
            if self.debug:
                print(self.loc.get(MessageId.INFO_ROUTE_ADDED, 
                                 src=route_key, 
                                 dst=target_field, 
                                 type=target_field_type))
    
    def visit_pipeline(self, node):
        """Обход конвейера обработки"""
        if not node.items:
            return None
        result = {}
        for idx, item in enumerate(node.items, 1):
            result[str(idx)] = item.accept(self)
        return result
    
    def visit_field_src(self, node):
        """Обход исходного поля"""
        return node.name
    
    def visit_field_dst(self, node):
        """Обход целевого поля"""
        return node.name, node.type_name
    
    def visit_func_call(self, node):
        """Обход вызова функции"""
        return {
            "type": PipelineItemType.PY_FUNC.value,
            "param": node.params.get("param", "$this"),
            "full_str": node.value
        }
    
    def visit_direct_map(self, node):
        """Обход прямого отображения"""
        return {
            "type": PipelineItemType.DIRECT.value,
            "param": node.params.get("param", "$this"),
            "full_str": node.value
        }
    
    def visit_condition(self, node):
        """Обход условного выражения"""
        return {
            "type": PipelineItemType.CONDITION.value,
            "condition": node.value,
            "params": node.params
        }
    
    def visit_event(self, node):
        """Обход события"""
        return {
            "type": PipelineItemType.EVENT.value,
            "event": node.value,
            "params": node.params
        }
    
    def _get_void_key(self):
        """Создает ключ для пустого исходного поля"""
        if self.current_target not in self.void_counters:
            self.void_counters[self.current_target] = 0
        
        self.void_counters[self.current_target] += 1
        return f"__void{self.void_counters[self.current_target]}"


# ==============================================================
# ИНТЕРПРЕТАТОР
# ==============================================================

class DataRouteParser:
    """Класс для парсинга и интерпретации DSL"""
    
    def __init__(self, debug=False, lang="ru"):
        self.lexer = Lexer(debug, lang)
        self.parser = Parser(debug, lang)
        self.json_generator = JSONGenerator(debug, lang)
        self.debug = debug
        self.lang = lang
        self.loc = Localization(lang)
    
    def parse(self, text: str) -> Dict:
        """Обрабатывает DSL и возвращает структуру JSON"""
        if self.debug:
            print(self.loc.get(MessageId.INFO_PROCESSING_START))
        
        try:
            # Этап 1: Лексический анализ
            tokens = self.lexer.tokenize(text)
            
            # Этап 2: Синтаксический анализ
            ast = self.parser.parse(tokens)
            
            # Этап 3: Обход AST и генерация JSON
            result = ast.accept(self.json_generator)
            
            if self.debug:
                print(self.loc.get(MessageId.INFO_PROCESSING_FINISH))
            
            return result
            
        except DSLSyntaxError as e:
            # Выводим ошибку в красивом формате
            print(e)
            sys.exit(1)
        except Exception as e:
            # Для других ошибок выводим стандартное сообщение
            print(self.loc.get(MessageId.ERR_GENERIC, message=str(e)))
            if self.debug:
                import traceback
                traceback.print_exc()
            sys.exit(1)


# ==============================================================
# ИСПОЛЬЗОВАНИЕ
# ==============================================================

if __name__ == "__main__":
    # Корректный пример
    correct_input = """
sourse=dict

target2=postgres("parser.norm_data")
target1=dict("target_new")

target1:
    [id] -> [external_id](str)
    [name] => |*lower| - [low_name](str)
    [age] - |*check_age| -> [age](int)
    [test1] -> [test_NORM](str)

target2:
    [id] -> |id| -> [id](str)
    [name] -> |*s1|*upper| -> [name](str)
    [] -> |*gen_rand_int| -> [score](int)
    [] -> |*gen_rand_int| -> [score2](int)
"""

    # Примеры с ошибками
    errors = [
        # Ошибка: ______
        """
sourse=dict
target1=dict("target1")
target1:
    [id] -> |*pipe| -> || -> [field](str)
""",
        # Ошибка: Квадратная скобка не закрыта
        """
sourse=dict
target1=dict("target1")
target1:
    [id -> |*pipe| -> [field](str)
""",
        # Ошибка: Отсутствие символа направления
        """
sourse=dict
target1=dict("target1")
target1:
    [id] |*pipe| -> [field](str)
""",
        # Ошибка: Финальный тип не указан
        """
sourse=dict
target1=dict("target1")
target1:
    [id] -> |*pipe| -> [field]
""",
        # Ошибка: Отсутствует открывающая скобка
        """
sourse=dict
target1=dict("target1")
target1:
    id] -> |*pipe| -> [field](str)
""",
        # Ошибка: Некорректный синтаксис в определении источника и цели
        """
sourse dict
target1=dict["target1"]
target1:
    [id] -> |*pipe| -> [field](str)
""",
        # Ошибка: Отсутствие определения цели для маршрута
        """
sourse=dict
target1=dict("target1")
undefined_target:
    [id] -> |*pipe| -> [field](str)
""",
        # Ошибка: Отсутствие маршрутов
        """
sourse=dict
target1=dict("target1")
"""
    ]

    # Создаем парсер с включенной отладкой
    parser = DataRouteParser(debug=True, lang="ru")
    
    try:
        # Обрабатываем корректный DSL
        print("\n=== ОБРАБОТКА КОРРЕКТНОГО DSL ===")
        result = parser.parse(correct_input)
        
        # Выводим результат
        print(json.dumps(result, indent=2))
        
        # Демонстрация обработки ошибок
        print("\n=== ДЕМОНСТРАЦИЯ ОБРАБОТКИ ОШИБОК ===")
        for i, error_input in enumerate(errors, 1):
            print(f"\n--- ПРИМЕР ОШИБКИ #{i} ---")
            try:
                parser.parse(error_input)
            except SystemExit:
                # Перехватываем sys.exit(1) для продолжения демонстрации
                pass
            
    except Exception as e:
        print(f"Ошибка при обработке примеров: {e}")
        import traceback
        traceback.print_exc() 