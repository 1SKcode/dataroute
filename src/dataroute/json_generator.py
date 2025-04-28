from typing import Dict, List, Any

from .ast_nodes import ASTVisitor
from .constants import PipelineItemType
from .localization import Localization, Messages as M


class JSONGenerator(ASTVisitor):
    """Посетитель для генерации JSON из AST"""
    
    def __init__(self, debug=False, lang="ru"):
        self.result = {}
        self.source_type = None
        self.current_target = None
        self.void_counters = {}
        self.target_name_map = {}
        self.target_info_map = {}  # Сохраняем инфу о таргетах
        self.debug = debug
        self.lang = lang
        self.loc = Localization(lang)
    
    def visit_program(self, node):
        """Обход корневого узла программы"""
        # Собираем карту таргетов (name -> TargetNode)
        self.target_info_map = getattr(node, '_targets', {})
        for name, target_node in self.target_info_map.items():
            self.target_name_map[name] = target_node.value
        for child in node.children:
            child.accept(self)
        if self.debug:
            print(self.loc.get(M.Info.JSON_GENERATED, count=len(self.result)))
        return self.result
    
    def visit_source(self, node):
        """Обход узла источника данных"""
        self.source_type = node.source_type
        if self.debug:
            print(self.loc.get(M.Info.SET_SOURCE_TYPE, type=self.source_type))
    
    def visit_target(self, node):
        # Не добавляем ключ в self.result, только сохраняем target_name_map
        self.target_name_map[node.name] = node.value
        if self.debug:
            print(self.loc.get(M.Info.TARGET_ADDED, value=node.value, type=node.target_type))
    
    def visit_route_block(self, node):
        """Обход блока маршрутов"""
        target_name = node.target_name
        # Получаем инфу о таргете
        target_node = self.target_info_map.get(target_name)
        if target_node:
            target_key = target_node.value
            self.target_name_map[target_name] = target_key
            # Если ключа ещё нет, создаём его (в нужном порядке)
            if target_key not in self.result:
                self.result[target_key] = {
                    "sourse_type": self.source_type,
                    "target_type": target_node.target_type,
                    "routes": {}
                }
            self.current_target = target_key
        else:
            # Фоллбек, если вдруг не нашли
            self.current_target = target_name
        if self.debug:
            print(self.loc.get(M.Info.ROUTE_PROCESSING, target=self.current_target))
        # Обрабатываем все маршруты
        for route in node.routes:
            route.accept(self)
    
    def visit_route_line(self, node):
        """Обход строки маршрута"""
        # Получаем данные о маршруте
        src_field = node.src_field.accept(self)
        pipeline = node.pipeline.accept(self)
        
        # Если целевое поле не указано, используем исходное
        if node.target_field:
            target_field, target_field_type = node.target_field.accept(self)
        else:
            target_field = src_field
            target_field_type = "str"
        
        # Для пустого исходного поля создаем специальный ключ
        route_key = src_field if src_field else self._get_void_key()
        
        # Добавляем маршрут в результат
        if self.current_target in self.result:
            self.result[self.current_target]["routes"][route_key] = {
                "pipeline": pipeline,
                "final_type": target_field_type,
                "final_name": target_field
            }
            
            if self.debug:
                print(self.loc.get(M.Info.ROUTE_ADDED, 
                                  src=route_key, 
                                  dst=target_field, 
                                  type=target_field_type))
    
    def visit_pipeline(self, node):
        """Обход конвейера обработки"""
        if not node.items:
            return None
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