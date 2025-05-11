from typing import Dict, Optional, Any, Callable


class Messages:
    """Контейнер для сообщений локализации по категориям"""
    
    class Info:
        PROCESSING_START = {"ru": "=== >Y<Начало обработки DSL>RS< ===", "en": "=== >Y<DSL Processing Started>RS< ==="}
        SET_SOURCE_TYPE = {"ru": "Установлен тип источника: >G<{type}>RS<", "en": "Source type detected: >G<{type}>RS<"}
        JSON_GENERATED = {"ru": ">G<>BOLD<[OK]>RS< >G<Компиляция в промежуточный код завершена>RS< - >G<>BOLD<JSON сгенерирован.>RS<Целей: {count} ", "en": ">G<>BOLD<[OK]>RS< >G<Compilation to intermediate code completed>RS< - >G<>BOLD<JSON generated.>RS<Targets: {count} "}
        ROUTE_ADDED = {"ru": "Добавлен маршрут: {src} -> {dst}(>O<{type}>RS<)", "en": "Route added: {src} -> {dst}(>O<{type}>RS<)"}
        TARGET_ADDED = {"ru": "Добавлена цель: {value} (тип: >O<>BOLD<{type}>RS<)", "en": "Target added: {value} (type: >O<>BOLD<{type}>RS<)"}
        GLOBAL_VAR_ADDED = {"ru": "Добавлена глобальная переменная: >B<${name}>RS< = {value} (тип: >O<{type}>RS<)", "en": "Global variable added: >B<${name}>RS< = {value} (type: >O<{type}>RS<)"}
        PROCESSING_FINISH = {"ru": "=== >G<Обработка DSL завершена>RS< ===", "en": "=== >G<DSL Processing Completed>RS< ==="}

    class Warning:
        EMPTY_PIPELINE_SEGMENT = {"ru": ">O<Предупреждение:>RS< Обнаружен пустой сегмент пайплайна", "en": ">O<Warning:>RS< Empty pipeline segment detected"}

    class Error:
        PIPELINE_CLOSING_BAR = {"ru": ">R<Закрывающая прямая черта пайплайна не найдена>RS<", "en": ">R<Pipeline closing bar is missing>RS<"}
        BRACKET_MISSING = {"ru": ">R<Квадратная скобка определения сущности не найдена>RS<", "en": ">R<Entity definition bracket is missing>RS<"}
        FLOW_DIRECTION = {"ru": ">R<Символ направляющего потока не найден. Используйте ->, =>, - или >", "en": ">R<Flow direction symbol is missing. Use ->, =>, - or >"}
        FINAL_TYPE = {"ru": ">R<Финальный тип не задан или задан некорректно>RS<", "en": ">R<Final type is not specified or incorrectly specified>RS<"}
        VOID_TYPE = {"ru": ">R<Для пустого поля [] нельзя указывать тип>RS<", "en": ">R<Empty field [] cannot have a type specification>RS<"}
        SYNTAX_SOURCE = {"ru": ">R<Неверный синтаксис определения источника>RS<", "en": ">R<Invalid source definition syntax>RS<"}
        SYNTAX_TARGET = {"ru": ">R<Неверный синтаксис определения цели>RS<", "en": ">R<Invalid target definition syntax>RS< "}
        SEMANTIC_TARGET = {"ru": ">R<Ошибка в определении цели>RS<", "en": ">R<Error in target definition>RS<"}
        SEMANTIC_ROUTES = {"ru": ">R<Ошибка в определении маршрутов>RS<", "en": ">R<Error in route definitions>RS<"}
        PIPELINE_EMPTY = {"ru": ">R<Пустой пайплайн обнаружен>RS<", "en": ">R<Empty pipeline detected>RS<"}
        UNKNOWN = {"ru": ">R<Неизвестная синтаксическая ошибка>RS<", "en": ">R<Unknown syntax error>RS<"}
        GENERIC = {"ru": ">R<Ошибка при обработке DSL:>RS< {message}", "en": ">R<Error processing DSL:>RS< {message}"}
        LINE_PREFIX = {"ru": ">R<Ошибка в строке {line_num}:>RS<", "en": ">R<Error in line {line_num}:>RS<"}
        FILE_NOT_FOUND = {"ru": ">R<Файл не найден:>RS< {file}. {message}", "en": ">R<File not found:>RS< {file}. {message}"}
        DUPLICATE_VAR = {"ru": "Дублирующееся имя переменной: ${var_name}", "en": "Duplicate variable name: ${var_name}"}
        VARS_FOLDER_NOT_FOUND = {"ru": "Папка с внешними переменными не найдена: {folder}", "en": "External variables folder not found: {folder}"}
        EXTERNAL_VAR_FILE_NOT_FOUND = {"ru": "Файл с внешними переменными не найден: {file}", "en": "External variable file not found: {file}"}
        EXTERNAL_VAR_PATH_NOT_FOUND = {"ru": "Путь не найден во внешней переменной: {path}", "en": "Path not found in external variable: {path}"}

    class Hint:
        LABEL = {"ru": ">G<Возможное решение:>RS<", "en": ">G<Possible solution:>RS<"}
        ADD_CLOSING_BAR = {"ru": "Добавьте закрывающую вертикальную черту '|'", "en": "Add closing vertical bar '|'"}
        CHECK_BRACKETS = {"ru": "Проверьте правильность открывающих и закрывающих скобок [field]", "en": "Check if brackets are properly opened and closed [field]"}
        USE_FLOW_SYMBOL = {"ru": "Используйте один из символов направления: >GREEN<->, =>, -, >>RESET<", "en": "Use one of the flow direction symbols: >GREEN<->, =>, -, >>RESET<"}
        SPECIFY_TYPE = {"ru": "Укажите тип в круглых скобках: [field](type)", "en": "Specify type in parentheses: [field](type)"}
        VOID_NO_TYPE = {"ru": "Для пустого поля [] не нужно указывать тип", "en": "Empty field [] must not have a type specifier"}
        SOURCE_SYNTAX = {"ru": "Используйте source=type", "en": "Use source=type"}
        TARGET_SYNTAX = {"ru": "Используйте target=type(\"value\")", "en": "Use target=type(\"value\")"}
        PIPELINE_MUST_HAVE_CONTENT = {"ru": "Пайплайн должен содержать хотя бы один символ между вертикальными чертами", "en": "Pipeline must contain at least one character between vertical bars"}
        SEQUENTIAL_PIPELINES = {"ru": "Обнаружены последовательные пайплайны без данных между ними", "en": "Sequential pipelines detected without data between them"}
        TARGET_DEFINITION_MISSING = {"ru": "Не найдено определение цели для маршрута {target}", "en": "Target definition not found for route {target}"}
        ROUTES_MISSING = {"ru": "Отсутствуют определения маршрутов (target:)", "en": "Route definitions are missing (target:)"}
        FILE_NOT_FOUND = {"ru": "Проверьте корректность пути к файлу: {file}", "en": "Check the file path: {file}"}
        DUPLICATE_VAR = {"ru": "Переменная уже определена на строке {first_pos}", "en": "Variable is already defined at line {first_pos}"}
        VARS_FOLDER_NOT_FOUND = {"ru": "Убедитесь, что папка существует и доступна для чтения", "en": "Make sure the folder exists and is readable"}
        EXTERNAL_VAR_FILE_NOT_FOUND = {"ru": "Проверьте, существует ли файл в папке внешних переменных", "en": "Check if the file exists in the external variables folder"}
        EXTERNAL_VAR_PATH_NOT_FOUND = {"ru": "Проверьте путь во внешней переменной", "en": "Check the path in the external variable"}
    class Debug:
        PARSING_ROUTE_BLOCK = {"ru": "Разбор блока маршрутов для {target}", "en": "Parsing route block for {target}"}
        ROUTE_PROCESSING = {"ru": "Обработка маршрутов для цели: {target}", "en": "Processing routes for target: {target}"}
        PARSING_FINISH = {"ru": ">G<Синтаксический анализ завершен. Создано узлов:>RS< >BOLD<{count}>RS<", "en": ">G<Parsing completed. Nodes created:>RS< >BOLD<{count}>RS<"}
        PARSING_START = {"ru": ">Y<Начало синтаксического анализа...>RS<", "en": ">Y<Starting parsing...>RS<"}
        TOKENIZATION_FINISH = {"ru": ">G<Токенизация завершена. Создано токенов:>RS< >BOLD<{count}>RS<", "en": ">G<Tokenization completed. Tokens created:>RS< >BOLD<{count}>RS<"}
        TOKENIZATION_START = {"ru": ">Y<Начало токенизации...>RS<", "en": ">Y<Starting tokenization...>RS<"}
        TOKEN_CREATED = {"ru": "Токен {type}: {value}", "en": "Token {type}: {value}"}
        COMMENT_IGNORED = {"ru": "Комментарий проигнорирован: {comment}", "en": "Comment ignored: {comment}"}
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