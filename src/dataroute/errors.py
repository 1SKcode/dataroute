import re
import sys
from typing import Optional

from .constants import ErrorType, ERROR_MESSAGE_MAP, ERROR_HINT_MAP
from .localization import Localization, Messages
from .config import Config


class DSLSyntaxError(Exception):
    """Базовый класс для всех синтаксических ошибок DSL"""
    
    def __init__(self, 
                 error_type: ErrorType,
                 line: str,
                 line_num: int,
                 position: Optional[int] = None,
                 suggestion: Optional[str] = None):
        self.error_type = error_type
        self.line = line
        self.line_num = line_num
        self.position = position or self._guess_error_position(line)
        self.suggestion = suggestion
        self.lang = Config.get_lang()
        self.loc = Localization(self.lang)
        
        # Формируем сообщение об ошибке
        message = self._format_error_message()
        super().__init__(message)
    
    def _guess_error_position(self, line: str) -> int:
        """Пытается угадать позицию ошибки в строке"""
        return 0
    
    def _format_error_message(self) -> str:
        """Форматирует сообщение об ошибке"""
        # Получаем соответствующее сообщение об ошибке
        message = self.loc.get(ERROR_MESSAGE_MAP.get(self.error_type, Messages.Error.UNKNOWN))
        
        # Форматируем строку с указателем на позицию ошибки
        pointer = " " * self.position + "^"
        
        result = [
            self.loc.get(Messages.Error.LINE_PREFIX, line_num=self.line_num),
            f"{self.line}",
            f"{pointer}",
            f"{message}",
        ]
        
        # Если есть подсказка, добавляем её
        if self.suggestion:
            hint_label = self.loc.get(Messages.Hint.LABEL)
            result.append(f"{hint_label} {self.suggestion}")
        # Иначе пробуем использовать стандартную подсказку для данного типа ошибки
        elif ERROR_HINT_MAP.get(self.error_type):
            hint = self.loc.get(ERROR_HINT_MAP.get(self.error_type), 
                                target=self.line if self.error_type == ErrorType.SEMANTIC_TARGET else None)
            if hint:
                hint_label = self.loc.get(Messages.Hint.LABEL)
                result.append(f"{hint_label} {hint}")
        
        return "\n".join(result)


class SyntaxErrorHandler:
    """Обработчик синтаксических ошибок DSL"""
    
    def __init__(self):
        # Паттерны для частичных совпадений
        self.patterns = {
            # Для проверки открытого пайплайна без закрытия
            "pipeline_open": r'\|[^|]*(?!\|)[^|]*$',
            
            # Для проверки пустого пайплайна
            "pipeline_empty": r'\|\|',
            
            # Для проверки последовательных пайплайнов
            "pipeline_sequential": r'\|[^|]*\|\s*(?:->|=>|-|>)\s*\|',
            
            # Для проверки неправильных скобок
            "brackets_missing_open": r'(?<!\[)\w+\]',
            "brackets_missing_close": r'\[[^\]]*$',
            
            # Для проверки корректности символов направления
            "direction_missing": r'\]\s*(?!(?:->|=>|-|>))[^\s]',
            
            # Для проверки корректности финального типа
            "final_type_missing": r'\]\s*$|\]\s*(?!\()',
            
            # Для проверки синтаксиса источника
            "source_syntax": r'sourse\s+\w+',
            
            # Для проверки синтаксиса цели
            "target_syntax": r'=\s*\w+\s*\[\s*["\'](.*?)["\']'
        }
    
    def analyze(self, line: str, line_num: int) -> DSLSyntaxError:
        """Анализирует строку и возвращает соответствующую ошибку"""
        # Проверка на пустой пайплайн
        if re.search(self.patterns["pipeline_empty"], line):
            pos = re.search(self.patterns["pipeline_empty"], line).start() + 1
            return PipelineEmptyError(line, line_num, pos)
        
        # Проверка на последовательные пайплайны
        if re.search(self.patterns["pipeline_sequential"], line):
            pos = re.search(self.patterns["pipeline_sequential"], line).end() - 1
            return DSLSyntaxError(ErrorType.PIPELINE_EMPTY, line, line_num, pos, Messages.Hint.SEQUENTIAL_PIPELINES)
        
        # Проверка синтаксиса определения источника и цели
        if re.match(self.patterns["source_syntax"], line):
            pos = line.find('sourse') + len('sourse')
            return DSLSyntaxError(ErrorType.SYNTAX_SOURCE, line, line_num, pos, None)
        
        if re.search(self.patterns["target_syntax"], line):
            pos = line.find('[')
            return DSLSyntaxError(ErrorType.SYNTAX_TARGET, line, line_num, pos, None)
        
        # Проверка на финальный тип
        if ']' in line and '->' in line:  # Убедимся, что это строка маршрута
            last_bracket_pos = line.rfind(']')
            # После последней ] должна быть (
            if last_bracket_pos != -1 and ('(' not in line[last_bracket_pos:]):
                return FinalTypeError(line, line_num, last_bracket_pos + 1)
        
        # Проверка на символ направления
        direction_missing = False
        direction_pos = 0
        
        if ']' in line and '[' in line:
            # Найдем все вхождения закрывающей скобки
            for match in re.finditer(r'\]', line):
                end_pos = match.end()
                # Если после скобки нет стрелки, и это не последняя скобка в строке
                if end_pos < len(line) - 1 and not re.match(r'\s*(?:->|=>|-|>|\()', line[end_pos:]):
                    # Если после этого есть еще квадратная скобка
                    if '[' in line[end_pos:]:
                        direction_missing = True
                        direction_pos = end_pos
                        break
        
        if direction_missing:
            return FlowDirectionError(line, line_num, direction_pos)
        
        # Проверка на незакрытый пайплайн
        pipe_count = line.count('|')
        if pipe_count > 0 and pipe_count % 2 != 0:
            # Найти позицию последней вертикальной черты
            last_pipe_pos = line.rfind('|')
            return PipelineClosingBarError(line, line_num, last_pipe_pos)
        
        # Проверка на неправильные скобки
        if line.count('[') != line.count(']'):
            if line.count('[') > line.count(']'):
                # Если открывающих скобок больше
                for match in re.finditer(r'\[', line):
                    start_pos = match.start()
                    # Проверяем, есть ли для этой скобки закрывающая
                    remaining = line[start_pos+1:]
                    if ']' not in remaining:
                        return BracketMissingError(line, line_num, start_pos)
            else:
                # Если закрывающих скобок больше
                for match in re.finditer(r'\]', line):
                    end_pos = match.start()
                    preceding = line[:end_pos]
                    if preceding.count('[') < preceding.count(']') + 1:
                        return BracketMissingError(line, line_num, end_pos)
        
        # Проверка отсутствия открывающей скобки
        opening_bracket_missing = re.search(r'(?<!\[)(\w+)\]', line)
        if opening_bracket_missing:
            pos = opening_bracket_missing.start(1)
            return BracketMissingError(line, line_num, pos)
        
        # Если не удалось определить конкретную ошибку
        return DSLSyntaxError(ErrorType.UNKNOWN, line, line_num, 0, None)


