import re
import json
import sys
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

# ==============================================================
# КОНСТАНТЫ И ПЕРЕЧИСЛЕНИЯ
# ==============================================================

class TokenType(Enum):
    """Типы токенов в языке DSL"""
    SOURCE = auto()      # Определение источника (sourse=dict)
    TARGET = auto()      # Определение цели (target1=dict("target1"))
    ROUTE_HEADER = auto() # Заголовок маршрута (target1:)
    ROUTE_LINE = auto()  # Строка маршрута ([id] -> |*s1| -> [name](type))
    CONDITION = auto()   # Условное выражение (if (exp) : (else))
    EVENT = auto()       # Событие (ROLLBACK, SKIP, NOTIFY)


class NodeType(Enum):
    """Типы узлов AST"""
    PROGRAM = auto()      # Корневой узел программы
    SOURCE = auto()       # Определение источника
    TARGET = auto()       # Определение цели
    ROUTE_BLOCK = auto()  # Блок маршрутов
    ROUTE_LINE = auto()   # Строка маршрута
    PIPELINE = auto()     # Конвейер обработки
    FIELD_SRC = auto()    # Исходное поле
    FIELD_DST = auto()    # Целевое поле
    CONDITION = auto()    # Условное выражение
    EVENT = auto()        # Событие
    FUNC_CALL = auto()    # Вызов функции
    DIRECT_MAP = auto()   # Прямое отображение


class PipelineItemType(Enum):
    """Типы элементов конвейера"""
    PY_FUNC = "py_func"   # Функция Python с *
    DIRECT = "direct"     # Прямое отображение
    CONDITION = "condition" # Условный оператор
    EVENT = "event"       # Событие


# ==============================================================
# РЕГУЛЯРНЫЕ ВЫРАЖЕНИЯ ДЛЯ ТОКЕНИЗАЦИИ
# ==============================================================

PATTERNS = {
    # Определение источника: sourse=dict
    TokenType.SOURCE: r'sourse\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)',
    
    # Определение цели: target1=dict("target1")
    TokenType.TARGET: r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*"([^"]*)"\s*\)',
    
    # Заголовок маршрута: target1:
    TokenType.ROUTE_HEADER: r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:',
    
    # Строка маршрута с отступом: [field] -> |pipeline| -> [field](type)
    TokenType.ROUTE_LINE: r'^\s+\[([a-zA-Z0-9_]*)\]\s*->\s*(\|[^|]*(?:\|[^|]*)*\|)\s*(?:->\s*\[([a-zA-Z0-9_]+)\]\(([a-zA-Z0-9_]+)\))?'
}


# ==============================================================
# БАЗОВЫЕ КЛАССЫ
# ==============================================================

@dataclass
class Token:
    """Токен, полученный при лексическом анализе"""
    type: TokenType
    value: Any
    position: int = 0
    
    def __repr__(self):
        return f"Token({self.type.name}, {self.value})"


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
    dst_field: Optional[FieldDstNode] = None
    node_type: NodeType = NodeType.ROUTE_LINE
    
    def accept(self, visitor):
        return visitor.visit_route_line(self)


# ==============================================================
# ЛЕКСИЧЕСКИЙ АНАЛИЗАТОР
# ==============================================================

class Lexer:
    """Лексический анализатор для преобразования текста в токены"""
    
    def __init__(self, debug=False):
        self.tokens = []
        self.debug = debug
    
    def tokenize(self, text: str) -> List[Token]:
        """Разбивает текст на токены"""
        self.tokens = []
        lines = text.strip().split('\n')
        
        if self.debug:
            print("Начинаю токенизацию...")
        
        for line_num, line in enumerate(lines):
            original_line = line
            line = line.strip()
            if not line:
                continue
            
            # Анализируем строку на соответствие шаблонам
            matched = False
            
            # Определение источника (sourse=dict)
            if not matched:
                match = re.match(PATTERNS[TokenType.SOURCE], line)
                if match:
                    self.tokens.append(Token(TokenType.SOURCE, match.group(1), line_num))
                    if self.debug:
                        print(f"Токен SOURCE: {match.group(1)}")
                    matched = True
            
            # Определение цели (target1=dict("target1"))
            if not matched:
                match = re.match(PATTERNS[TokenType.TARGET], line)
                if match:
                    target_info = {
                        'name': match.group(1),
                        'type': match.group(2),
                        'value': match.group(3)
                    }
                    self.tokens.append(Token(TokenType.TARGET, target_info, line_num))
                    if self.debug:
                        print(f"Токен TARGET: {target_info}")
                    matched = True
            
            # Заголовок маршрута (target1:)
            if not matched:
                match = re.match(PATTERNS[TokenType.ROUTE_HEADER], line)
                if match:
                    self.tokens.append(Token(TokenType.ROUTE_HEADER, match.group(1), line_num))
                    if self.debug:
                        print(f"Токен ROUTE_HEADER: {match.group(1)}")
                    matched = True
            
            # Строка маршрута с отступом ([id] -> |*s1| -> [external_id](str))
            if not matched and original_line.startswith('    '):
                match = re.match(PATTERNS[TokenType.ROUTE_LINE], original_line)
                if match:
                    # Извлекаем компоненты маршрута
                    src_field = match.group(1)
                    pipeline_str = match.group(2)
                    dst_field = match.group(3) if len(match.groups()) > 2 else None
                    dst_type = match.group(4) if len(match.groups()) > 3 else None
                    
                    route_info = {
                        'src_field': src_field,
                        'pipeline': pipeline_str,
                        'dst_field': dst_field,
                        'dst_type': dst_type
                    }
                    
                    self.tokens.append(Token(TokenType.ROUTE_LINE, route_info, line_num))
                    if self.debug:
                        print(f"Токен ROUTE_LINE: {route_info}")
                    matched = True
            
            if not matched and self.debug:
                print(f"ОШИБКА ТОКЕНИЗАЦИИ: Не распознана строка: {line}")
                sys.exit(1)
        
        if self.debug:
            print(f"Токенизация завершена. Создано токенов: {len(self.tokens)}")
        
        return self.tokens


