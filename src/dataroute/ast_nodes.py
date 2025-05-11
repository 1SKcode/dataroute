from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from .constants import NodeType, PipelineItemType


class ASTNode(ABC):
    """Базовый класс для узла абстрактного синтаксического дерева"""
    node_type: NodeType
    
    @abstractmethod
    def accept(self, visitor):
        """Принимает посетителя для обхода дерева"""
        pass


class ASTVisitor(ABC):
    """Базовый класс для посетителя AST"""
    
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


class DataSourceStrategy(ABC):
    """Стратегия для работы с различными источниками данных"""
    
    @abstractmethod
    def read_field(self, field_name: str, data: Any) -> Any:
        """Чтение поля из источника данных"""
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
    """Элемент конвейера обработки"""
    item_type: PipelineItemType
    value: str
    params: Dict[str, str] = field(default_factory=lambda: {"param": "$this"})
    
    def accept(self, visitor):
        if self.item_type == PipelineItemType.PY_FUNC:
            return visitor.visit_func_call(self)
        elif self.item_type == PipelineItemType.DIRECT:
            return visitor.visit_direct_map(self)
        elif self.item_type == PipelineItemType.CONDITION:
            return visitor.visit_condition(self)
        elif self.item_type == PipelineItemType.EVENT:
            return visitor.visit_event(self)


@dataclass
class PipelineNode(ASTNode):
    """Конвейер обработки"""
    items: List[PipelineItemNode] = field(default_factory=list)
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
    """Глобальная переменная"""
    name: str            # Имя переменной (без $)
    value: str           # Значение переменной (строковое представление)
    value_type: str = "str"  # Тип переменной (по умолчанию строка)
    node_type: NodeType = NodeType.GLOBAL_VAR
    
    def accept(self, visitor):
        return visitor.visit_global_var(self) 