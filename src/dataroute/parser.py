import sys
import re
from typing import List, Dict, Optional, Any

from .ast_nodes import (
    ASTNode, ProgramNode, SourceNode, TargetNode, RouteBlockNode,
    FieldSrcNode, PipelineNode, FieldDstNode, RouteLineNode, PipelineItemNode, GlobalVarNode
)
from .constants import ErrorType, PipelineItemType, TokenType
from .errors import DSLSyntaxError, FinalTypeError, VoidTypeError
from .localization import Localization, Messages as M
from .mess_core import pr
from .config import Config


class Parser:
    """Синтаксический анализатор для создания AST из токенов"""
    
    def __init__(self):
        """Инициализация парсера"""
        self.tokens = []
        self.position = 0
        self.targets = {}
        self.loc = Localization(Config.get_lang())
    
    def parse(self, tokens=None):
        """Запускает процесс парсинга"""
        if tokens is not None:
            self.tokens = tokens
        
        self.position = 0
        self.ast = ProgramNode()
        
        # Хранилище для глобальных переменных, чтобы проверять дубликаты
        self._global_vars = {}
        
        pr(M.Debug.PARSING_START)
        
        # Проходим по токенам
        while self.position < len(self.tokens):
            token = self.tokens[self.position]
            
            if token.type == TokenType.SOURCE:
                self.ast.children.append(SourceNode(token.value))
                self.position += 1
            elif token.type == TokenType.TARGET:
                target_node = TargetNode(
                    token.value['name'],
                    token.value['type'],
                    token.value['value']
                )
                self.ast.children.append(target_node)
                # Сохраняем информацию о нашем таргете для упрощения доступа
                if not hasattr(self.ast, '_targets'):
                    self.ast._targets = {}
                self.ast._targets[token.value['name']] = target_node
                self.position += 1
            elif token.type == TokenType.GLOBAL_VAR:
                var_info = token.value
                var_name = var_info['name']
                
                # Проверка на дублирование имени переменной
                if var_name in self._global_vars:
                    # Выводим сообщение об ошибке и завершаем программу
                    pr(self.loc.get(M.Error.DUPLICATE_VAR, var_name=var_name), "red")
                    # Добавляем подсказку
                    pr(self.loc.get(M.Hint.LABEL) + " " + 
                       self.loc.get(M.Hint.DUPLICATE_VAR, first_pos=str(self._global_vars[var_name].position)))
                    sys.exit(1)
                
                # Сохраняем переменную и создаем узел AST
                self._global_vars[var_name] = token
                
                var_node = GlobalVarNode(
                    name=var_name,
                    value=var_info['value'],
                    value_type=var_info['type']
                )
                self.ast.children.append(var_node)
                
                # Сохраняем глобальные переменные в AST для доступа из других компонентов
                if not hasattr(self.ast, '_global_vars'):
                    self.ast._global_vars = {}
                self.ast._global_vars[var_name] = var_node
                
                self.position += 1
            elif token.type == TokenType.ROUTE_HEADER:
                target_name = token.value
                self.position += 1
                
                # Проверяем, что существует целевой объект для этого маршрута
                if not hasattr(self.ast, '_targets') or target_name not in self.ast._targets:
                    self._error(f"Целевой объект '{target_name}' не определен")
                
                # Получаем все маршруты для этой цели
                routes = []
                while self.position < len(self.tokens) and self.tokens[self.position].type == TokenType.ROUTE_LINE:
                    route_line_token = self.tokens[self.position]
                    routes.append(self._parse_route_line(route_line_token))
                    self.position += 1
                
                # Создаем блок маршрутов и добавляем в AST
                route_block = RouteBlockNode(target_name, routes)
                self.ast.children.append(route_block)
            else:
                # Пропускаем неизвестные токены
                self.position += 1
        
        pr(M.Debug.PARSING_FINISH)
        return self.ast
    
    def _parse_source(self) -> SourceNode:
        """Создает узел источника данных"""
        token = self.tokens[self.position]
        self.position += 1
        return SourceNode(token.value)
    
    def _parse_target(self) -> TargetNode:
        """Создает узел цели"""
        token = self.tokens[self.position]
        self.position += 1
        return TargetNode(
            token.value['name'],
            token.value['type'],
            token.value['value']
        )
    
    def _parse_route_line(self, token):
        """Разбор строки маршрута."""
        src_field = token.value['src_field']
        pipeline_text = token.value.get('pipeline')
        target_field = token.value['target_field']
        target_field_type = token.value.get('target_field_type')
        
        # Создаем узел исходного поля
        field_src = FieldSrcNode(src_field)
        
        # Обрабатываем конвейер
        pipeline = self._parse_pipeline(pipeline_text) if pipeline_text else PipelineNode()
        
        # Создаем узел целевого поля
        field_dst = None
        
        # Проверяем случай с пустым целевым полем, чтобы различать [] и [field] без типа
        if target_field == "":
            # Пустое поле, как в [age] -> |*check_age| -> [] или [score] -> |*validate_score| -> []()
            # Проверяем, указан ли тип для пустого поля (что является ошибкой)
            if target_field_type is not None:
                # Ошибка: указан тип для пустого поля
                from .errors import VoidTypeError
                original_line = token.value.get('line', f"[{src_field}] -> ... -> []({target_field_type})")
                error = VoidTypeError(original_line, token.position, original_line.rfind(']') + 1)
                pr(str(error))
                sys.exit(1)
                
            field_dst = FieldDstNode(name=None, type_name=None)
        elif target_field:
            # Есть поле, например [id] -> [external_id](str)
            # Проверяем, указан ли тип явно
            if target_field_type is None:
                # Ошибка: не указан тип для непустого поля
                error_msg = f"Не указан тип для поля [{target_field}]"
                from .errors import FinalTypeError
                original_line = token.value.get('line', f"[{src_field}] -> ... -> [{target_field}]")
                error = FinalTypeError(original_line, token.position, original_line.rfind(']') + 1)
                pr(str(error))
                sys.exit(1)
                
            field_dst = FieldDstNode(
                name=target_field,
                type_name=target_field_type
            )
            
        # Создаем узел строки маршрута
        route_line = RouteLineNode(
            src_field=field_src,
            pipeline=pipeline,
            target_field=field_dst
        )
        
        return route_line
    
    def _parse_pipeline(self, pipeline_str: str) -> PipelineNode:
        """Создает конвейер обработки"""
        if pipeline_str is None:
            return PipelineNode()
        
        # Удаляем начальный и конечный |
        if pipeline_str.startswith('|') and pipeline_str.endswith('|'):
            pipeline_content = pipeline_str[1:-1]
        else:
            pipeline_content = pipeline_str
        
        # Разбиваем на элементы
        pipeline = PipelineNode()
        
        if pipeline_content:
            # Проверка на пустое содержимое пайплайна
            segments = pipeline_content.split('|')
            
            for segment in segments:
                segment = segment.strip()
                if not segment:
                    pr(M.Warning.EMPTY_PIPELINE_SEGMENT)
                
                if not segment:
                    continue
                
                if segment.startswith('*'):
                    # Функция Python
                    # Извлекаем имя функции и параметры
                    func_name = segment[1:]  # Убираем *
                    param = "$this"  # Параметр по умолчанию
                    is_pre_var = False
                    is_external_var = False
                    
                    # Проверяем наличие скобок с параметрами
                    if '(' in func_name and func_name.endswith(')'):
                        param_start = func_name.find('(')
                        param_end = func_name.rfind(')')
                        
                        # Извлекаем параметр
                        param_str = func_name[param_start+1:param_end].strip()
                        
                        # Проверяем на тип параметра
                        if param_str.startswith('$^'):
                            # Пре-переменная
                            param = param_str
                            is_pre_var = True
                        elif param_str.startswith('$$'):
                            # Внешняя переменная
                            param = param_str
                            is_external_var = True
                        elif param_str.startswith('$'):
                            # Обычная переменная
                            param = param_str
                        else:
                            # Строковый или другой литерал
                            param = param_str
                        
                        # Оставляем только имя функции
                        func_name = func_name[:param_start]
                    
                    pipeline.items.append(PipelineItemNode(
                        PipelineItemType.PY_FUNC,
                        func_name,
                        params={"param": param, "is_pre_var": is_pre_var, "is_external_var": is_external_var}
                    ))
                    pr(M.Debug.PIPELINE_ITEM_ADDED, type=PipelineItemType.PY_FUNC.value, value=segment)
                else:
                    # Прямое отображение
                    pipeline.items.append(PipelineItemNode(
                        PipelineItemType.DIRECT,
                        segment
                    ))
                    pr(M.Debug.PIPELINE_ITEM_ADDED, type=PipelineItemType.DIRECT.value, value=segment)
        
        return pipeline

    def _error(self, message):
        """Генерирует сообщение об ошибке и прерывает выполнение"""
        pr(f"Ошибка парсинга: {message}", "red")
        sys.exit(1)


# Импортируем TokenType в конце файла, чтобы избежать циклических зависимостей
from .constants import NodeType 