# ==============================================================
# СИНТАКСИЧЕСКИЙ АНАЛИЗАТОР
# ==============================================================

class Parser:
    """Синтаксический анализатор для построения AST из токенов"""
    
    def __init__(self, debug=False):
        self.tokens = []
        self.position = 0
        self.debug = debug
    
    def parse(self, tokens: List[Token]) -> ProgramNode:
        """Создает AST из токенов"""
        self.tokens = tokens
        self.position = 0
        
        program = ProgramNode()
        
        if self.debug:
            print("Начинаю синтаксический анализ...")
        
        while self.position < len(self.tokens):
            token = self.tokens[self.position]
            
            if token.type == TokenType.SOURCE:
                program.children.append(self._parse_source())
            elif token.type == TokenType.TARGET:
                program.children.append(self._parse_target())
            elif token.type == TokenType.ROUTE_HEADER:
                program.children.append(self._parse_route_block())
            else:
                self.position += 1
        
        if self.debug:
            print(f"Синтаксический анализ завершен. Создано узлов: {len(program.children)}")
        
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
        
        if self.debug:
            print(f"Разбор блока маршрутов для {target_name}")
        
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
        dst_field = None
        if route_data['dst_field'] is not None:
            dst_field = FieldDstNode(
                route_data['dst_field'],
                route_data['dst_type'] or 'str'
            )
        
        if self.debug:
            print(f"  Создана строка маршрута: {src_field.name} -> ... -> {dst_field.name if dst_field else '-'}")
        
        return RouteLineNode(src_field, pipeline, dst_field)
    
    def _parse_pipeline(self, pipeline_str: str) -> PipelineNode:
        """Создает конвейер обработки"""
        # Удаляем начальный и конечный |
        if pipeline_str.startswith('|') and pipeline_str.endswith('|'):
            pipeline_content = pipeline_str[1:-1]
        else:
            pipeline_content = pipeline_str
        
        # Разбиваем на элементы
        pipeline = PipelineNode()
        
        if pipeline_content:
            # Разбиваем по | внутри содержимого
            segments = pipeline_content.split('|')
            
            for segment in segments:
                segment = segment.strip()
                if not segment:
                    continue
                
                if segment.startswith('*'):
                    # Функция Python
                    pipeline.items.append(PipelineItemNode(
                        PipelineItemType.PY_FUNC,
                        segment
                    ))
                    if self.debug:
                        print(f"    Добавлен элемент пайплайна: {PipelineItemType.PY_FUNC.value} {segment}")
                else:
                    # Прямое отображение
                    pipeline.items.append(PipelineItemNode(
                        PipelineItemType.DIRECT,
                        segment
                    ))
                    if self.debug:
                        print(f"    Добавлен элемент пайплайна: {PipelineItemType.DIRECT.value} {segment}")
        
        return pipeline


# ==============================================================
# ПОСЕТИТЕЛИ AST
# ==============================================================

