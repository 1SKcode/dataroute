import re
import sys
from dataclasses import dataclass
from typing import List, Any, Optional

from .constants import PATTERNS, TokenType, ALLOWED_TYPES, SUPPORTED_TARGET_LANGUAGES, ErrorType
from .errors import SyntaxErrorHandler, PipelineEmptyError, InvalidTypeError, DSLSyntaxError
from .localization import Localization, Messages as M
from .config import Config
from .mess_core import pr


@dataclass
class Token:
    """Токен, полученный при лексическом анализе"""
    type: TokenType
    value: Any
    position: int = 0
    
    def __repr__(self):
        return f"Token({self.type.name}, {self.value})"


class Lexer:
    """Лексический анализатор для преобразования текста в токены"""
    
    def __init__(self):
        self.tokens = []
        self.error_handler = SyntaxErrorHandler()
        self.loc = Localization(Config.get_lang())

    def _strip_quotes(self, s):
        """Удаляет кавычки из строкового значения"""
        if len(s) >= 2 and s[0] == s[-1] and s[0] in {"'", '"'}:
            return s[1:-1]
        return s
    
    def tokenize(self, text: str) -> List[Token]:
        """Разбивает текст на токены"""
        self.tokens = []
        lines = text.strip().split('\n')
        
        pr(M.Debug.TOKENIZATION_START)
        
        # Проверка наличия директивы языка компиляции ДО любого анализа DSL
        lang_found = any(re.match(PATTERNS[TokenType.LANG], line.strip()) for line in lines if line.strip())
        if not lang_found:
            error = DSLSyntaxError(
                ErrorType.MISSING_TARGET_LANG,
                '',
                1,
                0,
                None
            )
            pr(str(error))
            sys.exit(1)
        
        source_found = False
        
        for line_num, line in enumerate(lines, 1):
            original_line = line
            line = line.strip()
            if not line:
                continue
            
            # Проверка на пустой пайплайн до токенизации
            if '||' in original_line:
                error = PipelineEmptyError(original_line, line_num, original_line.find('||') + 1)
                pr(str(error))
                sys.exit(1)
                
            # Анализируем строку на соответствие шаблонам
            matched = False
            
            # Определение языка компиляции (lang=py,lang=cpp) — ДОЛЖНО БЫТЬ ПЕРВЫМ!
            if not matched:
                match = re.match(PATTERNS[TokenType.LANG], line)
                if match:
                    lang_value = match.group(1)
                    # Проверяем, поддерживается ли язык компиляции
                    if lang_value not in SUPPORTED_TARGET_LANGUAGES:
                        error = DSLSyntaxError(
                            ErrorType.UNSUPPORTED_TARGET_LANG,
                            original_line,
                            line_num,
                            line.find('lang'),
                            None,
                            lang=lang_value
                        )
                        pr(str(error))
                        sys.exit(1)
                    # Добавляем токен языка
                    self.tokens.append(Token(TokenType.LANG, lang_value, line_num))
                    pr(M.Debug.TOKEN_CREATED, type=TokenType.LANG.name, value=lang_value)
                    matched = True
            
            # Определение источника (source=тип/путь)
            if not matched:
                match = re.match(PATTERNS[TokenType.SOURCE], line)
                if match:
                    source_found = True
                    source_type = match.group(1)
                    source_name = match.group(2)
                    if not source_type or not source_name:
                        error = DSLSyntaxError(
                            ErrorType.SYNTAX_SOURCE,
                            original_line,
                            line_num,
                            line.find('source'),
                            self.loc.get(M.Hint.SOURCE_SYNTAX)
                        )
                        pr(str(error))
                        sys.exit(1)
                    self.tokens.append(Token(TokenType.SOURCE, {"type": source_type, "name": source_name}, line_num))
                    pr(M.Debug.TOKEN_CREATED, type=TokenType.SOURCE.name, value={"type": source_type, "name": source_name})
                    matched = True
            
            # Если строка начинается с source=, но не проходит паттерн — это тоже ошибка синтаксиса источника
            if not matched and line.startswith('source='):
                error = DSLSyntaxError(
                    ErrorType.SYNTAX_SOURCE,
                    original_line,
                    line_num,
                    line.find('source'),
                    self.loc.get(M.Hint.SOURCE_SYNTAX)
                )
                pr(str(error))
                sys.exit(1)
            
            # Определение цели (targetN=тип/имя_или_путь)
            if not matched:
                match = re.match(PATTERNS[TokenType.TARGET], line)
                if match:
                    target_name = match.group(1)
                    target_type = match.group(2)
                    target_value = match.group(3)
                    if not target_type or not target_value:
                        error = DSLSyntaxError(
                            ErrorType.SYNTAX_TARGET,
                            original_line,
                            line_num,
                            line.find(target_name),
                            self.loc.get(M.Hint.TARGET_SYNTAX)
                        )
                        pr(str(error))
                        sys.exit(1)
                    self.tokens.append(Token(TokenType.TARGET, {"name": target_name, "type": target_type, "value": target_value}, line_num))
                    pr(M.Debug.TOKEN_CREATED, type=TokenType.TARGET.name, value={"name": target_name, "type": target_type, "value": target_value})
                    matched = True
            # Если строка похожа на targetN=... (имя=...), но не проходит паттерн — ошибка SYNTAX_TARGET
            if not matched and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*=.*$', line):
                error = DSLSyntaxError(
                    ErrorType.SYNTAX_TARGET,
                    original_line,
                    line_num,
                    line.find('='),
                    self.loc.get(M.Hint.TARGET_SYNTAX)
                )
                pr(str(error))
                sys.exit(1)
            
            # Глобальная переменная ($myVar = "value")
            if not matched:
                match = re.match(PATTERNS[TokenType.GLOBAL_VAR], line)
                if match:
                    var_name = match.group(1)
                    var_value = match.group(2).strip()
                    
                    # Определяем тип значения
                    var_type = "str"  # По умолчанию
                    
                    # Проверяем кавычки для строк
                    if (var_value.startswith('"') and var_value.endswith('"')) or \
                       (var_value.startswith("'") and var_value.endswith("'")):
                        var_value = self._strip_quotes(var_value)
                    # Проверяем целое число
                    elif var_value.isdigit():
                        var_type = "int"
                        var_value = int(var_value)
                    # Проверяем число с плавающей точкой
                    elif re.match(r'^-?\d+\.\d+$', var_value):
                        var_type = "float"
                        var_value = float(var_value)
                    # Проверяем булево значение
                    elif var_value.lower() in ("true", "false"):
                        var_type = "bool"
                        var_value = var_value.lower() == "true"
                    
                    var_info = {
                        'name': var_name,
                        'value': var_value,
                        'type': var_type
                    }
                    
                    self.tokens.append(Token(TokenType.GLOBAL_VAR, var_info, line_num))
                    pr(M.Debug.TOKEN_CREATED, type=TokenType.GLOBAL_VAR.name, value=var_info)
                    matched = True
            
            # Комментарий (# ...)
            if not matched:
                match = re.match(PATTERNS[TokenType.COMMENT], line)
                if match:
                    # Обрабатываем комментарий, но не создаем токен
                    # Комментарии игнорируются в процессе токенизации
                    pr(M.Debug.COMMENT_IGNORED, comment=match.group(1).strip())
                    matched = True
            
            # Заголовок маршрута (target1:)
            if not matched:
                match = re.match(PATTERNS[TokenType.ROUTE_HEADER], line)
                if match:
                    self.tokens.append(Token(TokenType.ROUTE_HEADER, match.group(1), line_num))
                    pr(M.Debug.TOKEN_CREATED, type=TokenType.ROUTE_HEADER.name, value=match.group(1))
                    matched = True
            
            # Строка маршрута с отступом
            match = re.match(PATTERNS[TokenType.ROUTE_LINE], original_line)
            if match:
                # Получаем тип данных из маршрута
                target_field_type = match.group(4)
                
                # Проверка типа данных, если он указан
                if target_field_type and target_field_type not in ALLOWED_TYPES:
                    # Определяем позицию ошибки в строке - находим позицию типа в скобках
                    type_position = original_line.find(f"({target_field_type})")
                    if type_position == -1:
                        type_position = original_line.rfind(")") - len(target_field_type) - 1
                    
                    # Создаем ошибку с указанием некорректного типа
                    error = InvalidTypeError(
                        original_line, 
                        line_num, 
                        target_field_type, 
                        type_position
                    )
                    pr(str(error))
                    sys.exit(1)
                
                # Получаем целевое поле и очищаем от пробелов
                target_field = match.group(3).strip()
                
                route_info = {
                    'src_field': match.group(1),
                    'pipeline': match.group(2),
                    'target_field': target_field,
                    'target_field_type': target_field_type,
                    'line': original_line
                }
                self.tokens.append(Token(TokenType.ROUTE_LINE, route_info, line_num))
                pr(M.Debug.TOKEN_CREATED, type=TokenType.ROUTE_LINE.name, value=route_info)
                matched = True
            
            # Строка маршрута с использованием глобальной переменной
            if not matched:
                match = re.match(PATTERNS[TokenType.GLOBAL_VAR_USAGE], original_line)
                if match:
                    var_name = match.group(1)
                    self.tokens.append(Token(TokenType.GLOBAL_VAR_USAGE, {"var_name": var_name, "line": original_line}, line_num))
                    pr(M.Debug.TOKEN_CREATED, type=TokenType.GLOBAL_VAR_USAGE.name, value={"var_name": var_name, "line": original_line})
                    matched = True
            
            if not matched:
                error = self.error_handler.analyze(line, line_num)
                # Выводим ошибку и прерываем выполнение
                pr(str(error))
                sys.exit(1)
        
        if not source_found:
            error = DSLSyntaxError(
                ErrorType.SYNTAX_SOURCE,
                '',
                1,
                0,
                self.loc.get(M.Hint.SOURCE_SYNTAX)
            )
            pr(str(error))
            sys.exit(1)
        
        pr(M.Debug.TOKENIZATION_FINISH, count=len(self.tokens))
        
        return self.tokens 