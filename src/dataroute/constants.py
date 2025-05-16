from enum import Enum, auto
import re

# ==============================================================
# ТИПЫ ТОКЕНОВ И УЗЛОВ
# ==============================================================

class TokenType(Enum):
    """Типы токенов в языке DSL"""
    SOURCE = auto()      # Определение источника (sourse=dict)
    TARGET = auto()      # Определение цели (target1=dict("target1"))
    ROUTE_HEADER = auto() # Заголовок маршрута (target1:)
    ROUTE_LINE = auto()  # Строка маршрута ([id] -> |*s1| -> [name](type))
    GLOBAL_VAR = auto()   # Глобальная переменная ($var = value)
    COMMENT = auto()      # Комментарий (# ...)
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
    GLOBAL_VAR = auto()    # Глобальная переменная
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
    VOID_TYPE = auto()             # Ошибка указания типа для void
    UNKNOWN_PIPELINE_SEGMENT = auto()  # Неизвестный сегмент в пайплайне
    UNDEFINED_VAR = auto()         # Неопределенная переменная
    INVALID_VAR_USAGE = auto()     # Неверное использование переменной
    SRC_FIELD_AS_VAR = auto()      # Использование поля из левой части как переменной
    INVALID_TYPE = auto()          # Неверный тип данных
    DUPLICATE_FINAL_NAME = auto()  # Дублирующееся имя финальной цели
    DUPLICATE_TARGET_NAME_TYPE = auto()  # Дублирующееся type/name для цели
    CONDITION_MISSING_IF = auto()  # В выражении может быть только if, но не может быть else без if
    CONDITION_MISSING_PARENTHESIS = auto()  # Условная конструкция должна содержать знак скобок
    CONDITION_EMPTY_EXPRESSION = auto()  # Не найдено логическое выражение внутри условной конструкции
    CONDITION_MISSING_COLON = auto()  # Не найден знак завершения условного выражения (:)
    CONDITION_INVALID = auto()  # Недопустимое или неправильное условное выражение
    FUNC_NOT_FOUND = auto()  # Функция не найдена
    FUNC_CONFLICT = auto()  # Конфликт имён функций


# ==============================================================
# СООТВЕТСТВИЕ ОШИБОК И СООБЩЕНИЙ
# ==============================================================

# Импортируем из локализации после создания модуля
from .localization import Messages as M

# Связь между ErrorType и сообщениями об ошибках
ERROR_MESSAGE_MAP = {
    ErrorType.PIPELINE_CLOSING_BAR: M.Error.PIPELINE_CLOSING_BAR,
    ErrorType.BRACKET_MISSING: M.Error.BRACKET_MISSING,
    ErrorType.FLOW_DIRECTION: M.Error.FLOW_DIRECTION,
    ErrorType.FINAL_TYPE: M.Error.FINAL_TYPE,
    ErrorType.VOID_TYPE: M.Error.VOID_TYPE,
    ErrorType.SYNTAX_SOURCE: M.Error.SYNTAX_SOURCE,
    ErrorType.SYNTAX_TARGET: M.Error.SYNTAX_TARGET,
    ErrorType.SEMANTIC_TARGET: M.Error.SEMANTIC_TARGET,
    ErrorType.SEMANTIC_ROUTES: M.Error.SEMANTIC_ROUTES,
    ErrorType.PIPELINE_EMPTY: M.Error.PIPELINE_EMPTY,
    ErrorType.UNKNOWN: M.Error.UNKNOWN,
    ErrorType.UNKNOWN_PIPELINE_SEGMENT: M.Error.UNKNOWN_PIPELINE_SEGMENT,
    ErrorType.UNDEFINED_VAR: M.Error.UNDEFINED_VAR,
    ErrorType.INVALID_VAR_USAGE: M.Error.INVALID_VAR_USAGE,
    ErrorType.SRC_FIELD_AS_VAR: M.Error.SRC_FIELD_AS_VAR,
    ErrorType.INVALID_TYPE: M.Error.INVALID_TYPE,
    ErrorType.DUPLICATE_FINAL_NAME: M.Error.DUPLICATE_FINAL_NAME,
    ErrorType.DUPLICATE_TARGET_NAME_TYPE: M.Error.DUPLICATE_TARGET_NAME_TYPE,
    ErrorType.CONDITION_MISSING_IF: M.Error.CONDITION_MISSING_IF,
    ErrorType.CONDITION_MISSING_PARENTHESIS: M.Error.CONDITION_MISSING_PARENTHESIS,
    ErrorType.CONDITION_EMPTY_EXPRESSION: M.Error.CONDITION_EMPTY_EXPRESSION,
    ErrorType.CONDITION_MISSING_COLON: M.Error.CONDITION_MISSING_COLON,
    ErrorType.CONDITION_INVALID: M.Error.CONDITION_INVALID,
    ErrorType.FUNC_NOT_FOUND: M.Error.FUNC_NOT_FOUND,
    ErrorType.FUNC_CONFLICT: M.Error.FUNC_CONFLICT
}