class JSONGenerator(ASTVisitor):
    """Посетитель для генерации JSON из AST"""
    
    def __init__(self, debug=False):
        self.result = {}
        self.source_type = None
        self.current_target = None
        self.void_counters = {}
        self.target_name_map = {}
        self.debug = debug
    
    def visit_program(self, node):
        """Обход корневого узла программы"""
        for child in node.children:
            child.accept(self)
        
        if self.debug:
            print(f"JSON сгенерирован. {len(self.result)} целей")
        
        return self.result
    
    def visit_source(self, node):
        """Обход узла источника данных"""
        self.source_type = node.source_type
        if self.debug:
            print(f"Установлен тип источника: {self.source_type}")
    
    def visit_target(self, node):
        """Обход узла цели"""
        target_key = node.value
        self.result[target_key] = {
            "sourse_type": self.source_type,
            "target_type": node.target_type,
            "routes": {}
        }
        
        # Сохраняем отображение имени на ключ
        self.target_name_map[node.name] = target_key
        
        if self.debug:
            print(f"Добавлена цель: {target_key} (тип: {node.target_type})")
    
    def visit_route_block(self, node):
        """Обход блока маршрутов"""
        target_name = node.target_name
        
        # Находим соответствующую цель в результате
        if target_name in self.target_name_map:
            self.current_target = self.target_name_map[target_name]
        else:
            # Пробуем найти подходящую цель
            for name, key in self.target_name_map.items():
                if name.startswith(target_name) or target_name in name:
                    self.current_target = key
                    break
            else:
                self.current_target = target_name
        
        if self.debug:
            print(f"Обработка маршрутов для цели: {self.current_target}")
        
        # Обрабатываем все маршруты
        for route in node.routes:
            route.accept(self)
    
    def visit_route_line(self, node):
        """Обход строки маршрута"""
        # Получаем данные о маршруте
        src_field = node.src_field.accept(self)
        pipeline = node.pipeline.accept(self)
        
        # Если целевое поле не указано, используем исходное
        if node.dst_field:
            dst_field, dst_type = node.dst_field.accept(self)
        else:
            dst_field = src_field
            dst_type = "str"
        
        # Для пустого исходного поля создаем специальный ключ
        route_key = src_field if src_field else self._get_void_key()
        
        # Добавляем маршрут в результат
        if self.current_target in self.result:
            self.result[self.current_target]["routes"][route_key] = {
                "pipeline": pipeline,
                "final_type": dst_type,
                "final_name": dst_field
            }
            
            if self.debug:
                print(f"Добавлен маршрут: {route_key} -> {dst_field}({dst_type})")
    
    def visit_pipeline(self, node):
        """Обход конвейера обработки"""
        result = {}
        
        for idx, item in enumerate(node.items, 1):
            result[str(idx)] = item.accept(self)
        
        return result
    
    def visit_field_src(self, node):
        """Обход исходного поля"""
        return node.name
    
    def visit_field_dst(self, node):
        """Обход целевого поля"""
        return node.name, node.type_name
    
    def visit_func_call(self, node):
        """Обход вызова функции"""
        return {
            "type": PipelineItemType.PY_FUNC.value,
            "param": node.params.get("param", "$this"),
            "full_str": node.value
        }
    
    def visit_direct_map(self, node):
        """Обход прямого отображения"""
        return {
            "type": PipelineItemType.DIRECT.value,
            "param": node.params.get("param", "$this"),
            "full_str": node.value
        }
    
    def visit_condition(self, node):
        """Обход условного выражения"""
        return {
            "type": PipelineItemType.CONDITION.value,
            "condition": node.value,
            "params": node.params
        }
    
    def visit_event(self, node):
        """Обход события"""
        return {
            "type": PipelineItemType.EVENT.value,
            "event": node.value,
            "params": node.params
        }
    
    def _get_void_key(self):
        """Создает ключ для пустого исходного поля"""
        if self.current_target not in self.void_counters:
            self.void_counters[self.current_target] = 0
        
        self.void_counters[self.current_target] += 1
        return f"__void{self.void_counters[self.current_target]}"


# ==============================================================
# ИНТЕРПРЕТАТОР
# ==============================================================

class DataRouteParser:
    """Класс для парсинга и интерпретации DSL"""
    
    def __init__(self, debug=False):
        self.lexer = Lexer(debug)
        self.parser = Parser(debug)
        self.json_generator = JSONGenerator(debug)
        self.debug = debug
    
    def parse(self, text: str) -> Dict:
        """Обрабатывает DSL и возвращает структуру JSON"""
        if self.debug:
            print("=== Начало обработки DSL ===")
        
        # Этап 1: Лексический анализ
        tokens = self.lexer.tokenize(text)
        
        # Этап 2: Синтаксический анализ
        ast = self.parser.parse(tokens)
        
        # Этап 3: Обход AST и генерация JSON
        result = ast.accept(self.json_generator)
        
        if self.debug:
            print("=== Обработка DSL завершена ===")
        
        return result


# ==============================================================
# ИСПОЛЬЗОВАНИЕ
# ==============================================================

if __name__ == "__main__":
    test_input = """sourse=dict

target1=dict("target_new")
target2=dict("target_new_2")

target1:
    [id] -> |*s1| -> [external_id](str)
    [name] -> |*lower| -> [low_name](str)
    [age] -> |*check_age| -> [age](int)
    [test1] -> [test_NORM](str)

target2:
    [id] -> |id| -> [id](str)
    [name] -> |*s1|*upper| -> [name](str)
    [] -> |*gen_rand_int| -> [score](int)
    [] -> |*gen_rand_int| -> [score2](int)
"""

    # Создаем парсер с включенной отладкой
    parser = DataRouteParser(debug=True)
    
    try:
        # Обрабатываем DSL
        result = parser.parse(test_input)
        
        # Выводим результат
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Ошибка при обработке DSL: {e}")
        import traceback
        traceback.print_exc() 