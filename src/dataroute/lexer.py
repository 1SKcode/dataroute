import re
import sys
from dataclasses import dataclass
from typing import List, Any, Optional

from .constants import PATTERNS, TokenType
from .errors import SyntaxErrorHandler, PipelineEmptyError
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
            
            # Определение источника (sourse=dict)
            if not matched:
                match = re.match(PATTERNS[TokenType.SOURCE], line)
                if match:
                    self.tokens.append(Token(TokenType.SOURCE, match.group(1), line_num))
                    pr(M.Debug.TOKEN_CREATED, type=TokenType.SOURCE.name, value=match.group(1))
                    matched = True
            
            # Определение цели (target1=dict("target1"))
            if not matched:
                match = re.match(PATTERNS[TokenType.TARGET], line)
                if match:
                    target_info = {
                        'name': match.group(1),
                        'type': match.group(2),
                        'value': self._strip_quotes(match.group(3)) 
                    }
                    self.tokens.append(Token(TokenType.TARGET, target_info, line_num))
                    pr(M.Debug.TOKEN_CREATED, type=TokenType.TARGET.name, value=target_info)
                    matched = True
            
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
                route_info = {
                    'src_field': match.group(1),
                    'pipeline': match.group(2),
                    'target_field': match.group(3),
                    'target_field_type': match.group(4),
                    'line': original_line
                }
                self.tokens.append(Token(TokenType.ROUTE_LINE, route_info, line_num))
                pr(M.Debug.TOKEN_CREATED, type=TokenType.ROUTE_LINE.name, value=route_info)
                matched = True
            
            if not matched:
                error = self.error_handler.analyze(line, line_num)
                # Выводим ошибку и прерываем выполнение
                pr(str(error))
                sys.exit(1)
        
        pr(M.Debug.TOKENIZATION_FINISH, count=len(self.tokens))
        
        return self.tokens 