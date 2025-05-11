from typing import Dict, List, Any
import json
import os
import glob

from .ast_nodes import ASTVisitor
from .constants import PipelineItemType
from .localization import Localization, Messages as M
from .config import Config
from .mess_core import pr


class JSONGenerator(ASTVisitor):
    """Посетитель для генерации JSON из AST"""
    
    def __init__(self, vars_folder: str = None):
        self.result = {}
        self.source_type = None
        self.current_target = None
        self.void_counters = {}
        self.target_name_map = {}
        self.target_info_map = {}
        self.global_vars = {}
        self.vars_folder = vars_folder
        self.external_vars = {}  # Кеш для внешних переменных
        
        # Загружаем внешние переменные, если указана папка
        if vars_folder and os.path.isdir(vars_folder):
            self._load_external_vars()
        elif vars_folder and not os.path.isdir(vars_folder):
            pr(f"Ошибка: Папка с внешними переменными не найдена: {vars_folder}", "red")
        
        self.loc = Localization(Config.get_lang())
    
    def _load_external_vars(self):
        """Загружает внешние переменные из JSON файлов в папке"""
        if not self.vars_folder:
            return
        
        # Ищем все JSON файлы в указанной папке
        json_files = glob.glob(os.path.join(self.vars_folder, "*.json"))
        
        for json_file in json_files:
            try:
                # Получаем имя файла без расширения
                file_name = os.path.basename(json_file).rsplit('.', 1)[0]
                
                # Загружаем содержимое JSON файла
                with open(json_file, 'r', encoding='utf-8') as f:
                    file_content = json.load(f)
                    
                # Сохраняем в словаре внешних переменных
                self.external_vars[file_name] = file_content
                pr(f"Загружены внешние переменные из файла: {json_file}")
            except Exception as e:
                pr(f"Ошибка при загрузке файла {json_file}: {str(e)}", "red")
    
    def get_external_var_value(self, var_path: str):
        """Получает значение внешней переменной по пути с точечной нотацией"""
        if not var_path.startswith('$$'):
            return None
        
        # Убираем префикс $$ и разбиваем по точкам
        path_parts = var_path[2:].split('.')
        
        if not path_parts:
            pr(f"Ошибка: Некорректная внешняя переменная: {var_path}", "red")
            return None
        
        # Первая часть - имя файла
        file_name = path_parts[0]
        
        # Проверяем, что файл загружен
        if file_name not in self.external_vars:
            pr(f"Ошибка: Внешняя переменная из файла {file_name} не найдена", "red")
            return None
        
        # Начинаем с корня файла
        current = self.external_vars[file_name]
        
        # Проходим по частям пути
        for i, part in enumerate(path_parts[1:], 1):
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
                current = current[int(part)]
            else:
                path_so_far = '.'.join(path_parts[:i+1])
                pr(f"Ошибка: Путь {path_so_far} не найден во внешних переменных", "red")
                return None
                
        return current
    
    def visit_program(self, node):
        """Обход корневого узла программы"""
        # Собираем карту таргетов (name -> TargetNode)
        self.target_info_map = getattr(node, '_targets', {})
        # Получаем глобальные переменные
        global_vars = getattr(node, '_global_vars', {})
        
        for name, target_node in self.target_info_map.items():
            self.target_name_map[name] = target_node.value
        for child in node.children:
            child.accept(self)
        
        # Добавляем глобальные переменные в результат, если они есть
        if self.global_vars:
            self.result["global_vars"] = self.global_vars
        
        pr(M.Info.JSON_GENERATED, count=len(self.result))
        return self.result
    
    def visit_source(self, node):
        """Обход узла источника данных"""
        self.source_type = node.source_type
        pr(M.Info.SET_SOURCE_TYPE, type=self.source_type)
    
    def visit_target(self, node):
        # Не добавляем ключ в self.result, только сохраняем target_name_map
        self.target_name_map[node.name] = node.value
        pr(M.Info.TARGET_ADDED, value=node.value, type=node.target_type)
    
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
        pr(M.Debug.ROUTE_PROCESSING, target=self.current_target)
        # Обрабатываем все маршруты
        for route in node.routes:
            route.accept(self)
    
    def visit_route_line(self, node):
        """Обход строки маршрута"""
        # Получаем данные о маршруте
        src_field = node.src_field.accept(self)
        pipeline = node.pipeline.accept(self)
        
        # Проверяем наличие целевого поля
        if node.target_field:
            target_field, target_field_type = node.target_field.accept(self)
        else:
            # Если целевое поле не указано совсем, используем исходное
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
            
            # Для вывода сообщения корректно обрабатываем None значения
            display_target = target_field if target_field is not None else "None"
            display_type = target_field_type if target_field_type is not None else "None"
            pr(M.Info.ROUTE_ADDED, src=route_key, dst=display_target, type=display_type)
    
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
        param = node.params.get("param", "$this")
        is_pre_var = node.params.get("is_pre_var", False)
        is_external_var = node.params.get("is_external_var", False)
        
        # Проверяем на наличие внешней переменной
        if is_external_var and param.startswith('$$'):
            # Проверка доступности внешней переменной при необходимости
            external_value = self.get_external_var_value(param)
            if external_value is None:
                pr(f"Предупреждение: Внешняя переменная {param} не найдена, используется как есть", "yellow")
        
        return {
            "type": PipelineItemType.PY_FUNC.value,
            "param": param,
            "is_pre_var": is_pre_var,
            "is_external_var": is_external_var,
            "full_str": node.value
        }
    
    def visit_direct_map(self, node):
        """Обход прямого отображения"""
        param = node.params.get("param", "$this")
        is_pre_var = node.params.get("is_pre_var", False)
        is_external_var = node.params.get("is_external_var", False)
        
        # Проверяем на наличие внешней переменной
        if is_external_var and param.startswith('$$'):
            # Проверка доступности внешней переменной при необходимости
            external_value = self.get_external_var_value(param)
            if external_value is None:
                pr(f"Предупреждение: Внешняя переменная {param} не найдена, используется как есть", "yellow")
        
        return {
            "type": PipelineItemType.DIRECT.value,
            "param": param,
            "is_pre_var": is_pre_var,
            "is_external_var": is_external_var,
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

    def visit_global_var(self, node):
        """Обход узла глобальной переменной"""
        var_name = node.name
        var_value = node.value
        var_type = node.value_type
        
        self.global_vars[var_name] = {"type": var_type, "value": var_value}
        pr(M.Info.GLOBAL_VAR_ADDED, name=var_name, value=var_value, type=var_type)
        
        return {
            "name": var_name,
            "value": var_value,
            "type": var_type
        }

    def visit_field(self, node):
        """Обход узла поля"""
        field_name = node.name.value
        field_value = node.value.value if node.value else None

        # Проверка на переопределение поля
        if field_name in self.current_target:
            pr(self.loc.get(M.WARNING_FIELD_REDEFINED, field_name), "yellow")

        # Обработка внешних переменных
        if field_value and isinstance(field_value, str) and field_value.startswith('$$'):
            external_value = self.get_external_var_value(field_value)
            if external_value is not None:
                field_value = external_value
                pr(f"Использована внешняя переменная: {node.value.value} = {field_value}")

        # Добавляем поле к текущему объекту target
        self.current_target[field_name] = field_value
        
        return {
            "name": field_name,
            "value": field_value,
            "type": node.type_name
        } 