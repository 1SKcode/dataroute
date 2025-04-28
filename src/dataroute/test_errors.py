"""
Тестовый файл для проверки обработки ошибок в новой реализации DataRoute.
Тестирует синтаксические ошибки в DSL и их обработку.
"""

import sys
import os

# Добавляем родительский каталог в путь поиска модулей
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dataroute.errors import DSLSyntaxError, SyntaxErrorHandler


def main():
    # Создаем экземпляры для тестирования
    error_handler = SyntaxErrorHandler()
    
    # Примеры с ошибками
    errors = [
        # Ошибка: Закрывающая черта пайплайна отсутствует
        "[id] -> |*pipe -> [field](str)",
        
        # Ошибка: Квадратная скобка не закрыта
        "[id -> |*pipe| -> [field](str)",
        
        # Ошибка: Отсутствие символа направления
        "[id] |*pipe| -> [field](str)",
        
        # Ошибка: Финальный тип не указан
        "[id] -> |*pipe| -> [field]",
        
        # Ошибка: Пустой пайплайн
        "[id] -> || -> [field](str)",
    ]

    # Проверяем обработку ошибок
    for i, line in enumerate(errors, 1):
        print(f"\n=== Ошибка #{i} ===")
        print(f"DSL: {line}")
        error = error_handler.analyze(line, i)
        print(error)
        print("=" * 50)


if __name__ == "__main__":
    main() 