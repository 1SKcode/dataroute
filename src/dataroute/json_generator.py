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
        super().__init__()
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
        # Обработка использования глобальных переменных в маршрутах
        for token in getattr(node, 'tokens', []):
            if hasattr(token, 'type') and hasattr(token, 'value') and token.type.name == "GLOBAL_VAR_USAGE":
                var_name = token.value["var_name"]
                # Формируем JSON как требуется
                self.result[f"__GLOBVAR__{var_name}"] = {
                    "pipeline": None,
                    "final_type": None,
                    "final_name": None
                }
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
            # Новый маршрут для добавления
            new_route = {
                "pipeline": pipeline,
                "final_type": target_field_type,
                "final_name": target_field
            }
            
            # Проверяем, существует ли уже маршрут с таким ключом
            routes = self.result[self.current_target]["routes"]
            
            if route_key in routes:
                # Если ключ уже существует
                existing_route = routes[route_key]
                
                # Если это первый дубликат, преобразуем существующий маршрут в список
                if not isinstance(existing_route, list):
                    # Сохраняем существующий маршрут как первый элемент списка
                    routes[route_key] = [existing_route]
                
                # Добавляем новый маршрут в список
                routes[route_key].append(new_route)
            else:
                # Если это первый маршрут с таким ключом, добавляем как обычно
                routes[route_key] = new_route
            
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
        def resolve_all_vars(p):
            p = self.resolve_all_external_vars_in_str(p)
            p = self.resolve_all_global_vars_in_str(p)
            return p
        if isinstance(param, list):
            resolved = [resolve_all_vars(p) for p in param]
            def to_str(x):
                if isinstance(x, list):
                    import json
                    return json.dumps(x, ensure_ascii=False)
                if isinstance(x, str):
                    return x
                return str(x)
            param_str = ', '.join(to_str(x) for x in resolved)
            result_param = param_str
        else:
            result_param = resolve_all_vars(param)
        return {
            "type": PipelineItemType.PY_FUNC.value,
            "param": result_param,
            "full_str": node.value
        }
    
    def visit_direct_map(self, node):
        """Обход прямого отображения"""
        param = node.params.get("param", "$this")
        def resolve_all_vars(p):
            p = self.resolve_all_external_vars_in_str(p)
            p = self.resolve_all_global_vars_in_str(p)
            return p
        if isinstance(param, list):
            resolved = [resolve_all_vars(p) for p in param]
            def to_str(x):
                if isinstance(x, list):
                    import json
                    return json.dumps(x, ensure_ascii=False)
                if isinstance(x, str):
                    return x
                return str(x)
            param_str = ', '.join(to_str(x) for x in resolved)
            result_param = param_str
        else:
            result_param = resolve_all_vars(param)
        return {
            "type": PipelineItemType.DIRECT.value,
            "param": result_param,
            "full_str": node.value
        }
    
    def visit_condition(self, node):
        """Обход условного выражения"""
        cond = node.value.strip()
        pattern = re.compile(r'(?i)\b(IF|ELIF|ELSE)\b')
        matches = list(pattern.finditer(cond))
        if not matches:
            return {"type": PipelineItemType.CONDITION.value, "full_str": cond}
        branches = []
        for i, m in enumerate(matches):
            key = m.group(1).upper()
            start = m.start()
            end = matches[i+1].start() if i+1 < len(matches) else len(cond)
            branch_text = cond[start:end].strip()
            branches.append((key, branch_text))
        has_elif = any(k.upper() == "ELIF" for k, _ in branches)
        has_else = any(k.upper() == "ELSE" for k, _ in branches)
        if has_elif:
            sub_type = "if_elifs_else"
        elif has_else:
            sub_type = "if_else"
        else:
            sub_type = "if"
        result = {
            "type": PipelineItemType.CONDITION.value, 
            "sub_type": sub_type,
            "full_str": cond
        }
        elif_counter = 0
        for key, text in branches:
            key = key.upper()
            if key in ("IF", "ELIF"):
                match = re.match(r'(?i)' + key + r'\s*\(([^)]*)\)\s*:\s*(.*)', text)
                if match:
                    exp_str = match.group(1).strip()
                    do_str = match.group(2).strip()
                    # Сначала внешние, потом глобальные переменные
                    exp_str_resolved = self.resolve_all_external_vars_in_str(exp_str)
                    exp_str_resolved = self.resolve_all_global_vars_in_str(exp_str_resolved)
                    if exp_str.startswith('*'):
                        exp_json = {
                            "type": PipelineItemType.PY_FUNC.value, 
                            "param": "$this", 
                            "full_str": exp_str_resolved
                        }
                    else:
                        exp_json = {
                            "type": "cond_exp", 
                            "full_str": exp_str_resolved
                        }
                    do_json = self._build_do_json(do_str)
                    if key == "IF":
                        result["if"] = {"exp": exp_json, "do": do_json}
                    else:
                        elif_counter += 1
                        result[f"elif_{elif_counter}"] = {"exp": exp_json, "do": do_json}
                else:
                    if "(" in text and ")" in text and ":" in text:
                        open_paren = text.find("(")
                        close_paren = text.find(")", open_paren)
                        colon = text.find(":", close_paren)
                        if open_paren != -1 and close_paren != -1 and colon != -1:
                            exp_str = text[open_paren+1:close_paren].strip()
                            do_str = text[colon+1:].strip()
                            exp_str_resolved = self.resolve_all_external_vars_in_str(exp_str)
                            exp_str_resolved = self.resolve_all_global_vars_in_str(exp_str_resolved)
                            if exp_str.startswith('*'):
                                exp_json = {
                                    "type": PipelineItemType.PY_FUNC.value, 
                                    "param": "$this", 
                                    "full_str": exp_str_resolved
                                }
                            else:
                                exp_json = {
                                    "type": "cond_exp", 
                                    "full_str": exp_str_resolved
                                }
                            do_json = self._build_do_json(do_str)
                            if key == "IF":
                                result["if"] = {"exp": exp_json, "do": do_json}
                            else:
                                elif_counter += 1
                                result[f"elif_{elif_counter}"] = {"exp": exp_json, "do": do_json}
            elif key == "ELSE":
                match = re.match(r'(?i)ELSE\s*:\s*(.*)', text)
                if match:
                    do_str = match.group(1).strip()
                    do_json = self._build_do_json(do_str)
                    result["else"] = {"do": do_json}
                else:
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
                # Сначала внешние, потом глобальные переменные
                if param:
                    params = [p.strip() for p in param.split(',')]
                    resolved_params = [self.resolve_all_external_vars_in_str(p) for p in params]
                    resolved_params = [self.resolve_all_global_vars_in_str(p) for p in resolved_params]
                    def to_str(x):
                        if isinstance(x, list):
                            import json
                            return json.dumps(x, ensure_ascii=False)
                        if isinstance(x, str):
                            return x
                        return str(x)
                    if len(resolved_params) == 1:
                        param = to_str(resolved_params[0])
                    else:
                        param = ', '.join(to_str(x) for x in resolved_params)
            else:
                # Если параметр без скобок (например, *func1 $myvar), тоже подставляем переменные
                func_param = func_text.strip()
                if func_param:
                    func_param = self.resolve_all_external_vars_in_str(func_param)
                    func_param = self.resolve_all_global_vars_in_str(func_param)
                    param = func_param
            # Всегда прогоняем param через подстановку, если это строка
            if isinstance(param, str):
                param = self.resolve_all_external_vars_in_str(param)
                param = self.resolve_all_global_vars_in_str(param)
            return {"type": PipelineItemType.PY_FUNC.value, "param": param, "full_str": text}
        # Событие: SKIP, ROLLBACK, NOTIFY
        match = re.match(r'(?i)^(SKIP|ROLLBACK|NOTIFY)\((.*)\)$', text)
        if match:
            event_type = match.group(1).upper()
            param_text = match.group(2)
            return {"type": PipelineItemType.EVENT.value, "sub_type": event_type, "param": param_text, "full_str": text}
        # Прямое отображение или переменная — всегда подставляем значения глобальных и внешних переменных
        text_resolved = self.resolve_all_external_vars_in_str(text)
        text_resolved = self.resolve_all_global_vars_in_str(text_resolved)
        return {"type": PipelineItemType.DIRECT.value, "param": text_resolved, "full_str": text}
        # Логическое выражение
        return {"type": "cond_exp", "full_str": text} 

    def resolve_all_external_vars_in_str(self, s, node_context=None):
        """Заменяет все вхождения $$var.path в строке на их значения"""
        import json as _json
        def replacer(match):
            var_path = match.group(0)
            value = self.get_external_var_value(var_path, node_context=node_context)
            if isinstance(value, (dict, list)):
                return _json.dumps(value, ensure_ascii=False)
            return str(value)
        return re.sub(r'\$\$[a-zA-Z0-9_\.]+', replacer, s)

    def resolve_all_global_vars_in_str(self, s):
        """Заменяет все вхождения $var в строке на их значения из global_vars (кроме $this)"""
        import json as _json
        def replacer(match):
            var_name = match.group(1)
            if var_name == "this":
                return "$this"
            value = self.global_vars.get(var_name)
            if value is None:
                return "$" + var_name
            val = value.get("value") if isinstance(value, dict) and "value" in value else value
            if isinstance(val, (dict, list)):
                return _json.dumps(val, ensure_ascii=False)
            return str(val)
        # $var, но не $$var
        return re.sub(r'(?<!\$)\$([a-zA-Z_][a-zA-Z0-9_]*)', replacer, s) 