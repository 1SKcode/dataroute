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
    ErrorType.UNKNOWN: M.Error.UNKNOWN
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
    ErrorType.UNKNOWN: None
}


# ==============================================================
# РЕГУЛЯРНЫЕ ВЫРАЖЕНИЯ ДЛЯ ТОКЕНИЗАЦИИ
# ==============================================================

PATTERNS = {
    # Определение источника: source=dict
    TokenType.SOURCE: r'source\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)',
    
    # Определение цели: target1=dict("target1")
    TokenType.TARGET: r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*)\)',
    
    # Заголовок маршрута: target1:
    TokenType.ROUTE_HEADER: r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:',
    
    # Глобальная переменная: $myVar = "value"
    TokenType.GLOBAL_VAR: r'\$([a-zA-Z][a-zA-Z0-9_]*)\s*=\s*(.*)',
    
    # Комментарий: # This is a comment
    TokenType.COMMENT: r'#(.*)',
    
    # Строка маршрута с отступом: [id] -> |*s1| -> [external_id](str))
    TokenType.ROUTE_LINE: r'^\s*\[([a-zA-Z0-9_]*)\]\s*(?:->|=>|-|>)\s*(?:(\|[^|]*(?:\|[^|]*)*\|)\s*(?:->|=>|-|>)\s*)?\[([$a-zA-Z0-9_]*)\](?:\(([a-zA-Z0-9_]+)\))?'
} 