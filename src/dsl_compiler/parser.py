import sys
import re
from typing import List, Dict, Optional, Any, Tuple

from .errors import (DSLSyntaxError, UndefinedVarError, InvalidVarUsageError, 
                    SrcFieldAsVarError, PipelineClosingBarError, FlowDirectionError,
                    FinalTypeError, VoidTypeError, UnknownPipelineSegmentError,
                    ConditionMissingIfError, ConditionMissingParenthesisError,
                    ConditionEmptyExpressionError, ConditionMissingColonError,
                    ConditionInvalidError, FuncNotFoundError, ExternalVarWriteError,
                    GlobalVarWriteError)
from .ast_nodes import (
    ASTNode, ProgramNode, SourceNode, TargetNode, RouteBlockNode,
    FieldSrcNode, PipelineNode, FieldDstNode, RouteLineNode, PipelineItemNode, GlobalVarNode, FuncCallNode, DirectMapNode, ConditionNode, EventNode
)
from .constants import PipelineItemType, TokenType
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
        self._local_vars = {}  # Отслеживание локальных переменных: имя -> {тип, исходное_поле, определен}
        self._local_var_refs = {}  # Список всех ссылок на переменные: имя -> [маршруты]
        self._available_funcs = set()
    
    def parse(self, tokens=None):
        """Запускает процесс парсинга"""
        if tokens is not None:
            self.tokens = tokens
        
        self.position = 0
        self.ast = ProgramNode()
        self.ast.tokens = self.tokens  # Сохраняем все токены для генератора JSON
        
        # Хранилище для глобальных переменных, чтобы проверять дубликаты
        self._global_vars = {}
        
        pr(M.Debug.PARSING_START)
        
        # Для проверки дубликатов type/name
        type_name_keys = set()
        
        # Проходим по токенам
        while self.position < len(self.tokens):
            token = self.tokens[self.position]
            
            if token.type == TokenType.SOURCE:
                self.ast.children.append(SourceNode(token.value))
                self.position += 1
            elif token.type == TokenType.TARGET:
                target_node = TargetNode(
                    token.value['name'],
                    {"type": token.value['type'], "name": token.value['value']},
                    token.value['value']
                )
                # Проверка дубликата по type/name
                type_name_key = f"{token.value['type']}/{token.value['value']}"
                if type_name_key in type_name_keys:
                    from .errors import DSLSyntaxError
                    from .constants import ErrorType
                    from .localization import Messages
                    raise DSLSyntaxError(
                        ErrorType.DUPLICATE_TARGET_NAME_TYPE,
                        type_name_key,
                        token.position,
                        0,
                        self.loc.get(Messages.Hint.DUPLICATE_TARGET_NAME_TYPE),
                        target_name=token.value['value'],
                        target_type=type_name_key
                    )
                type_name_keys.add(type_name_key)
                self.ast.children.append(target_node)
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
            elif token.type == TokenType.GLOBAL_VAR_USAGE:
                var_name = token.value["var_name"]
                original_line = token.value["line"]
                line_num = token.position
                # Проверяем, определена ли глобальная переменная
                if var_name not in self._global_vars:
                    from .errors import UndefinedGlobalVarError
                    raise UndefinedGlobalVarError(
                        original_line,
                        line_num,
                        var_name,
                        original_line.find(f"${var_name}")
                    )
                # Если определена, добавляем специальный узел (или сохраняем для генерации JSON)
                # Здесь можно добавить в AST специальный узел или обработать позже в генераторе JSON
                # Пока просто пропускаем (или можно добавить в ast.children для генерации)
                self.position += 1
            elif token.type == TokenType.ROUTE_HEADER:
                target_name = token.value
                self.position += 1
                # Проверяем, что существует целевой объект для этого маршрута
                if not hasattr(self.ast, '_targets') or target_name not in self.ast._targets:
                    from .errors import DSLSyntaxError
                    from .constants import ErrorType
                    from .localization import Messages
                    raise DSLSyntaxError(
                        ErrorType.SEMANTIC_TARGET,
                        f"{target_name}:",
                        token.position,
                        0,
                        self.loc.get(Messages.Hint.TARGET_DEFINITION_MISSING, target=target_name)
                    )
                # Получаем все маршруты для этой цели
                routes = []
                final_names = set()
                while self.position < len(self.tokens) and self.tokens[self.position].type == TokenType.ROUTE_LINE:
                    route_line_token = self.tokens[self.position]
                    route_line = self._parse_route_line(route_line_token)
                    # Проверка на дублирование финальной цели (без учёта $)
                    if route_line.target_field and route_line.target_field.name:
                        norm_name = route_line.target_field.name.lstrip("$")
                        if norm_name in final_names:
                            from .errors import DSLSyntaxError
                            from .constants import ErrorType
                            from .localization import Messages
                            raise DSLSyntaxError(
                                ErrorType.DUPLICATE_FINAL_NAME,
                                route_line_token.value['line'],
                                route_line_token.position,
                                0,
                                None,
                                final_name=route_line.target_field.name
                            )
                        final_names.add(norm_name)
                    routes.append(route_line)
                    self.position += 1
                # Создаем блок маршрутов и добавляем в AST
                route_block = RouteBlockNode(target_name, routes)
                self.ast.children.append(route_block)
            else:
                # Пропускаем неизвестные токены
                self.position += 1
        
        pr(M.Debug.PARSING_FINISH)
        # Если нет ни одного блока маршрутов, выбрасываем SEMANTIC_ROUTES
        if not any(isinstance(child, RouteBlockNode) for child in self.ast.children):
            from .errors import DSLSyntaxError
            from .constants import ErrorType
            from .localization import Messages
            raise DSLSyntaxError(
                ErrorType.SEMANTIC_ROUTES,
                "(no routes)",
                0,
                0,
                self.loc.get(Messages.Hint.ROUTES_MISSING)
            )
        return self.ast
    
    def _parse_source(self) -> SourceNode:
        """Создает узел источника данных"""
        token = self.tokens[self.position]
        self.position += 1
        # Используем полное значение токена в качестве source_type
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
        route_info = token.value
        original_line = route_info['line']
        line_num = token.position
        src_field_name = route_info['src_field']
        pipeline_str = route_info['pipeline']
        target_field_name = route_info['target_field']
        target_field_type = route_info['target_field_type']
        
        # Проверяем наличие типа у пустого поля
        if target_field_name == "" and target_field_type:
            # Если у пустого поля указан тип - выдаем ошибку VOID_TYPE
            from .errors import VoidTypeError
            error = VoidTypeError(original_line, line_num)
            pr(str(error))
            sys.exit(1)
        
        # Запрет на запись во внешнюю переменную
        if target_field_name and target_field_name.startswith('$$'):
            from .errors import ExternalVarWriteError
            error = ExternalVarWriteError(original_line, line_num, target_field_name)
            pr(str(error))
            sys.exit(1)
        
        # Запрет на запись в глобальную переменную
        if (
            target_field_name
            and target_field_name.startswith('$')
            and hasattr(self.ast, '_global_vars')
            and target_field_name[1:] in self.ast._global_vars
        ):
            from .errors import GlobalVarWriteError
            error = GlobalVarWriteError(original_line, line_num, target_field_name)
            pr(str(error))
            sys.exit(1)
        
        # Проверяем наличие типа целевого поля (если поле не пустое)
        if target_field_name and not target_field_type:
            # Находим позицию для сообщения об ошибке - после последней скобки
            target_field_pos = original_line.rfind(']')
            if target_field_pos != -1:
                # Генерируем ошибку отсутствия типа
                error = FinalTypeError(original_line, line_num, target_field_pos + 1)
                pr(str(error))
                sys.exit(1)
        
        # Создаем узел для исходного поля
        src_field = FieldSrcNode(src_field_name)
        # Сохраняем информацию о позиции
        src_field_pos = original_line.find('[' + src_field_name + ']')
        src_field.set_position_info(original_line, line_num, src_field_pos)
        
        # Создаем узел для целевого поля, если оно указано
        if target_field_name == "":
            target_field = FieldDstNode("", None)
        elif target_field_name:
            target_field = FieldDstNode(target_field_name, target_field_type)
            # Сохраняем информацию о позиции
            target_field_pos = original_line.rfind('[' + target_field_name + ']')
            target_field.set_position_info(original_line, line_num, target_field_pos)
            
            # Регистрируем локальную переменную
            if target_field_name.startswith('$'):
                # Переменная явно определена с $
                var_name = target_field_name[1:]  # Убираем $ в начале
                self._local_vars[var_name] = {
                    'type': target_field_type,
                    'src_field': src_field_name,
                    'defined': True
                }
                
                # Проверяем, не используется ли эта переменная в пайплайне текущего маршрута
                if pipeline_str and f'${var_name}' in pipeline_str:
                    error = InvalidVarUsageError(original_line, line_num, var_name, pipeline_str.find(f'${var_name}'))
                    pr(str(error))
                    sys.exit(1)
            else:
                # Создаем неявную переменную для каждого поля в правой части
                # Это позволяет ссылаться на поле как $имя_поля
                self._local_vars[target_field_name] = {
                    'type': target_field_type,
                    'src_field': src_field_name,
                    'defined': True
                }
        else:
            target_field = None
        
        # Создаем узел для конвейера
        pipeline = PipelineNode()
        # Сохраняем информацию о позиции
        if pipeline_str:
            pipeline_pos = original_line.find('|')
            pipeline.set_position_info(original_line, line_num, pipeline_pos)
            
            segments = [seg.strip() for seg in pipeline_str.strip('|').split('|') if seg.strip()]
            items = []
            for seg in segments:
                items.extend(self._parse_pipeline_items(seg, original_line, line_num))
            pipeline.items = items
        
        # Создаем узел строки маршрута и связываем все компоненты
        route_line = RouteLineNode(src_field, pipeline, target_field)
        # Сохраняем информацию о позиции для всей строки
        route_line.set_position_info(original_line, line_num, 0)
        
        return route_line
    
    def _parse_pipeline(self, pipeline_str: str, src_field: str, original_line: str, line_num: int) -> PipelineNode:
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
                    func_name = segment[1:]
                    params = []
                    if '(' in func_name and func_name.endswith(')'):
                        param_start = func_name.find('(')
                        param_end = func_name.rfind(')')
                        param_str = func_name[param_start+1:param_end].strip()
                        arg_list = self._split_args(param_str)
                        checked_params = [p.strip() if p.strip() != f"${src_field}" else "$this" for p in arg_list]
                        params = checked_params
                        func_name = func_name[:param_start]
                    else:
                        params = []
                    checked_params = []
                    for param in params if params else ["$this"]:
                        param = param.strip()
                        # Если аргумент совпадает с текущим src_field, подставляем $this
                        if param == f"${src_field}":
                            param = "$this"
                        if param.startswith('$^'):
                            var_name = param[2:]
                            if var_name != 'this' and not var_name:
                                error = UndefinedVarError(original_line, line_num, 'пустое имя', pipeline_str.find('$^'))
                                pr(str(error))
                                sys.exit(1)
                        elif param.startswith('$$'):
                            pass
                        elif param.startswith('$'):
                            var_name = param[1:]
                            if not var_name:
                                error = UndefinedVarError(original_line, line_num, 'пустое имя', pipeline_str.find('$'))
                                pr(str(error))
                                sys.exit(1)
                            if var_name != 'this':
                                src_fields = []
                                for token in self.tokens:
                                    if token.type == TokenType.ROUTE_LINE:
                                        src_fields.append(token.value.get('src_field', ''))
                                if var_name in src_fields and var_name not in self._local_vars:
                                    error = SrcFieldAsVarError(original_line, line_num, var_name, pipeline_str.find('$' + var_name))
                                    pr(str(error))
                                    sys.exit(1)
                                is_global_var = False
                                if hasattr(self.ast, '_global_vars') and var_name in self.ast._global_vars:
                                    is_global_var = True
                                if not is_global_var and var_name not in self._local_vars:
                                    error = UndefinedVarError(original_line, line_num, var_name, pipeline_str.find('$' + var_name))
                                    pr(str(error))
                                    sys.exit(1)
                                elif not is_global_var and var_name in self._local_vars and self._local_vars[var_name]['src_field'] == src_field:
                                    error = InvalidVarUsageError(original_line, line_num, var_name, pipeline_str.find('$' + var_name))
                                    pr(str(error))
                                    sys.exit(1)
                            if var_name != 'this':
                                if var_name not in self._local_var_refs:
                                    self._local_var_refs[var_name] = []
                                self._local_var_refs[var_name].append({
                                    'src_field': src_field,
                                    'line': line_num,
                                    'context': segment
                                })
                        checked_params.append(param)
                    param_value = checked_params[0] if len(checked_params) == 1 else checked_params
                    if self._available_funcs and func_name not in self._available_funcs:
                        error = FuncNotFoundError(original_line, line_num, func_name, original_line.find(f"*{func_name}"), func_folder=getattr(self, '_func_folder', None))
                        pr(str(error))
                        sys.exit(1)
                    pipeline.items.append(PipelineItemNode(
                        PipelineItemType.PY_FUNC,
                        func_name,
                        params={"param": param_value}
                    ))
                    pr(M.Debug.PIPELINE_ITEM_ADDED, type=PipelineItemType.PY_FUNC.value, value=segment)
                elif segment.lower().startswith('if'):
                    # Условный оператор - анализируем его содержимое на переменные
                    self._check_condition_vars(segment, src_field, original_line, line_num)
                    
                    pipeline.items.append(PipelineItemNode(
                        PipelineItemType.CONDITION,
                        segment
                    ))
                    pr(M.Debug.PIPELINE_ITEM_ADDED, type=PipelineItemType.CONDITION.value, value=segment)
                else:
                    # Неизвестный тип сегмента - ошибка
                    error = UnknownPipelineSegmentError(original_line, line_num, segment, original_line.find(segment))
                    pr(str(error))
                    sys.exit(1)
        
        return pipeline

    def _check_condition_vars(self, condition: str, src_field: str, original_line: str, line_num: int):
        """Проверяет переменные в условном выражении"""
        # Находим все переменные в условии
        var_matches = re.finditer(r'\$(\^?)?\s*([a-zA-Z][a-zA-Z0-9_]*)', condition)
        
        for match in var_matches:
            # Пропускаем внешние переменные ($$...)
            if (match.start() > 0 and condition[match.start()-1] == '$') or condition[match.start():].startswith('$$'):
                continue
            is_pre_var = match.group(1) == '^'
            var_name = match.group(2)
            
            # Для $this не нужна проверка, это текущее значение поля
            if var_name == 'this':
                continue
                
            if is_pre_var:
                # Для $^var проверяем, существует ли она как поле или переменная
                if var_name not in self._local_vars and var_name != src_field:
                    error = UndefinedVarError(original_line, line_num, var_name, original_line.find('$^' + var_name))
                    pr(str(error))
                    sys.exit(1)
            else:
                # Проверяем, не является ли это попыткой использовать имя поля из левой части
                src_fields = []
                for token in self.tokens:
                    if token.type == TokenType.ROUTE_LINE:
                        src_fields.append(token.value.get('src_field', ''))
                
                # Если имя поля есть в левой части других маршрутов, но не определено как переменная
                if var_name in src_fields and var_name not in self._local_vars:
                    # Это попытка обратиться к левой части - специальная ошибка
                    error = SrcFieldAsVarError(original_line, line_num, var_name, original_line.find('$' + var_name))
                    pr(str(error))
                    sys.exit(1)
                
                # Проверяем наличие в глобальных переменных
                is_global_var = False
                if hasattr(self.ast, '_global_vars') and var_name in self.ast._global_vars:
                    is_global_var = True
                
                if not is_global_var and var_name not in self._local_vars:
                    # Переменная не определена вообще
                    error = UndefinedVarError(original_line, line_num, var_name, original_line.find('$' + var_name))
                    pr(str(error))
                    sys.exit(1)
                
                # Проверяем правильность использования
                # В пайплайне нельзя использовать переменные, которые определяются далее
                if not is_global_var and var_name in self._local_vars and self._local_vars[var_name]['src_field'] == src_field:
                    error = InvalidVarUsageError(original_line, line_num, var_name, original_line.find('$' + var_name))
                    pr(str(error))
                    sys.exit(1)
                    
            # Регистрируем использование переменной
            if var_name not in self._local_var_refs:
                self._local_var_refs[var_name] = []
            self._local_var_refs[var_name].append({
                'src_field': src_field,
                'line': line_num,
                'context': condition
            })

    def _parse_pipeline_items(self, pipeline_str: str, original_line: str, line_num: int):
        """Парсит элементы конвейера обработки и сохраняет информацию о позиции"""
        if not pipeline_str:
            return []
        
        # Убираем обрамляющие вертикальные черты
        inner_content = pipeline_str.strip('|').strip()
        
        # Находим позицию начала содержимого пайплайна в исходной строке
        pipeline_start_pos = original_line.find('|') + 1
        
        # Извлекаем имя исходного поля из строки для более подробного предупреждения
        src_field_name = ""
        bracket_start = original_line.find('[')
        bracket_end = original_line.find(']')
        if bracket_start != -1 and bracket_end != -1 and bracket_start < bracket_end:
            src_field_name = original_line[bracket_start+1:bracket_end]
        
        # Проверяем, есть ли в пайплайне неопределенные переменные
        var_pattern = r'\$(\^)?([a-zA-Z][a-zA-Z0-9_]*)'
        items = []
        for match in re.finditer(var_pattern, pipeline_str):
            # Пропускаем внешние переменные ($$...)
            if (match.start() > 0 and pipeline_str[match.start()-1] == '$') or pipeline_str[match.start():].startswith('$$'):
                continue
            is_pre_var = match.group(1) == '^'
            var_name = match.group(2)
            
            # Пропускаем $this и $^this
            if var_name == 'this':
                continue
                
            if is_pre_var:
                # Переменные с префиксом $^ - проверка только на существование поля в левой части
                # Не требуют дополнительной проверки, так как могут ссылаться на поля источника
                continue
                
            # Проверяем, не является ли это попыткой использовать имя поля из левой части
            # 1. Совпадает ли имя переменной с именем поля в левой части текущего маршрута
            if var_name == src_field_name:
                # Это обращение к текущему значению поля — трактуем как $this
                continue
                
            # 2. Собираем имена всех полей из левой части всех маршрутов, кроме текущего
            src_fields = []
            for token in self.tokens:
                if token.type == TokenType.ROUTE_LINE:
                    field_name = token.value.get('src_field', '')
                    if field_name and field_name != src_field_name and field_name not in src_fields:
                        src_fields.append(field_name)
            
            # 3. Проверяем, есть ли имя в списке полей левой части, но не определено как переменная
            if var_name in src_fields and var_name not in self._local_vars:
                error = SrcFieldAsVarError(original_line, line_num, var_name, pipeline_str.find('$' + var_name))
                pr(str(error))
                sys.exit(1)
                
            # Проверяем наличие в глобальных переменных
            is_global_var = False
            if hasattr(self.ast, '_global_vars') and var_name in self.ast._global_vars:
                is_global_var = True
                
            # Проверяем наличие локальной переменной
            if not is_global_var and var_name not in self._local_vars:
                # Переменная не определена
                error = UndefinedVarError(original_line, line_num, var_name, pipeline_str.find('$' + var_name))
                pr(str(error))
                sys.exit(1)
        
        # Если строка пустая, возвращаем пустой список
        if not inner_content:
            return items
        
        # Определяем тип узла на основе содержимого и создаем соответствующий узел
        if inner_content.lower().startswith(('if', 'elif', 'else')):
            # Обрабатываем условные выражения с проверкой ошибок
            try:
                node = self._parse_conditional_expression(inner_content, original_line, line_num, pipeline_start_pos, src_field_name)
                items.append(node)
                return items
            except DSLSyntaxError as e:
                # Обработка и вывод ошибки, затем прерывание выполнения
                pr(str(e))
                sys.exit(1)
        if inner_content.startswith('*'):
            func_text = inner_content[1:]
            param_value = "$this"
            if '(' in func_text and func_text.endswith(')'):
                idx = func_text.find('(')
                func_name = func_text[:idx]
                param_text = func_text[idx+1:-1].strip()
                arg_list = self._split_args(param_text)
                checked_params = [p.strip() if p.strip() != f"${src_field_name}" else "$this" for p in arg_list]
                param_value = checked_params[0] if len(checked_params) == 1 else checked_params
            else:
                func_name = func_text
                param_value = "$this"
            if self._available_funcs and func_name not in self._available_funcs:
                error = FuncNotFoundError(original_line, line_num, func_name, original_line.find(f"*{func_name}"), func_folder=getattr(self, '_func_folder', None))
                pr(str(error))
                sys.exit(1)
            node = FuncCallNode(
                value=inner_content,
                params={"param": param_value}
            )
            node_pos = pipeline_start_pos + inner_content.find('*')
            node.set_position_info(original_line, line_num, node_pos)
            items.append(node)
        elif inner_content == '$this':
            # Прямое отображение значения
            node = DirectMapNode(
                value=inner_content,
                params={"param": "$this", "is_external_var": False}
            )
            # Сохраняем информацию о позиции
            node_pos = pipeline_start_pos
            node.set_position_info(original_line, line_num, node_pos)
            items.append(node)
        elif inner_content.startswith('$$'):
            # Прямое отображение внешней переменной
            node = DirectMapNode(
                value=inner_content,
                params={"param": inner_content, "is_external_var": True}
            )
            # Сохраняем информацию о позиции
            node_pos = pipeline_start_pos
            node.set_position_info(original_line, line_num, node_pos)
            items.append(node)
        elif re.match(r'(?i)^(SKIP|ROLLBACK|NOTIFY)\(', inner_content):
            # Событие в пайплайне
            match = re.match(r'(?i)^(SKIP|ROLLBACK|NOTIFY)\((.*)\)$', inner_content)
            if match:
                event_name = match.group(1).upper()
                param_text = match.group(2)
            else:
                event_name = inner_content
                param_text = ""
            node = EventNode(
                value=inner_content,
                params={"sub_type": event_name, "param": param_text}
            )
            # Сохраняем позицию события
            event_pos = pipeline_start_pos + inner_content.lower().find(event_name.lower())
            node.set_position_info(original_line, line_num, event_pos)
            items.append(node)
        else:
            # Неизвестный тип, используем прямое отображение по умолчанию
            node = DirectMapNode(
                value=inner_content,
                params={"param": inner_content, "is_external_var": False}
            )
            # Проверяем, похоже ли это на забытую звездочку перед функцией
            # Условия: не начинается с $$, не является $this, не содержит пробелов
            if (not inner_content.startswith('$$') and inner_content != '$this' and 
                ' ' not in inner_content and inner_content.isalnum()):
                # Выводим предупреждение - возможно забыта звездочка
                pr(M.Warning.DIRECT_MAPPING_WITHOUT_STAR, 
                   value=inner_content, 
                   src=src_field_name,
                   color="yellow")
            # Сохраняем информацию о позиции
            node_pos = pipeline_start_pos
            node.set_position_info(original_line, line_num, node_pos)
            items.append(node)
        return items
        
    def _parse_conditional_expression(self, content: str, original_line: str, line_num: int, pipeline_start_pos: int, src_field_name: str):
        """
        Строго парсит условное выражение IF/ELIF/ELSE с проверкой синтаксиса для каждой ветки
        """
        import re
        # === СТАРЫЕ ПРОВЕРКИ ДЛЯ BACKWARD COMPATIBILITY ===
        content_strip = content.strip()
        # ELSE без IF
        if content_strip.lower().startswith('else') and not content_strip.lower().startswith('else:'):
            pos = pipeline_start_pos + content_strip.lower().find('else')
            raise ConditionMissingIfError(original_line, line_num, pos)
        # IF без скобок
        if content_strip.lower().startswith('if'):
            after_if = content_strip[2:].lstrip()
            if not after_if.startswith('('):
                pos = pipeline_start_pos + content_strip.lower().find('if') + 2
                raise ConditionMissingParenthesisError(original_line, line_num, pos)
        # ELIF без скобок (например, ELIFtrue)
        m_elif_no_paren = re.search(r"(?i)\bELIF(?=\w)", content)
        if m_elif_no_paren:
            pos = pipeline_start_pos + m_elif_no_paren.start()
            raise ConditionMissingParenthesisError(original_line, line_num, pos)
        # === СТРОГИЙ РАЗБОР ВСЕХ ВЕТОК ===
        pattern = re.compile(r"(?i)\b(IF|ELIF|ELSE)\b")
        matches = list(pattern.finditer(content))
        if not matches:
            from .localization import Messages
            raise ConditionInvalidError(
                original_line,
                line_num,
                None,  # Использовать стандартное сообщение
                pipeline_start_pos
            )

        for idx, m in enumerate(matches):
            key = m.group(1).upper()
            start = m.start()
            end = matches[idx+1].start() if idx+1 < len(matches) else len(content)
            branch = content[start:end].strip()
            rel_pos = pipeline_start_pos + start

            if key in ("IF", "ELIF"):
                # Проверка скобок
                open_paren = branch.find("(")
                close_paren = branch.find(")", open_paren)
                if open_paren == -1 or close_paren == -1:
                    raise ConditionMissingParenthesisError(original_line, line_num, rel_pos + (open_paren if open_paren != -1 else 0))
                exp_content = branch[open_paren+1:close_paren].strip()
                if not exp_content:
                    raise ConditionEmptyExpressionError(original_line, line_num, rel_pos + open_paren + 1)
                # Проверка двоеточия
                after_paren = branch[close_paren+1:].lstrip()
                if not after_paren.startswith(":"):
                    raise ConditionMissingColonError(original_line, line_num, rel_pos + close_paren + 1)
                # Проверка действия
                colon_pos = branch.find(":", close_paren)
                do_content = branch[colon_pos+1:].strip()
                if not do_content:
                    from .localization import Messages
                    raise ConditionInvalidError(
                        original_line,
                        line_num,
                        None,  # Использовать стандартное сообщение
                        rel_pos + colon_pos + 1,
                        key=key
                    )
                # Проверка переменных
                if "$" in exp_content:
                    self._check_condition_vars(exp_content, src_field_name, original_line, line_num)
                if "$" in do_content:
                    self._check_condition_vars(do_content, src_field_name, original_line, line_num)
                # === Теперь ищем все вызовы *func только если синтаксис валиден ===
                for func_match in re.finditer(r"\*([a-zA-Z_][a-zA-Z0-9_]*)\s*(\(|\||$)", branch):
                    func_name = func_match.group(1)
                    if self._available_funcs and func_name not in self._available_funcs:
                        pos = rel_pos + func_match.start()
                        error = FuncNotFoundError(original_line, line_num, func_name, pos, func_folder=getattr(self, '_func_folder', None))
                        pr(str(error))
                        sys.exit(1)
            elif key == "ELSE":
                after_else = branch[4:].lstrip()
                if not after_else.startswith(":"):
                    raise ConditionMissingColonError(original_line, line_num, rel_pos + 4)
                do_content = after_else[1:].strip()
                if not do_content:
                    from .localization import Messages
                    raise ConditionInvalidError(
                        original_line,
                        line_num,
                        None,  # Использовать стандартное сообщение
                        rel_pos + 5,
                        key=key
                    )
                if "$" in do_content:
                    self._check_condition_vars(do_content, src_field_name, original_line, line_num)
                # === Теперь ищем все вызовы *func только если синтаксис валиден ===
                for func_match in re.finditer(r"\*([a-zA-Z_][a-zA-Z0-9_]*)\s*(\(|\||$)", branch):
                    func_name = func_match.group(1)
                    if self._available_funcs and func_name not in self._available_funcs:
                        pos = rel_pos + func_match.start()
                        error = FuncNotFoundError(original_line, line_num, func_name, pos, func_folder=getattr(self, '_func_folder', None))
                        pr(str(error))
                        sys.exit(1)
            else:
                from .localization import Messages
                raise ConditionInvalidError(
                    original_line,
                    line_num,
                    None,  # Использовать стандартное сообщение
                    rel_pos
                )

        node = ConditionNode(
            value=content,
            params={}
        )
        node.set_position_info(original_line, line_num, pipeline_start_pos)
        return node

    def _parse_route_block(self) -> RouteBlockNode:
        """Разбор блока маршрутов для одной цели с проверкой дублирования финальных целей"""
        token = self.tokens[self.position]
        target_name = token.value['name']
        self.position += 1
        routes = []
        final_names = set()
        while self.position < len(self.tokens) and self.tokens[self.position].type == TokenType.ROUTE_LINE:
            route_line_token = self.tokens[self.position]
            route_line = self._parse_route_line(route_line_token)
            # Проверка на дублирование финальной цели (без учёта $)
            if route_line.target_field and route_line.target_field.name:
                norm_name = route_line.target_field.name.lstrip("$")
                if norm_name in final_names:
                    from .errors import DSLSyntaxError
                    from .constants import ErrorType
                    from .localization import Messages
                    raise DSLSyntaxError(
                        ErrorType.DUPLICATE_FINAL_NAME,
                        route_line_token.value['line'],
                        route_line_token.position,
                        0,
                        None,
                        final_name=route_line.target_field.name
                    )
                final_names.add(norm_name)
            routes.append(route_line)
            self.position += 1
        route_block = RouteBlockNode(target_name, routes)
        self.ast.children.append(route_block)
        return route_block

    def set_available_funcs(self, funcs: set, func_folder: str = None):
        """Устанавливает список доступных функций для проверки и путь к папке функций."""
        self._available_funcs = set(funcs)
        self._func_folder = func_folder

    def _split_args(self, s):
        args = []
        buf = ''
        depth = 0
        in_str = False
        str_char = ''
        i = 0
        while i < len(s):
            c = s[i]
            if in_str:
                buf += c
                if c == str_char:
                    in_str = False
                elif c == '\\':
                    if i+1 < len(s):
                        buf += s[i+1]
                        i += 1
            elif c in ('"', "'"):
                in_str = True
                str_char = c
                buf += c
            elif c == '(': 
                depth += 1
                buf += c
            elif c == ')':
                depth -= 1
                buf += c
            elif c == ',' and depth == 0:
                args.append(buf.strip())
                buf = ''
            else:
                buf += c
            i += 1
        if buf.strip():
            args.append(buf.strip())
        return args


# Импортируем TokenType в конце файла, чтобы избежать циклических зависимостей
from .constants import NodeType 