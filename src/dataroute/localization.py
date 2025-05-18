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
        DIRECT_MAPPING_WITHOUT_STAR = {"ru": ">O<Предупреждение:>RS< Обнаружено прямое отображение [{src}] -> |{value}| без *. Возможно, вы забыли поставить * перед именем функции?", "en": ">O<Warning:>RS< Direct mapping [{src}] -> |{value}| without * detected. Did you forget to add * before function name?"}

    class Error:
        PIPELINE_CLOSING_BAR = {
            "ru": ">R<Закрывающая прямая черта пайплайна не найдена>RS<",
            "en": ">R<Pipeline closing bar is missing>RS<"
        }
        BRACKET_MISSING = {
            "ru": ">R<Квадратная скобка определения сущности не найдена>RS<",
            "en": ">R<Entity definition bracket is missing>RS<"
        }
        FLOW_DIRECTION = {"ru": ">R<Символ направляющего потока не найден. Используйте ->, =>, - или >", "en": ">R<Flow direction symbol is missing. Use ->, =>, - or >"}
        FINAL_TYPE = {"ru": ">R<Финальный тип не задан или задан некорректно>RS<", "en": ">R<Final type is not specified or incorrectly specified>RS<"}
        VOID_TYPE = {"ru": ">R<Для пустого поля [] нельзя указывать тип>RS<", "en": ">R<Empty field [] cannot have a type specification>RS<"}
        SYNTAX_SOURCE = {"ru": ">R<Неверный синтаксис определения источника>RS<", "en": ">R<Invalid source definition syntax>RS<"}
        SYNTAX_TARGET = {"ru": ">R<Неверный синтаксис определения цели>RS<", "en": ">R<Invalid target definition syntax>RS< "}
        SEMANTIC_TARGET = {"ru": ">R<Ошибка в определении цели>RS<", "en": ">R<Error in target definition>RS<"}
        SEMANTIC_ROUTES = {"ru": ">R<Ошибка в определении маршрутов>RS<", "en": ">R<Error in route definitions>RS<"}
        PIPELINE_EMPTY = {"ru": ">R<Пустой пайплайн обнаружен>RS<", "en": ">R<Empty pipeline detected>RS<"}
        UNKNOWN = {"ru": ">R<Неожиданный токен в коде. Проверьте синтаксис>RS<", "en": ">R<Unexpected token in code. Check syntax>RS<"}
        GENERIC = {"ru": ">R<Ошибка при обработке DSL:>RS< {message}", "en": ">R<Error processing DSL:>RS< {message}"}
        LINE_PREFIX = {"ru": ">R<Ошибка в строке {line_num}:>RS<", "en": ">R<Error in line {line_num}:>RS<"}
        FILE_NOT_FOUND = {"ru": ">R<Файл не найден:>RS< {file}. {message}", "en": ">R<File not found:>RS< {file}. {message}"}
        DUPLICATE_VAR = {"ru": ">R<Дублирующееся имя переменной:>RS< ${var_name}", "en": ">R<Duplicate variable name:>RS< ${var_name}"}
        VARS_FOLDER_NOT_FOUND = {"ru": ">R<Папка с внешними переменными не найдена:>RS< {folder}", "en": ">R<External variables folder not found:>RS< {folder}"}
        EXTERNAL_VAR_FILE_NOT_FOUND = {"ru": ">R<Файл с внешними переменными не найден:>RS< {file}", "en": ">R<External variable file not found:>RS< {file}"}
        EXTERNAL_VAR_PATH_NOT_FOUND = {"ru": ">R<Путь не найден во внешней переменной:>RS< {path}", "en": ">R<Path not found in external variable:>RS< {path}"}
        UNKNOWN_PIPELINE_SEGMENT = {"ru": ">R<Неизвестное поведение внутри пайплайна>RS<", "en": ">R<Unknown behavior inside pipeline>RS<"}
        UNDEFINED_VAR = {"ru": ">R<Переменная '${var_name}' не определена в текущем контексте>RS<", "en": ">R<Variable '${var_name}' is not defined in current context>RS<"}
        INVALID_VAR_USAGE = {"ru": ">R<Некорректное использование переменной '${var_name}'>RS<", "en": ">R<Invalid usage of variable '${var_name}'>RS<"}
        SRC_FIELD_AS_VAR = {"ru": ">R<Поле из левой части '${var_name}' нельзя использовать как переменную>RS<", "en": ">R<Source field '${var_name}' cannot be used as a variable>RS<"}
        INVALID_TYPE = {"ru": ">R<Неверный тип данных: {data_type}>RS<", "en": ">R<Invalid data type: {data_type}>RS<"}
        CONDITION_MISSING_IF = {"ru": ">R<В выражении может быть только if, но не может быть else без if>RS<", "en": ">R<Expression can only have if, but cannot have else without if>RS<"}
        CONDITION_MISSING_PARENTHESIS = {"ru": ">R<Условная конструкция должна содержать знак скобок>RS<", "en": ">R<Conditional construction must contain parentheses>RS<"}
        CONDITION_EMPTY_EXPRESSION = {"ru": ">R<Не найдено логическое выражение внутри условной конструкции>RS<", "en": ">R<No logical expression found inside conditional construction>RS<"}
        CONDITION_MISSING_COLON = {"ru": ">R<Не найден знак завершения условного выражения (:)>RS<", "en": ">R<Closing symbol (:) of the conditional expression not found>RS<"}
        CONDITION_INVALID = {"ru": ">R<Недопустимое или неправильное условное выражение{key_part}>RS<", "en": ">R<Invalid or incorrect conditional expression{key_part}>RS<"}
        DUPLICATE_FINAL_NAME = {"ru": ">R<Дублирующееся имя финальной цели:>RS< {final_name}", "en": ">R<Duplicate final target name:>RS< {final_name}"}
        DUPLICATE_TARGET_NAME_TYPE = {"ru": ">R<Дублирующееся имя цели:>RS< {target_type}", "en": ">R<Duplicate target name:>RS< {target_type}"}
        FUNC_NOT_FOUND = {"ru": ">R<Функция не найдена:>RS< {func_name}", "en": ">R<Function not found:>RS< {func_name}"}
        FUNC_CONFLICT = {"ru": ">R<Конфликт имён функций:>RS< {func_name}. Уже определена в системной и пользовательской папках.", "en": ">R<Function name conflict:>RS< {func_name}. Already defined in both system and user folders."}
        FUNC_FOLDER_NOT_FOUND = {"ru": ">R<Папка с пользовательскими функциями не найдена:>RS< {folder}", "en": ">R<User function folder not found:>RS< {folder}"}
        EXTERNAL_VAR_WRITE = {
            "ru": ">R<Нельзя записывать во внешнюю переменную:>RS< {var_name}",
            "en": ">R<You cannot write to an external variable:>RS< {var_name}"
        }
        GLOBAL_VAR_WRITE = {
            "ru": ">R<Нельзя записывать в глобальную переменную:>RS< {var_name}",
            "en": ">R<You cannot write to a global variable:>RS< {var_name}"
        }
        UNDEFINED_GLOBAL_VAR = {
            "ru": ">R<Глобальная переменная '{var_name}' не определена>RS<",
            "en": ">R<Global variable '{var_name}' is not defined>RS<"
        }

    class Hint:
        LABEL = {"ru": ">G<Возможное решение:>RS<", "en": ">G<Possible solution:>RS<"}
        ADD_CLOSING_BAR = {"ru": "Добавьте закрывающую вертикальную черту '|'", "en": "Add closing vertical bar '|'"}
        CHECK_BRACKETS = {"ru": "Проверьте правильность открывающих и закрывающих скобок [field]", "en": "Check if brackets are properly opened and closed [field]"}
        USE_FLOW_SYMBOL = {"ru": "Используйте один из символов направления: >GREEN<->, =>, -, >>RESET<", "en": "Use one of the flow direction symbols: >GREEN<->, =>, -, >>RESET<"}
        SPECIFY_TYPE = {"ru": "Укажите тип в круглых скобках: [field](type)", "en": "Specify type in parentheses: [field](type)"}
        VOID_NO_TYPE = {"ru": "Для пустого поля [] не нужно указывать тип", "en": "Empty field [] must not have a type specifier"}
        SOURCE_SYNTAX = {"ru": "Используйте source=type", "en": "Use source=type"}
        TARGET_SYNTAX = {"ru": "Используйте target=type/имя", "en": "Use target=type/name"}
        PIPELINE_MUST_HAVE_CONTENT = {"ru": "Пайплайн должен содержать хотя бы один символ между вертикальными чертами", "en": "Pipeline must contain at least one character between vertical bars"}
        SEQUENTIAL_PIPELINES = {"ru": "Обнаружены последовательные пайплайны без данных между ними", "en": "Sequential pipelines detected without data between them"}
        TARGET_DEFINITION_MISSING = {"ru": "Определена карта маршрута {target}, но нет определения цели для этого маршрута\nИспользуйте {target}=type/имя", "en": "Route {target} is defined, but no target definition is found for it\nUse {target}=type/name"}
        ROUTES_MISSING = {"ru": "Отсутствуют определения маршрутов (target:)", "en": "Route definitions are missing (target:)"}
        FILE_NOT_FOUND = {"ru": "Проверьте корректность пути к файлу: {file}", "en": "Check the file path: {file}"}
        DUPLICATE_VAR = {"ru": "Переменная уже определена на строке {first_pos}", "en": "Variable is already defined at line {first_pos}"}
        VARS_FOLDER_NOT_FOUND = {"ru": "Убедитесь, что папка существует и доступна для чтения", "en": "Make sure the folder exists and is readable"}
        EXTERNAL_VAR_FILE_NOT_FOUND = {"ru": "Проверьте, существует ли файл в папке внешних переменных", "en": "Check if the file exists in the external variables folder"}
        EXTERNAL_VAR_PATH_NOT_FOUND = {"ru": "Проверьте путь во внешней переменной", "en": "Check the path in the external variable"}
        UNKNOWN_PIPELINE_SEGMENT = {"ru": "Используйте *имя_функции для вызова функции или усло", "en": "Use *function_name to call a function or if for conditions"}
        UNDEFINED_VAR = {"ru": "Переменная должна быть определена перед использованием. Пример: [field] -> |*func| -> [$var_name](type)", "en": "Variable must be defined before usage. Example: [field] -> |*func| -> [$var_name](type)"}
        INVALID_VAR_USAGE = {"ru": "Обратите внимание на место определения и использования переменной", "en": "Pay attention to the definition and usage of the variable"}
        SRC_FIELD_AS_VAR = {"ru": "Создайте отдельный маршрут для сохранения поля в переменную: [field] -> [$var_field](type), затем используйте $var_field", "en": "Create a separate route to save the field as a variable: [field] -> [$var_field](type), then use $var_field"}
        INVALID_TYPE = {"ru": "Используйте один из разрешённых типов данных: {allowed_types}", "en": "Use one of the allowed data types: {allowed_types}"}
        CONDITION_MISSING_IF = {"ru": "Возможное решение: используйте конструкции IF(exp): ... ELSE: ... / IF(exp): ... ELIF(exp): ... ELSE: ...", "en": "Possible solution: use IF(exp): ... ELSE: ... / IF(exp): ... ELIF(exp): ... ELSE: ... constructions"}
        CONDITION_MISSING_PARENTHESIS = {"ru": "Возможное решение: используйте конструкции IF(exp): ... ELSE: ... / IF(exp): ... ELIF(exp): ... ELSE: ...", "en": "Possible solution: use IF(exp): ... ELSE: ... / IF(exp): ... ELIF(exp): ... ELSE: ... constructions"}
        CONDITION_EMPTY_EXPRESSION = {"ru": "Добавьте логическое выражение внутрь условной конструкции IF(услвие). используйте конструкции IF(exp): ... ELSE: ... / IF(exp): ... ELIF(exp): ... ELSE: ...", "en": "Add logical expression inside conditional construction IF(condition). Use IF(exp): ... ELSE: ... / IF(exp): ... ELIF(exp): ... ELSE: ... constructions"}
        CONDITION_MISSING_COLON = {"ru": "Возможное решение: используйте конструкции IF(exp): ... ELSE: ... / IF(exp): ... ELIF(exp): ... ELSE: ...", "en": "Possible solution: use IF(exp): ... ELSE: ... / IF(exp): ... ELIF(exp): ... ELSE: ... constructions"}
        CONDITION_INVALID = {"ru": "Проверьте правильность условного выражения и используйте конструкции IF(exp): ... ELSE: ... / IF(exp): ... ELIF(exp): ... ELSE: ...", "en": "Check the correctness of the conditional expression and use IF(exp): ... ELSE: ... / IF(exp): ... ELIF(exp): ... ELSE: ... constructions"}
        DUPLICATE_FINAL_NAME = {"ru": "Цель уже используется для записи. Проверьте уникальность имени.", "en": "Target is already used for writing. Check name uniqueness."}
        DUPLICATE_TARGET_NAME_TYPE = {"ru": "Используйте уникальные имена целей для разных типов", "en": "Use unique target names for different types"}
        FUNC_NOT_FOUND = {"ru": "Проверьте имя функции и наличие файла с именем {func_name} в указанной вами папке: >Y<{func_folder}>RS<", "en": "Check the function name and the presence of a file named {func_name} in the specified folder: >Y<{func_folder}>RS<"}
        FUNC_CONFLICT = {"ru": "Переименуйте пользовательскую функцию или удалите конфликтующий файл: {func_name}", "en": "Rename the user function or remove the conflicting file: {func_name}"}
        FUNC_FOLDER_NOT_FOUND = {"ru": "Проверьте путь к папке с функциями или создайте её.", "en": "Check the function folder path or create it."}
        EXTERNAL_VAR_WRITE = {
            "ru": "Используйте только локальные переменные или обычные цели для записи",
            "en": "Use only local variables or regular targets for writing"
        }
        GLOBAL_VAR_WRITE = {
            "ru": "Используйте уникальное имя для переменной назначения или обычную цель",
            "en": "Use a unique name for the target variable or a regular target"
        }
        UNDEFINED_GLOBAL_VAR = {
            "ru": "Определите глобальную переменную выше по коду: $my_var = ...",
            "en": "Define the global variable above: $my_var = ..."
        }
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