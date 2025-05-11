import json
import os
import sys
import traceback
from typing import Dict, Any, Optional

from .lexer import Lexer
from .parser import Parser
from .json_generator import JSONGenerator
from .errors import DSLSyntaxError
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
        vars_folder: str = None
    ):
        """
        Инициализирует компоненты обработки DSL
        
        Args:
            source: Путь к файлу или строка с DSL кодом
            debug: Флаг отладочного режима
            lang: Код языка ('ru' или 'en')
            color: Флаг использования цветного вывода
            vars_folder: Путь к папке с внешними переменными
            
        Note:
            Класс не предназначен для прямого использования.
            Используйте DataRoute из основного модуля библиотеки.
        """
        self._source = source
        self._debug = debug
        self._lang = lang
        self._color = color
        self._vars_folder = vars_folder
        
        # Автоматически определяем, является ли source файлом
        self._is_file = self._detect_source_type(source)
            
        # Инициализация компонентов обработки DSL
        self._lexer = Lexer()
        self._parser = Parser()
        self._json_generator = JSONGenerator(vars_folder)
        
        # Результат обработки
        self._result = None
        self._text = None
        
        # Локализатор сообщений
        self._localizer = Localization(self._lang)
        
        # Обновляем локализацию в компонентах
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
        2. Лексический анализ (токенизация)
        3. Синтаксический анализ (парсинг)
        4. Построение JSON структуры
        
        Returns:
            Dict[str, Any]: JSON-структура, представляющая обработанный DSL
            
        Raises:
            SystemExit: При синтаксических ошибках или других проблемах
        """
        # Полный сброс предыдущего результата и состояния компонентов
        self._result = None
        self._text = None
        # Пересоздаем компоненты для полного сброса их внутреннего состояния
        self._lexer = Lexer()
        self._parser = Parser()
        self._json_generator = JSONGenerator(self._vars_folder)
        # Обновляем локализацию
        self._update_localization()
        
        self._print(M.Info.PROCESSING_START)
        
        try:
            # Загружаем исходный код
            self._text = self._load_source()
            
            # Этап 1: Лексический анализ
            tokens = self._lexer.tokenize(self._text)
            
            # Этап 2: Синтаксический анализ
            ast = self._parser.parse(tokens)
            
            # Этап 3: Обход AST и генерация JSON
            self._result = ast.accept(self._json_generator)
            
            self._print(M.Info.PROCESSING_FINISH)
            
            return self._result
            
        except DSLSyntaxError as e:
            # Выводим ошибку в красивом формате
            self._print(str(e))
            sys.exit(1)
        except Exception as e:
            # Для других ошибок выводим стандартное сообщение
            self._print(M.Error.GENERIC, message=str(e))
            if self._debug:
                traceback.print_exc()
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