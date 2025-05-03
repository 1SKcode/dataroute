from typing import Dict, Optional, Any, Callable


class Messages:
    """Контейнер для сообщений локализации по категориям"""
    
    class Info:
        TOKENIZATION_START = {"ru": "Начинаю токенизацию...", "en": "Starting tokenization..."}
        TOKENIZATION_FINISH = {"ru": "Токенизация завершена. Создано токенов: {count}", "en": "Tokenization completed. Tokens created: {count}"}
        PARSING_START = {"ru": "Начинаю синтаксический анализ...", "en": "Starting parsing..."}
        PARSING_FINISH = {"ru": "Синтаксический анализ завершен. Создано узлов: {count}", "en": "Parsing completed. Nodes created: {count}"}
        NODES_CREATED = {"ru": "Создано узлов: {count}", "en": "Nodes created: {count}"}
        JSON_GENERATED = {"ru": "JSON сгенерирован. {count} целей", "en": "JSON generated. {count} targets"}
        SET_SOURCE_TYPE = {"ru": "Установлен тип источника: {type}", "en": "Source type set: {type}"}
        ROUTE_PROCESSING = {"ru": "Обработка маршрутов для цели: {target}", "en": "Processing routes for target: {target}"}
        ROUTE_ADDED = {"ru": "Добавлен маршрут: {src} -> {dst}({type})", "en": "Route added: {src} -> {dst}({type})"}
        TARGET_ADDED = {"ru": "Добавлена цель: {value} (тип: {type})", "en": "Target added: {value} (type: {type})"}
        PROCESSING_START = {"ru": "=== Начало обработки DSL ===", "en": "=== DSL Processing Started ==="}
        PROCESSING_FINISH = {"ru": "=== Обработка DSL завершена ===", "en": "=== DSL Processing Completed ==="}
        PARSING_ROUTE_BLOCK = {"ru": "Разбор блока маршрутов для {target}", "en": "Parsing route block for {target}"}

    class Warning:
        EMPTY_PIPELINE_SEGMENT = {"ru": "Предупреждение: Обнаружен пустой сегмент пайплайна", "en": "Warning: Empty pipeline segment detected"}

    class Error:
        PIPELINE_CLOSING_BAR = {"ru": "Закрывающая прямая черта пайплайна не найдена", "en": "Pipeline closing bar is missing"}
        BRACKET_MISSING = {"ru": "Квадратная скобка определения сущности не найдена", "en": "Entity definition bracket is missing"}
        FLOW_DIRECTION = {"ru": "Символ направляющего потока не найден. Используйте ->, =>, - или >", "en": "Flow direction symbol is missing. Use ->, =>, - or >"}
        FINAL_TYPE = {"ru": "Финальный тип не задан или задан некорректно", "en": "Final type is not specified or incorrectly specified"}
        SYNTAX_SOURCE = {"ru": "Неверный синтаксис определения источника", "en": "Invalid source definition syntax"}
        SYNTAX_TARGET = {"ru": "Неверный синтаксис определения цели", "en": "Invalid target definition syntax"}
        SEMANTIC_TARGET = {"ru": "Ошибка в определении цели", "en": "Error in target definition"}
        SEMANTIC_ROUTES = {"ru": "Ошибка в определении маршрутов", "en": "Error in route definitions"}
        PIPELINE_EMPTY = {"ru": "Пустой пайплайн обнаружен", "en": "Empty pipeline detected"}
        UNKNOWN = {"ru": "Неизвестная синтаксическая ошибка", "en": "Unknown syntax error"}
        GENERIC = {"ru": "Ошибка при обработке DSL: {message}", "en": "Error processing DSL: {message}"}
        LINE_PREFIX = {"ru": "Ошибка в строке {line_num}:", "en": "Error in line {line_num}:"}

    class Hint:
        ADD_CLOSING_BAR = {"ru": "Добавьте закрывающую вертикальную черту '|'", "en": "Add closing vertical bar '|'"}
        CHECK_BRACKETS = {"ru": "Проверьте правильность открывающих и закрывающих скобок [field]", "en": "Check if brackets are properly opened and closed [field]"}
        USE_FLOW_SYMBOL = {"ru": "Используйте один из символов направления: ->, =>, -, >", "en": "Use one of the flow direction symbols: ->, =>, -, >"}
        SPECIFY_TYPE = {"ru": "Укажите тип в круглых скобках: [field](type)", "en": "Specify type in parentheses: [field](type)"}
        SOURCE_SYNTAX = {"ru": "Используйте sourse=type", "en": "Use sourse=type"}
        TARGET_SYNTAX = {"ru": "Используйте target=type(\"value\")", "en": "Use target=type(\"value\")"}
        PIPELINE_MUST_HAVE_CONTENT = {"ru": "Пайплайн должен содержать хотя бы один символ между вертикальными чертами", "en": "Pipeline must contain at least one character between vertical bars"}
        SEQUENTIAL_PIPELINES = {"ru": "Обнаружены последовательные пайплайны без данных между ними", "en": "Sequential pipelines detected without data between them"}
        TARGET_DEFINITION_MISSING = {"ru": "Не найдено определение цели для маршрута {target}", "en": "Target definition not found for route {target}"}
        ROUTES_MISSING = {"ru": "Отсутствуют определения маршрутов (target:)", "en": "Route definitions are missing (target:)"}
        LABEL = {"ru": "Возможное решение:", "en": "Possible solution:"}

    class Debug:
        TOKEN_CREATED = {"ru": "Токен {type}: {value}", "en": "Token {type}: {value}"}
        PIPELINE_ITEM_ADDED = {"ru": "Добавлен элемент пайплайна: {type} {value}", "en": "Pipeline item added: {type} {value}"}
        ROUTE_LINE_CREATED = {"ru": "Создана строка маршрута: {src} -> ... -> {dst}", "en": "Route line created: {src} -> ... -> {dst}"}


class Localization:
    """Система локализации с поддержкой нескольких языков"""
    
    SUPPORTED_LANGUAGES = ["ru", "en"]
    DEFAULT_LANGUAGE = "ru"
    
    def __init__(self, lang: str = DEFAULT_LANGUAGE):
        self.lang = lang if lang in self.SUPPORTED_LANGUAGES else self.DEFAULT_LANGUAGE
    
    def get(self, message_dict: dict, **kwargs) -> str:
        """Получение локализованного сообщения с подстановкой параметров"""
        if not isinstance(message_dict, dict):
            return f"[Invalid message format: {message_dict}]"
        
        # Получаем сообщение на нужном языке
        if self.lang not in message_dict:
            # Если запрошенного языка нет, используем первый доступный
            lang_key = next(iter(message_dict), None)
            if not lang_key:
                return f"[No translations available for: {message_dict}]"
            text = message_dict[lang_key]
        else:
            text = message_dict[self.lang]
        
        # Подстановка параметров, если они есть
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError as e:
                return f"{text} (Missing parameter: {e})"
        
        return text
    
    def add_language(self, lang_code: str) -> None:
        """Добавляет поддержку нового языка"""
        if lang_code not in self.SUPPORTED_LANGUAGES:
            self.SUPPORTED_LANGUAGES.append(lang_code)
    
    def switch_language(self, lang: str) -> None:
        """Переключает текущий язык"""
        self.lang = lang if lang in self.SUPPORTED_LANGUAGES else self.DEFAULT_LANGUAGE 