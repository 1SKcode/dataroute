import json
import sys
import traceback
from typing import Dict, Any, Optional

from .lexer import Lexer
from .parser import Parser
from .json_generator import JSONGenerator
from .errors import DSLSyntaxError
from .localization import Messages as M
from .config import Config
from .mess_core import pr




class DataRouteParser:
    """Класс для парсинга и интерпретации DSL"""
    
    def __init__(self, debug=False, lang="ru", color=True):
        Config.set(lang=lang, debug=debug, color=color)
        self.lexer = Lexer()
        self.parser = Parser()
        self.json_generator = JSONGenerator()
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Обрабатывает DSL и возвращает структуру JSON"""
        pr(M.Info.PROCESSING_START)
        
        try:
            # Этап 1: Лексический анализ
            tokens = self.lexer.tokenize(text)
            
            # Этап 2: Синтаксический анализ
            ast = self.parser.parse(tokens)
            
            # Этап 3: Обход AST и генерация JSON
            result = ast.accept(self.json_generator)
            
            pr(M.Info.PROCESSING_FINISH)
            
            return result
            
        except DSLSyntaxError as e:
            # Выводим ошибку в красивом формате
            pr(str(e))
            sys.exit(1)
        except Exception as e:
            # Для других ошибок выводим стандартное сообщение
            pr(M.Error.GENERIC, message=str(e))
            if Config.is_debug():
                traceback.print_exc()
            sys.exit(1)


def parse_dsl(text: str, debug: bool = False, lang: str = "ru", color: bool = True) -> Dict[str, Any]:
    """Парсинг DSL-текста в JSON-структуру"""
    parser = DataRouteParser(debug, lang, color)
    return parser.parse(text)


def parse_dsl_file(filename: str, debug: bool = False, lang: str = "ru", color: bool = True) -> Dict[str, Any]:
    """Функция для парсинга DSL-файла в JSON-структуру"""
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()
    return parse_dsl(text, debug, lang, color)


def parse_dsl_to_json(text: str, output_file: Optional[str] = None, 
                      indent: int = 2, debug: bool = False, lang: str = "ru", color: bool = True) -> None:
    """Парсит DSL-текст и сохраняет результат в JSON-файл или выводит в stdout"""
    result = parse_dsl(text, debug, lang, color)
    json_str = json.dumps(result, indent=indent, ensure_ascii=False)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json_str)
    else:
        pr(json_str)


def parse_dsl_file_to_json(input_file: str, output_file: Optional[str] = None, 
                           indent: int = 2, debug: bool = False, lang: str = "ru", color: bool = True) -> None:
    """Парсит DSL-файл и сохраняет результат в JSON-файл или выводит в stdout"""
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
    parse_dsl_to_json(text, output_file, indent, debug, lang, color)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Парсер DSL для Data Route")
    parser.add_argument('input', help='Входной DSL-файл')
    parser.add_argument('-o', '--output', help='Выходной JSON-файл')
    parser.add_argument('-d', '--debug', action='store_true', help='Режим отладки')
    parser.add_argument('-l', '--lang', choices=['ru', 'en'], default='ru', help='Язык сообщений')
    parser.add_argument('-i', '--indent', type=int, default=2, help='Отступ в JSON')
    parser.add_argument('--no-color', action='store_true', help='Отключить цветной вывод')
    
    args = parser.parse_args()
    
    parse_dsl_file_to_json(args.input, args.output, args.indent, args.debug, args.lang, not args.no_color) 