# Конкретные классы ошибок с специфичной логикой определения позиции

class PipelineClosingBarError(DSLSyntaxError):
    """Ошибка отсутствия закрывающей черты пайплайна"""
    
    def __init__(self, line: str, line_num: int, position: Optional[int] = None):
        super().__init__(ErrorType.PIPELINE_CLOSING_BAR, line, line_num, position, None)
    
    def _guess_error_position(self, line: str) -> int:
        # Находим последний символ '|' и предполагаем, что ошибка после него
        last_bar_pos = line.rfind('|')
        if last_bar_pos != -1:
            return last_bar_pos + 1
        # Если не нашли '|', ищем '[' и ']'
        bracket_pos = line.find('[')
        if bracket_pos != -1:
            return bracket_pos
        return 0


class BracketMissingError(DSLSyntaxError):
    """Ошибка отсутствия или неправильного использования квадратных скобок"""
    
    def __init__(self, line: str, line_num: int, position: Optional[int] = None):
        super().__init__(ErrorType.BRACKET_MISSING, line, line_num, position, None)
    
    def _guess_error_position(self, line: str) -> int:
        # Проверяем несоответствие открывающих и закрывающих скобок
        open_brackets = line.count('[')
        close_brackets = line.count(']')
        
        if open_brackets > close_brackets:
            # Ищем последнюю открывающую скобку без пары
            pos = len(line) - 1
            while pos >= 0:
                if line[pos] == '[':
                    close_pos = line.find(']', pos)
                    if close_pos == -1:
                        return pos
                pos -= 1
        elif close_brackets > open_brackets:
            # Ищем первую закрывающую скобку без пары
            for pos, char in enumerate(line):
                if char == ']':
                    if line[:pos].count('[') <= line[:pos].count(']'):
                        return pos
        
        # Если не можем найти проблему со скобками, ищем первое использование скобок
        bracket_pos = line.find('[')
        if bracket_pos != -1:
            return bracket_pos
        
        return 0


class FlowDirectionError(DSLSyntaxError):
    """Ошибка символа направления потока"""
    
    def __init__(self, line: str, line_num: int, position: Optional[int] = None):
        super().__init__(ErrorType.FLOW_DIRECTION, line, line_num, position, None)
    
    def _guess_error_position(self, line: str) -> int:
        # Ищем позицию после ']', где должна быть стрелка
        bracket_close_pos = line.find(']')
        if bracket_close_pos != -1:
            return bracket_close_pos + 1
        return 0


class FinalTypeError(DSLSyntaxError):
    """Ошибка финального типа"""
    
    def __init__(self, line: str, line_num: int, position: Optional[int] = None):
        super().__init__(ErrorType.FINAL_TYPE, line, line_num, position, None)
    
    def _guess_error_position(self, line: str) -> int:
        # Ищем последнюю скобку ']' и затем проверяем наличие '('
        last_bracket_pos = line.rfind(']')
        if last_bracket_pos != -1:
            return last_bracket_pos + 1
        return len(line) - 1


class PipelineEmptyError(DSLSyntaxError):
    """Ошибка пустого пайплайна"""
    
    def __init__(self, line: str, line_num: int, position: Optional[int] = None):
        super().__init__(ErrorType.PIPELINE_EMPTY, line, line_num, position, None)
    
    def _guess_error_position(self, line: str) -> int:
        # Находим позицию пустого пайплайна "||"
        empty_pipeline_match = re.search(r'\|\|', line)
        if empty_pipeline_match:
            return empty_pipeline_match.start() + 1
        return 0 