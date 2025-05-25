from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from .constants import NodeType, PipelineItemType


class ASTNode(ABC):
    """Базовый класс для узла абстрактного синтаксического дерева"""
    node_type: NodeType
    # Информация о позиции в исходном коде
    source_line: str = ""  # Исходная строка
    line_num: int = 0       # Номер строки
    position: int = 0       # Позиция в строке
    
    @abstractmethod
    def accept(self, visitor):
        """Метод для паттерна посетителя"""
        pass

    def set_position_info(self, source_line: str, line_num: int, position: int):
        """Устанавливает информацию о позиции узла в исходном коде"""
        self.source_line = source_line
        self.line_num = line_num
        self.position = position
        return self


class ASTVisitor(ABC):
    """Базовый класс посетителя для обхода AST"""
    
    @abstractmethod
    def visit_program(self, node):
        pass
    
    @abstractmethod
    def visit_source(self, node):
        pass
    
    @abstractmethod
    def visit_target(self, node):
        pass
    
    @abstractmethod
    def visit_route_block(self, node):
        pass
    
    @abstractmethod
    def visit_route_line(self, node):
        pass
    
    @abstractmethod
    def visit_pipeline(self, node):
        pass
    
    @abstractmethod
    def visit_field_src(self, node):
        pass
    
    @abstractmethod
    def visit_field_dst(self, node):
        pass
    
    @abstractmethod
    def visit_global_var(self, node):
        pass

    @abstractmethod
    def visit_func_call(self, node):
        pass
    
    @abstractmethod
    def visit_direct_map(self, node):
        pass
    
    @abstractmethod
    def visit_condition(self, node):
        pass
    
    @abstractmethod
    def visit_event(self, node):
        pass

    @abstractmethod
    def visit_field(self, node):
        pass


# ==============================================================
# КОНКРЕТНЫЕ УЗЛЫ AST
# ==============================================================

@dataclass
class ProgramNode(ASTNode):
    """Корневой узел программы"""
    children: List[ASTNode] = field(default_factory=list)
    node_type: NodeType = NodeType.PROGRAM
    
    def accept(self, visitor):
        return visitor.visit_program(self)


@dataclass
class SourceNode(ASTNode):
    """Узел определения источника данных"""
    source_type: str
    node_type: NodeType = NodeType.SOURCE
    
    def accept(self, visitor):
        return visitor.visit_source(self)


@dataclass
class TargetNode(ASTNode):
    """Узел определения цели"""
    name: str
    target_type: str
    value: str
    node_type: NodeType = NodeType.TARGET
    
    def accept(self, visitor):
        return visitor.visit_target(self)


@dataclass
class RouteBlockNode(ASTNode):
    """Блок маршрутов для конкретной цели"""
    target_name: str
    routes: List['RouteLineNode'] = field(default_factory=list)
    node_type: NodeType = NodeType.ROUTE_BLOCK
    
    def accept(self, visitor):
        return visitor.visit_route_block(self)


@dataclass
class FieldSrcNode(ASTNode):
    """Исходное поле"""
    name: str
    node_type: NodeType = NodeType.FIELD_SRC
    
    def accept(self, visitor):
        return visitor.visit_field_src(self)


@dataclass
class FieldDstNode(ASTNode):
    """Целевое поле"""
    name: str
    type_name: str
    node_type: NodeType = NodeType.FIELD_DST
    
    def accept(self, visitor):
        return visitor.visit_field_dst(self)


@dataclass
class PipelineItemNode(ASTNode):
    """Базовый класс для элементов конвейера"""
    value: str
    params: Dict[str, Any] = field(default_factory=dict)
    
    def accept(self, visitor):
        pass


@dataclass
class PipelineNode(ASTNode):
    """Узел конвейера обработки"""
    items: List['PipelineItemNode'] = field(default_factory=list)
    node_type: NodeType = NodeType.PIPELINE
    
    def accept(self, visitor):
        return visitor.visit_pipeline(self)


@dataclass
class RouteLineNode(ASTNode):
    """Строка маршрута"""
    src_field: FieldSrcNode
    pipeline: PipelineNode
    target_field: Optional[FieldDstNode] = None
    node_type: NodeType = NodeType.ROUTE_LINE
    
    def accept(self, visitor):
        return visitor.visit_route_line(self)


@dataclass
class GlobalVarNode(ASTNode):
    """Узел глобальной переменной"""
    name: str
    value: Any
    value_type: str
    node_type: NodeType = NodeType.GLOBAL_VAR
    
    def accept(self, visitor):
        return visitor.visit_global_var(self)


@dataclass
class FuncCallNode(PipelineItemNode):
    """Узел вызова функции"""
    node_type: NodeType = NodeType.FUNC_CALL
    
    def accept(self, visitor):
        return visitor.visit_func_call(self)


@dataclass
class DirectMapNode(PipelineItemNode):
    """Узел прямого отображения"""
    node_type: NodeType = NodeType.DIRECT_MAP
    
    def accept(self, visitor):
        return visitor.visit_direct_map(self)


@dataclass
class ConditionNode(PipelineItemNode):
    """Узел условного выражения"""
    node_type: NodeType = NodeType.CONDITION
    
    def accept(self, visitor):
        return visitor.visit_condition(self)


@dataclass
class EventNode(PipelineItemNode):
    """Узел события"""
    node_type: NodeType = NodeType.EVENT
    
    def accept(self, visitor):
        return visitor.visit_event(self) 