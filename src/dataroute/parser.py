import sys
from typing import List, Dict

from .ast_nodes import (
    ASTNode, ProgramNode, SourceNode, TargetNode, RouteBlockNode,
    FieldSrcNode, PipelineNode, FieldDstNode, RouteLineNode, PipelineItemNode
)
from .constants import ErrorType, PipelineItemType
from .errors import DSLSyntaxError, SyntaxErrorHandler
from .lexer import Token
from .localization import Localization, Messages as M
from .config import Config
from .mess_core import pr


class Parser:
    """Синтаксический анализатор для построения AST из токенов"""
    
    def __init__(self):
        self.tokens = []
        self.position = 0
        self.targets = {}
        self.error_handler = SyntaxErrorHandler()
        self.loc = Localization(Config.get_lang())
    
    def parse(self, tokens: List[Token]) -> ProgramNode:
        """Создает AST из токенов"""
        self.tokens = tokens
        self.position = 0
        program = ProgramNode()
        pr(M.Debug.PARSING_START)
        
        # Проверка на наличие хотя бы одного определения источника
        source_found = False
        for token in tokens:
            if token.type == TokenType.SOURCE:
                source_found = True
                break
        
        if not source_found:
            error_line = "sourse= (missing)"
            raise DSLSyntaxError(ErrorType.SYNTAX_SOURCE, error_line, 0, 0, None)
        
        while self.position < len(self.tokens):
            token = self.tokens[self.position]
            if token.type == TokenType.SOURCE:
                program.children.append(self._parse_source())
            elif token.type == TokenType.TARGET:
                target_node = self._parse_target()
                self.targets[target_node.name] = target_node
                program.children.append(target_node)
            elif token.type == TokenType.ROUTE_HEADER:
                route_block = self._parse_route_block()
                
                # Проверка наличия определения цели для маршрута
                if route_block.target_name not in self.targets:
                    error_line = f"{route_block.target_name}:"
                    hint = self.loc.get(M.Hint.TARGET_DEFINITION_MISSING, target=route_block.target_name)
                    raise DSLSyntaxError(ErrorType.SEMANTIC_TARGET, error_line, token.position, 0, hint)
                
                program.children.append(route_block)
            else:
                self.position += 1
        
        # Сохраняем targets в program для дальнейшего использования
        program._targets = self.targets
        
        # Проверка на наличие хотя бы одного определения маршрута
        route_blocks = [node for node in program.children if node.node_type == NodeType.ROUTE_BLOCK]
        if not route_blocks:
            error_line = "target: (missing)"
            raise DSLSyntaxError(ErrorType.SEMANTIC_ROUTES, error_line, 0, 0, None)
        
        pr(M.Debug.PARSING_FINISH, count=len(program.children))
        
        return program
    
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
    
    def _parse_route_block(self) -> RouteBlockNode:
        """Создает блок маршрутов"""
        token = self.tokens[self.position]
        target_name = token.value
        self.position += 1
        
        route_block = RouteBlockNode(target_name)
        
        pr(M.Debug.PARSING_ROUTE_BLOCK, target=target_name)
        
        # Собираем все строки маршрутов для этого блока
        while self.position < len(self.tokens) and self.tokens[self.position].type == TokenType.ROUTE_LINE:
            route_line = self._parse_route_line()
            route_block.routes.append(route_line)
        
        return route_block
    
    def _parse_route_line(self) -> RouteLineNode:
        """Создает строку маршрута"""
        token = self.tokens[self.position]
        route_data = token.value
        self.position += 1
        
        # Исходное поле
        src_field = FieldSrcNode(route_data['src_field'])
        
        # Конвейер обработки
        pipeline = self._parse_pipeline(route_data['pipeline'])
        
        # Целевое поле (может отсутствовать)
        target_field = None
        if route_data['target_field'] is not None:
            target_field = FieldDstNode(
                route_data['target_field'],
                route_data['target_field_type'] or 'str'
            )
        
        pr(M.Debug.ROUTE_LINE_CREATED, src=src_field.name, dst=target_field.name if target_field else '-')
        
        return RouteLineNode(src_field, pipeline, target_field)
    
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
                    pipeline.items.append(PipelineItemNode(
                        PipelineItemType.PY_FUNC,
                        segment
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


# Импортируем TokenType в конце файла, чтобы избежать циклических зависимостей
from .constants import TokenType, NodeType 