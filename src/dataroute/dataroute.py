"""
dataroute - Гибкая ETL-система на Python с DSL для построения маршрутов и трансформаций данных
"""

from typing import Dict, Any, Optional

from ._impl import Engine


class DataRoute:
    """
    Основной класс для работы с DSL DataRoute.
    
    Примеры использования:
    
    # Из файла
    dtrt = DataRoute("file.dtrt")
    result = dtrt.go()
    dtrt.print_json()  # Вывод в консоль
    dtrt.to_json("result.json")  # Сохранение в файл
    
    # Из строки
    code = 'source = data | [field] -> [other] |'
    dtrt = DataRoute(code, is_file=False)
    result = dtrt.go()
    """
    
    def __init__(
        self, 
        source: str, 
        vars_folder: str = None,
        debug: bool = False, 
        lang: str = "en", 
        color: bool = False
    ):
        """
        Создает новый экземпляр для обработки DSL
        
        Args:
            source: Путь к файлу или строка с кодом DSL.
                   Тип определяется автоматически:
                   - Файлы с расширением .txt, .dtrt
                   - Строки, содержащие синтаксис DSL (например '->')
            vars_folder: Путь к папке с внешними JSON переменными
            debug: Включить режим отладки с дополнительными сообщениями
            lang: Язык сообщений ('ru' или 'en')
            color: Использовать цветной вывод
        """
        self._engine = Engine(source, debug, lang, color, vars_folder)
    
    def go(self) -> Dict[str, Any]:
        """
        Запускает обработку DSL и возвращает результат
        
        Returns:
            Dict[str, Any]: Структура данных, представляющая обработанный DSL
        """
        return self._engine.go()
    
    def set_lang(self, lang: str) -> "DataRoute":
        """
        Меняет язык вывода сообщений
        
        Args:
            lang: Код языка ('ru' или 'en')
            
        Returns:
            DataRoute: Текущий экземпляр для цепочки вызовов
        """
        self._engine.set_lang(lang)
        return self
    
    def set_debug(self, debug: bool) -> "DataRoute":
        """
        Включает или выключает отладочный режим
        
        Args:
            debug: True для включения, False для выключения
            
        Returns:
            DataRoute: Текущий экземпляр для цепочки вызовов
        """
        self._engine.set_debug(debug)
        return self
    
    def set_color(self, color: bool) -> "DataRoute":
        """
        Включает или выключает цветной вывод
        
        Args:
            color: True для включения, False для выключения
            
        Returns:
            DataRoute: Текущий экземпляр для цепочки вызовов
        """
        self._engine.set_color(color)
        return self
    
    def to_json(self, output_file: Optional[str] = None, indent: int = 2) -> Optional[str]:
        """
        Преобразует результат в JSON и опционально сохраняет в файл
        
        Args:
            output_file: Путь к файлу для сохранения JSON. Если None,
                         возвращает JSON-строку
            indent: Отступ для форматирования JSON
            
        Returns:
            Optional[str]: JSON-строка, если output_file=None
        """
        return self._engine.to_json(output_file, indent)
    
    def print_json(self, indent: int = 2) -> None:
        """
        Выводит результат в формате JSON в stdout
        
        Args:
            indent: Отступ для форматирования JSON
        """
        self._engine.print_json(indent)
    
    @property
    def result(self) -> Optional[Dict[str, Any]]:
        """
        Результат последнего разбора
        
        Returns:
            Optional[Dict[str, Any]]: Структура данных или None, если разбор еще не выполнен
        """
        return self._engine.result
    
    @property
    def source(self) -> str:
        """
        Исходный код или путь к файлу
        
        Returns:
            str: Путь к файлу или строка с DSL
        """
        return self._engine.source
    
    @property
    def is_file(self) -> bool:
        """
        Признак использования файла как источника
        
        Returns:
            bool: True, если источник - файл, иначе False
        """
        return self._engine.is_file


if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Парсер DSL для Data Route")
    parser.add_argument('input', help='Входной DSL-файл')
    parser.add_argument('-o', '--output', help='Выходной JSON-файл')
    parser.add_argument('-d', '--debug', action='store_true', help='Режим отладки')
    parser.add_argument('-l', '--lang', choices=['ru', 'en'], default='en', help='Язык сообщений')
    parser.add_argument('-i', '--indent', type=int, default=2, help='Отступ в JSON')
    parser.add_argument('--no-color', action='store_true', help='Отключить цветной вывод')
    parser.add_argument('-v', '--vars', help='Путь к папке с внешними переменными (JSON)')
    
    args = parser.parse_args()
    
    dtrt = DataRoute(args.input, vars_folder=args.vars, debug=args.debug, lang=args.lang, color=not args.no_color)
    
    if args.output:
        dtrt.to_json(args.output, args.indent)
    else:
        dtrt.print_json(args.indent)