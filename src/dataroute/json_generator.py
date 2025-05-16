from typing import Dict, List, Any
import json
import os
import glob
import re

from .ast_nodes import ASTVisitor
from .constants import PipelineItemType
from .localization import Localization, Messages as M
from .config import Config
from .mess_core import pr
from .errors import ExternalVarsFolderNotFoundError, ExternalVarFileNotFoundError, ExternalVarPathNotFoundError


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
            # Вместо прямого вывода сообщения, создаем и сохраняем ошибку
            # для последующей обработки
            self._vars_folder_error = ExternalVarsFolderNotFoundError(vars_folder)
        else:
            self._vars_folder_error = None
        
        self.loc = Localization(Config.get_lang())
    
    def reset(self):
        """Сбрасывает состояние генератора для повторного использования"""
        self.result = {}
        self.source_type = None
        self.current_target = None
        self.void_counters = {}
        self.target_name_map = {}
        self.target_info_map = {}
        self.global_vars = {}
        # НЕ сбрасываем кеш внешних переменных, чтобы избежать повторной загрузки
        # НЕ сбрасываем vars_folder и _vars_folder_error
        
        # Обновляем локализацию на случай, если язык изменился
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
    
    def get_external_var_value(self, var_path: str, node_context=None):
        """
        Получает значение внешней переменной по пути с точечной нотацией
        
        Args:
            var_path (str): Путь к переменной в формате $$file.path.to.var
            node_context: Опциональный контекст узла для лучшей диагностики ошибок
        
        Returns:
            Any: Значение переменной
            
        Raises:
            ExternalVarsFolderNotFoundError: Если папка с переменными не найдена
            ExternalVarFileNotFoundError: Если файл с переменными не найден
            ExternalVarPathNotFoundError: Если путь в переменной не найден
        """
        if not var_path.startswith('$$'):
            return None
        
        # Если была ошибка при загрузке папки с переменными, вызываем исключение
        if hasattr(self, '_vars_folder_error') and self._vars_folder_error:
            if node_context and hasattr(node_context, 'source_line'):
                # Создаем новую ошибку с информацией о позиции из узла
                raise ExternalVarsFolderNotFoundError(
                    self._vars_folder_error.folder_name,
                    line=node_context.source_line,
                    line_num=node_context.line_num,
                    position=node_context.position
                )
            raise self._vars_folder_error
        
        # Убираем префикс $$ и разбиваем по точкам
        path_parts = var_path[2:].split('.')
        
        if not path_parts:
            raise ValueError(f"Некорректная внешняя переменная: {var_path}")
        
        # Первая часть - имя файла
        file_name = path_parts[0]
        
        # Проверяем, что файл загружен
        if file_name not in self.external_vars:
            # Создаем ошибку с учетом контекста узла, если он предоставлен
            if node_context and hasattr(node_context, 'source_line'):
                raise ExternalVarFileNotFoundError(
                    file_name,
                    line=node_context.source_line,
                    line_num=node_context.line_num,
                    position=node_context.position,
                    node_value=node_context.value
                )
            # Если нет контекста, используем стандартную ошибку
            raise ExternalVarFileNotFoundError(file_name)
        
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
                # Генерируем специальную ошибку для пути с учетом контекста
                if node_context and hasattr(node_context, 'source_line'):
                    raise ExternalVarPathNotFoundError(
                        path_so_far,
                        line=node_context.source_line,
                        line_num=node_context.line_num,
                        position=node_context.position,
                        node_value=node_context.value
                    )
                # Если нет контекста, используем стандартную ошибку
                raise ExternalVarPathNotFoundError(path_so_far)
                
        return current
    
    def visit_program(self, node):
        """Обход корневого узла программы"""
        self.target_info_map = getattr(node, '_targets', {})
        global_vars = getattr(node, '_global_vars', {})
        # Проверка дубликатов только по полному ключу type/name
        type_name_keys = set()
        for name, target_node in self.target_info_map.items():
            type_name_key = f"{target_node.target_type['type']}/{target_node.target_type['name']}"
            if type_name_key in type_name_keys:
                from .errors import DSLSyntaxError
                from .constants import ErrorType
                from .localization import Messages
                raise DSLSyntaxError(
                    ErrorType.DUPLICATE_TARGET_NAME_TYPE,
                    type_name_key,
                    0,
                    0,
                    self.loc.get(Messages.Hint.DUPLICATE_TARGET_NAME_TYPE),
                    target_name=target_node.value,
                    target_type=type_name_key
                )
            type_name_keys.add(type_name_key)
            self.target_name_map[name] = type_name_key
        for child in node.children:
            child.accept(self)
        if self.global_vars:
            self.result["global_vars"] = self.global_vars
        pr(M.Info.JSON_GENERATED, count=len(self.result))
        return self.result
    
    def visit_source(self, node):
        """Обход узла источника данных"""
        self.source_type = node.source_type
        pr(M.Info.SET_SOURCE_TYPE, type=self.source_type)
    
    def visit_target(self, node):
        # Ключ для результата теперь type/name
        type_name_key = f"{node.target_type['type']}/{node.target_type['name']}"
        self.target_name_map[node.name] = type_name_key
        pr(M.Info.TARGET_ADDED, value=node.value, type=node.target_type)
    
    def visit_route_block(self, node):
        """Обход блока маршрутов"""
        target_name = node.target_name
        target_node = self.target_info_map.get(target_name)
        if target_node:
            type_name_key = f"{target_node.target_type['type']}/{target_node.target_type['name']}"
            self.target_name_map[target_name] = type_name_key
            if type_name_key not in self.result:
                self.result[type_name_key] = {
                    "sourse_type": self.source_type,
                    "target_type": target_node.target_type,
                    "routes": {}
                }
            self.current_target = type_name_key
        else:
            self.current_target = target_name
        pr(M.Debug.ROUTE_PROCESSING, target=self.current_target)
        for route in node.routes:
            route.accept(self)
    
    def visit_route_line(self, node):
        """Обход строки маршрута"""
        # Получаем данные о маршруте
        src_field = node.src_field.accept(self)
        pipeline = node.pipeline.accept(self)
        
        # Определяем, что делать с целевым полем
        if node.target_field:
            # Получаем информацию о целевом поле
            target_field, target_field_type = node.target_field.accept(self)
            
            # Важно! Проверяем случай пустого поля []
            if node.target_field.name == "":
                # Если целевое поле - пустые скобки [], оба значения должны быть null
                target_field = None
                target_field_type = None
        else:
            # Если целевого поля вообще нет в маршруте, значения должны быть null
            target_field = None
            target_field_type = None
        
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
        # Если имя поля пустое (пустое поле []), возвращаем None для имени и типа
        if node.name == "":
            return None, None
        
        # Для обычных полей возвращаем имя и тип
        return node.name, node.type_name
    
    def visit_func_call(self, node):
        """Обход вызова функции"""
        param = node.params.get("param", "$this")
        is_external_var = node.params.get("is_external_var", False)
        
        # Словарь с информацией о внешней переменной
        external_var = {
            "is_external_var": is_external_var,
            "value": None
        }
        
        # Строгая проверка внешних переменных
        if is_external_var and param.startswith('$$'):
            # Проверка доступности внешней переменной
            try:
                # Передаем узел для контекста ошибки
                external_value = self.get_external_var_value(param, node_context=node)
                if external_value is None:
                    raise ValueError(f"Внешняя переменная {param} не найдена")
                # Сохраняем значение внешней переменной в словаре
                external_var["value"] = external_value
            except (ExternalVarsFolderNotFoundError, ExternalVarFileNotFoundError) as e:
                # Поднимаем специализированную ошибку с информацией о позиции
                raise
            except ExternalVarPathNotFoundError as e:
                # Если у узла есть информация о позиции, используем её
                if hasattr(node, 'source_line') and node.source_line:
                    raise ExternalVarPathNotFoundError(
                        e.path, 
                        line=node.source_line, 
                        line_num=node.line_num, 
                        position=node.position, 
                        node_value=node.value
                    )
                raise
        
        return {
            "type": PipelineItemType.PY_FUNC.value,
            "param": param,
            "external_var": external_var,  # Вместо is_external_var используем словарь external_var
            "full_str": node.value
        }
    
    def visit_direct_map(self, node):
        """Обход прямого отображения"""
        param = node.params.get("param", "$this")
        is_external_var = node.params.get("is_external_var", False)
        
        # Словарь с информацией о внешней переменной
        external_var = {
            "is_external_var": is_external_var,
            "value": None
        }
        
        # Строгая проверка внешних переменных - аналогично visit_func_call
        if is_external_var and param.startswith('$$'):
            try:
                # Передаем узел для контекста ошибки
                external_value = self.get_external_var_value(param, node_context=node)
                if external_value is None:
                    raise ValueError(f"Внешняя переменная {param} не найдена")
                # Сохраняем значение внешней переменной в словаре
                external_var["value"] = external_value
            except (ExternalVarsFolderNotFoundError, ExternalVarFileNotFoundError) as e:
                # Поднимаем специализированную ошибку
                raise
            except ExternalVarPathNotFoundError as e:
                # Если у узла есть информация о позиции, используем её
                if hasattr(node, 'source_line') and node.source_line:
                    raise ExternalVarPathNotFoundError(
                        e.path, 
                        line=node.source_line, 
                        line_num=node.line_num, 
                        position=node.position, 
                        node_value=node.value
                    )
                raise
        
        return {
            "type": PipelineItemType.DIRECT.value,
            "param": param,
            "external_var": external_var,  # Вместо is_external_var используем словарь external_var
            "full_str": node.value
        }
    
    def visit_condition(self, node):
        """Обход условного выражения"""
        cond = node.value.strip()
        
        # Находим ключевые слова IF, ELIF, ELSE
        pattern = re.compile(r'(?i)\b(IF|ELIF|ELSE)\b')
        matches = list(pattern.finditer(cond))
        
        if not matches:
            return {"type": PipelineItemType.CONDITION.value, "full_str": cond}
            
        # Формируем ветви
        branches = []
        for i, m in enumerate(matches):
            key = m.group(1).upper()
            start = m.start()
            end = matches[i+1].start() if i+1 < len(matches) else len(cond)
            branch_text = cond[start:end].strip()
            branches.append((key, branch_text))
            
        # Определяем тип конструкции
        has_elif = any(k.upper() == "ELIF" for k, _ in branches)
        sub_type = "if_elifs_else" if has_elif else "if_else"
        
        result = {
            "type": PipelineItemType.CONDITION.value, 
            "sub_type": sub_type,
            "full_str": cond
        }
        
        elif_counter = 0
        
        # Обрабатываем ветви
        for key, text in branches:
            key = key.upper()
            if key in ("IF", "ELIF"):
                # Извлекаем условие и действие
                # Для IF и ELIF паттерн: KEY(condition): action
                match = re.match(r'(?i)' + key + r'\s*\(([^)]*)\)\s*:\s*(.*)', text)
                
                if match:
                    exp_str = match.group(1).strip()
                    do_str = match.group(2).strip()
                    
                    # Парсинг выражения
                    if exp_str.startswith('*'):
                        exp_json = {
                            "type": PipelineItemType.PY_FUNC.value, 
                            "param": "$this", 
                            "full_str": exp_str
                        }
                    else:
                        exp_json = {
                            "type": "cond_exp", 
                            "full_str": exp_str
                        }
                    
                    # Парсинг действия
                    do_json = self._build_do_json(do_str)
                    
                    if key == "IF":
                        result["if"] = {"exp": exp_json, "do": do_json}
                    else:
                        elif_counter += 1
                        result[f"elif_{elif_counter}"] = {"exp": exp_json, "do": do_json}
                else:
                    # Если не нашли соответствие паттерну, пробуем другой подход
                    if "(" in text and ")" in text and ":" in text:
                        # Ищем скобки напрямую
                        open_paren = text.find("(")
                        close_paren = text.find(")", open_paren)
                        colon = text.find(":", close_paren)
                        
                        if open_paren != -1 and close_paren != -1 and colon != -1:
                            exp_str = text[open_paren+1:close_paren].strip()
                            do_str = text[colon+1:].strip()
                            
                            # Парсинг выражения
                            if exp_str.startswith('*'):
                                exp_json = {
                                    "type": PipelineItemType.PY_FUNC.value, 
                                    "param": "$this", 
                                    "full_str": exp_str
                                }
                            else:
                                exp_json = {
                                    "type": "cond_exp", 
                                    "full_str": exp_str
                                }
                            
                            # Парсинг действия
                            do_json = self._build_do_json(do_str)
                            
                            if key == "IF":
                                result["if"] = {"exp": exp_json, "do": do_json}
                            else:
                                elif_counter += 1
                                result[f"elif_{elif_counter}"] = {"exp": exp_json, "do": do_json}
            
            elif key == "ELSE":
                # Для ELSE паттерн: ELSE: action
                match = re.match(r'(?i)ELSE\s*:\s*(.*)', text)
                
                if match:
                    do_str = match.group(1).strip()
                    do_json = self._build_do_json(do_str)
                    result["else"] = {"do": do_json}
                else:
                    # Если не нашли соответствие паттерну, пробуем другой подход
                    if ":" in text:
                        colon = text.find(":")
                        do_str = text[colon+1:].strip()
                        do_json = self._build_do_json(do_str)
                        result["else"] = {"do": do_json}
        
        return result
    
    def visit_event(self, node):
        """Обход события"""
        return {
            "type": PipelineItemType.EVENT.value,
            "sub_type": node.params.get("sub_type"),
            "param": node.params.get("param"),
            "full_str": node.value
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

    # Вспомогательный метод для разбора действий внутри условного оператора
    def _build_do_json(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        # Функция Python
        if text.startswith('*'):
            func_text = text[1:]
            param = "$this"
            if '(' in func_text and func_text.endswith(')'):
                idx = func_text.find('(')
                param = func_text[idx+1:-1].strip()
            return {"type": PipelineItemType.PY_FUNC.value, "param": param, "full_str": text}
        # Событие: SKIP, ROLLBACK, NOTIFY
        match = re.match(r'(?i)^(SKIP|ROLLBACK|NOTIFY)\((.*)\)$', text)
        if match:
            event_type = match.group(1).upper()
            param_text = match.group(2)
            return {"type": PipelineItemType.EVENT.value, "sub_type": event_type, "param": param_text, "full_str": text}
        # Прямое отображение или переменная
        if text.startswith('$') or text.isidentifier():
            return {"type": PipelineItemType.DIRECT.value, "param": text, "full_str": text}
        # Логическое выражение
        return {"type": "cond_exp", "full_str": text} 