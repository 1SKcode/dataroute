import json
import os
import sys
import traceback
from typing import Dict, Any, Optional

from .lexer import Lexer
from .parser import Parser
from .json_generator import JSONGenerator
from .errors import DSLSyntaxError, ExternalVarsFolderNotFoundError, ExternalVarFileNotFoundError, ExternalVarPathNotFoundError, FuncConflictError, print_func_conflict_error, ExternalFuncFolderNotFoundError
from .localization import Messages as M, Localization
from .mess_core import colorize, pr
from .config import Config


class Engine:
    """
    Внутренняя реализация парсера и интерпретатора DSL DataRoute.
    
    Этот класс содержит всю основную логику обработки DSL и не должен
    использоваться напрямую. Вместо этого используйте публичный
    класс DataRoute из модуля dataroute.
    """
    
    def __init__(
        self, 
        source: str, 
        debug: bool = False, 
        lang: str = "en", 
        color: bool = False,
        vars_folder: str = None,
        func_folder: str = None
    ):
        """
        Инициализирует компоненты обработки DSL
        
        Args:
            source: Путь к файлу или строка с DSL кодом
            debug: Флаг отладочного режима
            lang: Код языка ('ru' или 'en')
            color: Флаг использования цветного вывода
            vars_folder: Путь к папке с внешними переменными
            func_folder: Путь к папке с функциями
            
        Note:
            Класс не предназначен для прямого использования.
            Используйте DataRoute из основного модуля библиотеки.
        """
        self._source = source
        self._debug = debug
        self._lang = lang  # Только для локализации!
        self._color = color
        self._vars_folder = vars_folder
        self._func_folder = func_folder
        self._is_file = self._detect_source_type(source)

        # --- Новый блок: определяем язык функций из DSL ---
        dsl_text = self._load_source() if not self._is_file else self._try_peek_file(self._source)
        self._dsl_lang = self._extract_dsl_lang(dsl_text)
        # --- конец нового блока ---

        self._lexer = Lexer()
        self._available_funcs = self._collect_functions(self._dsl_lang)
        self._parser = Parser()
        self._parser.set_available_funcs(self._available_funcs, func_folder=self._func_folder)
        self._json_generator = JSONGenerator(vars_folder)
        self._result = None
        self._text = None
        self._localizer = Localization(self._lang)
        self._update_localization()
    
    def _detect_source_type(self, source: str) -> bool:
        """
        Определяет тип источника данных
        
        Правила определения:
        1. Если строка заканчивается на .txt или .dtrt - считаем файлом
        2. Если строка содержит '->' - считаем DSL кодом
        3. Проверяем существование файла
        
        Args:
            source: Путь к файлу или строка с DSL кодом
            
        Returns:
            bool: True если источник - файл, False если строка с кодом
        """
        # Проверяем расширение файла
        if source.lower().endswith(('.txt', '.dtrt')):
            return True
            
        # Проверяем наличие синтаксических элементов DSL
        if '->' in source or '=>' in source:
            return False
            
        # Проверяем существование файла
        return os.path.exists(source) and os.path.isfile(source)
    
    def _update_localization(self):
        """Обновляет локализацию во всех компонентах"""
        # Необходимо обновить и глобальный Config для компонентов, которые от него зависят
        Config.set(lang=self._lang)

        # Обновляем локализаторы в компонентах напрямую
        self._lexer.loc = Localization(self._lang)
        self._parser.loc = Localization(self._lang)
        self._json_generator.loc = Localization(self._lang)
    
    def _load_source(self) -> str:
        """
        Загружает исходный код из файла или использует его как строку
        
        Returns:
            str: Содержимое файла или исходная строка
            
        Raises:
            SystemExit: Если файл не найден или не может быть прочитан
        """
        if self._is_file:
            if not os.path.exists(self._source) or not os.path.isfile(self._source):
                # Локализованный вывод ошибки и подсказки
                err_msg = self._localizer.get(M.Error.FILE_NOT_FOUND, file=self._source, message="")
                hint = self._localizer.get(M.Hint.LABEL) + " " + self._localizer.get(M.Hint.FILE_NOT_FOUND, file=self._source)
                pr(err_msg)
                pr(hint)
                sys.exit(1)
            try:
                with open(self._source, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                self._print(M.Error.FILE_NOT_FOUND, file=self._source, message=str(e))
                sys.exit(1)
        else:
            return self._source
    
    def _print(self, msg, *args, **kwargs):
        """
        Выводит локализованное сообщение с учетом настроек
        
        Args:
            msg: Сообщение (словарь из Messages или строка)
            *args: Дополнительные аргументы для print
            **kwargs: Параметры для форматирования сообщения
        """
        # Если это не dict (например, строка или DSLSyntaxError)
        if not isinstance(msg, dict):
            print(colorize(str(msg), self._color), *args, file=sys.stdout)
            return
            
        # Определяем тип сообщения по имени класса Messages
        msg_type = None
        for cls in (M.Debug, M.Info, M.Warning, M.Error, M.Hint):
            if msg in cls.__dict__.values():
                msg_type = cls.__name__
                break
                
        # Debug-сообщения выводим только если debug включён
        if msg_type == "Debug" and not self._debug:
            return
            
        # Получаем строку на нужном языке
        text = self._localizer.get(msg, **kwargs)
        text = colorize(text, self._color)
        print(text, *args, file=sys.stdout)
    
    def set_lang(self, lang: str) -> None:
        """
        Устанавливает язык для сообщений
        
        Args:
            lang: Код языка ('ru' или 'en')
        """
        self._lang = lang
        self._localizer = Localization(lang)
        self._update_localization()
    
    def set_debug(self, debug: bool) -> None:
        """
        Включает или выключает режим отладки
        
        Args:
            debug: True для включения, False для выключения
        """
        self._debug = debug
        Config.set(debug=debug)
    
    def set_color(self, color: bool) -> None:
        """
        Включает или выключает цветной вывод
        
        Args:
            color: True для включения, False для выключения
        """
        self._color = color
        Config.set(color=color)
    
    def go(self) -> Dict[str, Any]:
        """
        Запускает обработку DSL и возвращает структуру JSON
        
        Этот метод выполняет полный цикл обработки DSL:
        1. Загрузка текста из источника
        2. Лексический анализ
        3. Синтаксический анализ
        4. Генерация JSON
        
        Raises:
            Exception: При ошибках обработки. Текст ошибки локализован.
            
        Returns:
            Dict: Результирующая структура данных
        """
        # Полный сброс предыдущего результата и состояния компонентов
        self._result = None
        self._text = None
        # Пересоздаем компоненты для полного сброса их внутреннего состояния
        self._lexer = Lexer()
        self._parser = Parser()
        self._parser.set_available_funcs(self._available_funcs, func_folder=self._func_folder)
        # Не создаем новый JSONGenerator, а очищаем состояние существующего
        if hasattr(self._json_generator, 'reset'):
            self._json_generator.reset()
        # Обновляем локализацию
        self._update_localization()
        
        try:
            # Загружаем текст
            self._text = self._load_source()
            
            # Информационное сообщение о начале обработки
            pr(M.Info.PROCESSING_START)
            
            # Критическая проверка папки с переменными
            if self._vars_folder and not os.path.isdir(self._vars_folder):
                error = ExternalVarsFolderNotFoundError(self._vars_folder)
                pr(str(error), file=sys.stderr)
                sys.exit(1)
            
            # Проверяем существование пользовательской папки функций
            if self._func_folder and not os.path.isdir(self._func_folder):
                error = ExternalFuncFolderNotFoundError(self._func_folder)
                pr(str(error), file=sys.stderr)
                sys.exit(1)
            
            # Лексический анализ
            tokens = self._lexer.tokenize(self._text)
            
            # Синтаксический анализ
            ast = self._parser.parse(tokens)
            
            # Генерация JSON
            self._result = ast.accept(self._json_generator)
            
            # Информационное сообщение о завершении обработки
            pr(M.Info.PROCESSING_FINISH)
            
            return self._result
            
        except DSLSyntaxError as e:
            # Ошибки синтаксиса с указанием позиции
            pr(str(e), file=sys.stderr)
            sys.exit(1)
            
        except ExternalVarsFolderNotFoundError as e:
            # Ошибка папки с внешними переменными
            pr(str(e), file=sys.stderr)
            sys.exit(1)
            
        except ExternalVarFileNotFoundError as e:
            # Ошибка файла с внешними переменными
            pr(str(e), file=sys.stderr)
            sys.exit(1)
            
        except ExternalVarPathNotFoundError as e:
            # Ошибка пути во внешней переменной
            pr(str(e), file=sys.stderr)
            sys.exit(1)
            
        except FileNotFoundError as e:
            # Файл не найден или путь неверный
            pr(f"Ошибка: {str(e)}", file=sys.stderr)
            if self._debug:
                pr(traceback.format_exc(), file=sys.stderr)
            sys.exit(1)
            
        except KeyError as e:
            # Ошибки с переменными (ключ не найден)
            pr(f"Ошибка: {str(e)}", file=sys.stderr)
            if self._debug:
                pr(traceback.format_exc(), file=sys.stderr)
            sys.exit(1)
            
        except Exception as e:
            # Все прочие ошибки
            pr(f"Ошибка при обработке DSL: {str(e)}", "red", file=sys.stderr)
            if self._debug:
                pr(traceback.format_exc(), file=sys.stderr)
            sys.exit(1)
    
    def to_json(self, output_file: Optional[str] = None, indent: int = 2) -> Optional[str]:
        """
        Преобразует результат в JSON и опционально сохраняет в файл
        
        Args:
            output_file: Путь к файлу для сохранения JSON. Если None,
                         возвращает JSON-строку
            indent: Отступ для форматирования JSON
            
        Returns:
            Optional[str]: JSON-строка, если output_file=None, иначе None
            
        Note:
            Если результат еще не получен, автоматически вызывает go()
        """
        if self._result is None:
            self.go()
            
        json_str = json.dumps(self._result, indent=indent, ensure_ascii=False)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_str)
            return None
        else:
            return json_str
    
    def print_json(self, indent: int = 2) -> None:
        """
        Выводит результат в формате JSON в stdout
        
        Args:
            indent: Отступ для форматирования JSON
            
        Note:
            Если результат еще не получен, автоматически вызывает go()
        """
        json_str = self.to_json(indent=indent)
        self._print(json_str)
    
    @property
    def result(self) -> Optional[Dict[str, Any]]:
        """
        Получить результат последнего разбора
        
        Returns:
            Optional[Dict[str, Any]]: JSON-структура или None, если разбор еще не выполнен
        """
        return self._result
    
    @property
    def source(self) -> str:
        """
        Получить источник данных
        
        Returns:
            str: Путь к файлу или строка с DSL
        """
        return self._source
    
    @property
    def is_file(self) -> bool:
        """
        Проверить, является ли источник файлом
        
        Returns:
            bool: True, если источник - файл, иначе False
        """
        return self._is_file 
    
    def _extract_dsl_lang(self, text: str) -> str:
        """Извлекает язык функций из DSL (lang=py/cpp/...), по умолчанию py."""
        import re
        match = re.search(r"lang\s*=\s*([a-zA-Z0-9_]+)", text)
        return match.group(1).lower() if match else "py"

    def _try_peek_file(self, path: str) -> str:
        """Пробует прочитать первые 2-3 строки файла для поиска директивы lang=..."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return "\n".join([next(f) for _ in range(3)])
        except Exception:
            return ""

    def _collect_functions(self, dsl_lang="py"):
        """Собирает имена функций из std_func/<lang> и пользовательской папки, проверяет конфликты."""
        import os
        from .localization import Messages as M
        from .localization import Localization

        lang_map = {
            "py": "python",
            "python": "python",
            "cpp": "cpp",
            # можно добавить другие языки
        }
        lang_key = dsl_lang.lower()
        lang_folder = lang_map.get(lang_key)
        if not lang_folder:
            # Локализованная ошибка
            loc = Localization(getattr(self, '_lang', 'ru'))
            pr(loc.get(M.Error.UNSUPPORTED_TARGET_LANG, lang=lang_key))
            pr(loc.get(M.Hint.SUPPORTED_TARGET_LANGUAGES))
            sys.exit(1)

        std_func_dir = os.path.join(os.path.dirname(__file__), f"../std_func/{lang_folder}")
        std_func_dir = os.path.abspath(std_func_dir)
        std_funcs = set()
        user_funcs = set()
        if os.path.isdir(std_func_dir):
            for f in os.listdir(std_func_dir):
                if f.endswith(".py") and not f.startswith("_"):
                    std_funcs.add(os.path.splitext(f)[0])
        if self._func_folder and os.path.isdir(self._func_folder):
            for f in os.listdir(self._func_folder):
                if f.endswith(".py") and not f.startswith("_"):
                    user_funcs.add(os.path.splitext(f)[0])
        conflicts = std_funcs & user_funcs
        if conflicts:
            print_func_conflict_error(std_func_dir, self._func_folder, conflicts)
            sys.exit(1)
        return std_funcs | user_funcs 