# Связь между ErrorType и подсказками
ERROR_HINT_MAP = {
    ErrorType.PIPELINE_CLOSING_BAR: M.Hint.ADD_CLOSING_BAR,
    ErrorType.BRACKET_MISSING: M.Hint.CHECK_BRACKETS,
    ErrorType.FLOW_DIRECTION: M.Hint.USE_FLOW_SYMBOL,
    ErrorType.FINAL_TYPE: M.Hint.SPECIFY_TYPE,
    ErrorType.VOID_TYPE: M.Hint.VOID_NO_TYPE,
    ErrorType.SYNTAX_SOURCE: M.Hint.SOURCE_SYNTAX,
    ErrorType.SYNTAX_TARGET: M.Hint.TARGET_SYNTAX,
    ErrorType.PIPELINE_EMPTY: M.Hint.PIPELINE_MUST_HAVE_CONTENT,
    ErrorType.SEMANTIC_TARGET: M.Hint.TARGET_DEFINITION_MISSING,
    ErrorType.SEMANTIC_ROUTES: M.Hint.ROUTES_MISSING,
    ErrorType.UNKNOWN: None,
    ErrorType.UNKNOWN_PIPELINE_SEGMENT: M.Hint.UNKNOWN_PIPELINE_SEGMENT,
    ErrorType.UNDEFINED_VAR: M.Hint.UNDEFINED_VAR,
    ErrorType.INVALID_VAR_USAGE: M.Hint.INVALID_VAR_USAGE,
    ErrorType.SRC_FIELD_AS_VAR: M.Hint.SRC_FIELD_AS_VAR,
    ErrorType.INVALID_TYPE: M.Hint.INVALID_TYPE,
    ErrorType.DUPLICATE_FINAL_NAME: M.Hint.DUPLICATE_FINAL_NAME,
    ErrorType.DUPLICATE_TARGET_NAME_TYPE: M.Hint.DUPLICATE_TARGET_NAME_TYPE,
    ErrorType.CONDITION_MISSING_IF: M.Hint.CONDITION_MISSING_IF,
    ErrorType.CONDITION_MISSING_PARENTHESIS: M.Hint.CONDITION_MISSING_PARENTHESIS,
    ErrorType.CONDITION_EMPTY_EXPRESSION: M.Hint.CONDITION_EMPTY_EXPRESSION,
    ErrorType.CONDITION_MISSING_COLON: M.Hint.CONDITION_MISSING_COLON,
    ErrorType.CONDITION_INVALID: M.Hint.CONDITION_INVALID,
    ErrorType.FUNC_NOT_FOUND: M.Hint.FUNC_NOT_FOUND,
    ErrorType.FUNC_CONFLICT: M.Hint.FUNC_CONFLICT
}


# ==============================================================
# РЕГУЛЯРНЫЕ ВЫРАЖЕНИЯ ДЛЯ ТОКЕНИЗАЦИИ
# ==============================================================

PATTERNS = {
    # Определение источника: source=тип/путь
    TokenType.SOURCE: r'source\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)\/([^\s]+)$',
    
    # Определение цели: target1=тип/имя_или_путь
    TokenType.TARGET: r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)\/([^\s]+)$',
    
    # Заголовок маршрута: target1:
    TokenType.ROUTE_HEADER: r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:',
    
    # Глобальная переменная: $myVar = "value"
    TokenType.GLOBAL_VAR: r'\$([a-zA-Z][a-zA-Z0-9_]*)\s*=\s*(.*)',
    
    # Комментарий: # This is a comment
    TokenType.COMMENT: r'#(.*)',
    
    # Строка маршрута с отступом: [id] -> |*s1| -> [external_id](str))
    TokenType.ROUTE_LINE: r'^\s*\[([a-zA-Z0-9_]*)\]\s*(?:->|=>|-|>|>>)\s*(?:(\|[^|]*(?:\|[^|]*)*\|)\s*(?:->|=>|-|>|>>)\s*)?\[([$a-zA-Z0-9_]*)\](?:\(([a-zA-Z0-9_]+)\))?'
} 

# ==============================================================
# РАЗРЕШЕННЫЕ ТИПЫ ДАННЫХ
# ==============================================================

# Список разрешенных типов данных в DSL
ALLOWED_TYPES = [
    "str",      # Строка
    "int",      # Целое число
    "float",    # Число с плавающей точкой
    "bool",     # Логическое значение
    "dict",     # Словарь
    "list",     # Список
    "tuple",    # Кортеж
    "set",      # Множество
    "datetime", # Дата и время
    "date",     # Дата
    "time",     # Время
    "Decimal",  # Десятичное число
    "uuid",     # UUID
    "bytes",    # Бинарные данные
    "any"       # Любой тип
] 