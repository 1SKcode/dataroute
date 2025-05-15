import sys
import re
from typing import List, Dict, Optional, Any, Tuple

from .errors import (DSLSyntaxError, UndefinedVarError, InvalidVarUsageError, 
                    SrcFieldAsVarError, PipelineClosingBarError, FlowDirectionError,
                    FinalTypeError, VoidTypeError, UnknownPipelineSegmentError,
                    ConditionMissingIfError, ConditionMissingParenthesisError,
                    ConditionEmptyExpressionError, ConditionMissingColonError,
                    ConditionInvalidError)
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
                    {"type": token.value['type'], "name": token.value['value']},
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
        target_field = None
        if target_field_name:
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
        
        # Создаем узел для конвейера
        pipeline = PipelineNode()
        # Сохраняем информацию о позиции
        if pipeline_str:
            pipeline_pos = original_line.find('|')
            pipeline.set_position_info(original_line, line_num, pipeline_pos)
            
            # Обрабатываем элементы конвейера
            items = self._parse_pipeline_items(pipeline_str, original_line, line_num)
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
                            # Пре-переменная - проверяем, существует ли она
                            is_pre_var = True
                            param = param_str
                            var_name = param_str[2:]  # Убираем '$^'
                            
                            # Проверяем, что имя переменной указано и существует как поле
                            if var_name != 'this' and not var_name:
                                error = UndefinedVarError(original_line, line_num, 'пустое имя', pipeline_str.find('$^'))
                                pr(str(error))
                                sys.exit(1)
                            
                            # Для $^this не нужна проверка, это текущее значение поля
                            # Для полей с префиксом $^ не нужно проверять, существует ли переменная,
                            # они используются для доступа к исходным полям
                            # Убираем эту проверку, так как она приводит к ошибке
                            # if var_name != 'this':
                            #     # Если это не $^this, и нет такой локальной переменной, проверяем как исходное поле
                            #     if var_name not in self._local_vars and var_name != src_field:
                            #         from .errors import UndefinedVarError
                            #         error = UndefinedVarError(original_line, line_num, var_name, pipeline_str.find('$^' + var_name))
                            #         pr(str(error))
                            #         sys.exit(1)
                        elif param_str.startswith('$$'):
                            # Внешняя переменная
                            param = param_str
                            is_external_var = True
                            # Обработка внешних переменных выполняется в json_generator
                        elif param_str.startswith('$'):
                            # Обычная переменная - проверяем существование
                            param = param_str
                            var_name = param_str[1:]  # Убираем '$'
                            
                            # Проверяем, что имя переменной указано
                            if not var_name:
                                error = UndefinedVarError(original_line, line_num, 'пустое имя', pipeline_str.find('$'))
                                pr(str(error))
                                sys.exit(1)
                            
                            # Для $this не нужна проверка, это текущее значение
                            if var_name != 'this':
                                # Проверяем:
                                # 1. Переменная определена глобально
                                # 2. Переменная определена в предыдущих маршрутах
                                # 3. Проверка на то, что это не поле из левой части
                                
                                # Проверяем, не является ли это попыткой использовать имя поля из левой части
                                src_fields = []
                                for token in self.tokens:
                                    if token.type == TokenType.ROUTE_LINE:
                                        src_fields.append(token.value.get('src_field', ''))
                                
                                # Если имя поля есть в левой части других маршрутов, но не определено как переменная
                                if var_name in src_fields and var_name not in self._local_vars:
                                    # Это попытка обратиться к левой части - специальная ошибка
                                    error = SrcFieldAsVarError(original_line, line_num, var_name, pipeline_str.find('$' + var_name))
                                    pr(str(error))
                                    sys.exit(1)
                                
                                # Проверяем наличие в глобальных переменных
                                is_global_var = False
                                if hasattr(self.ast, '_global_vars') and var_name in self.ast._global_vars:
                                    is_global_var = True
                                
                                if not is_global_var and var_name not in self._local_vars:
                                    # Переменная не определена вообще
                                    error = UndefinedVarError(original_line, line_num, var_name, pipeline_str.find('$' + var_name))
                                    pr(str(error))
                                    sys.exit(1)
                                    
                                elif not is_global_var and var_name in self._local_vars and self._local_vars[var_name]['src_field'] == src_field:
                                    # Переменная определена в этом же маршруте, нельзя использовать
                                    error = InvalidVarUsageError(original_line, line_num, var_name, pipeline_str.find('$' + var_name))
                                    pr(str(error))
                                    sys.exit(1)
                                    
                            # Регистрируем использование переменной
                            if var_name != 'this':
                                if var_name not in self._local_var_refs:
                                    self._local_var_refs[var_name] = []
                                self._local_var_refs[var_name].append({
                                    'src_field': src_field,
                                    'line': line_num,
                                    'context': segment
                                })
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
        for match in re.finditer(var_pattern, pipeline_str):
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
                error = SrcFieldAsVarError(original_line, line_num, var_name, pipeline_str.find('$' + var_name))
                pr(str(error))
                sys.exit(1)
                
            # 2. Собираем имена всех полей из левой части всех маршрутов
            src_fields = []
            for token in self.tokens:
                if token.type == TokenType.ROUTE_LINE:
                    field_name = token.value.get('src_field', '')
                    if field_name and field_name not in src_fields:
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
        
        items = []
        # Если строка пустая, возвращаем пустой список
        if not inner_content:
            return items
            
        # Проверяем на условные выражения
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
        
        # Определяем тип узла на основе содержимого и создаем соответствующий узел
        if inner_content.startswith('*'):
            # Функция Python
            func_text = inner_content[1:]  # Убираем * в начале
            
            # Проверяем, есть ли параметры
            param_value = "$this"  # Значение по умолчанию
            is_external_var = False
            if '(' in func_text and func_text.endswith(')'):
                # Есть параметры
                param_start = func_text.find('(')
                param_end = func_text.rfind(')')
                func_name = func_text[:param_start]
                param_text = func_text[param_start+1:param_end].strip()
                
                # Проверяем специальные типы параметров
                if param_text.startswith('$$'):
                    # Внешняя переменная
                    param_value = param_text
                    is_external_var = True
                elif param_text.startswith('$^'):
                    # Пре-переменная
                    param_value = param_text
                elif param_text.startswith('$'):
                    # Локальная переменная
                    param_value = param_text
                else:
                    # Обычный параметр
                    param_value = param_text
            else:
                func_name = func_text
            
            # Создаем узел для функции
            node = FuncCallNode(
                value=inner_content,
                params={"param": param_value, "is_external_var": is_external_var}
            )
            
            # Сохраняем информацию о позиции
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
        Парсит условное выражение с проверкой синтаксиса
        
        Args:
            content: Содержимое условного выражения
            original_line: Исходная строка для сообщений об ошибках
            line_num: Номер строки для сообщений об ошибках
            pipeline_start_pos: Позиция начала пайплайна в строке
            src_field_name: Имя исходного поля для проверки переменных
            
        Raises:
            DSLSyntaxError: При обнаружении синтаксических ошибок
        """
        # Проверка на наличие ELSE без IF
        if content.lower().startswith('else') and not content.lower().startswith('else:'):
            pos = pipeline_start_pos + content.lower().find('else')
            raise ConditionMissingIfError(original_line, line_num, pos)
        elif content.lower().startswith('else:'):
            pos = pipeline_start_pos + content.lower().find('else')
            raise ConditionMissingIfError(original_line, line_num, pos)
            
        # Если выражение начинается с IF
        if content.lower().startswith('if'):
            # Проверяем наличие скобок
            if '(' not in content or ')' not in content:
                pos = pipeline_start_pos + len('if')
                raise ConditionMissingParenthesisError(original_line, line_num, pos)
                
            # Проверяем, что скобки идут после IF и перед ними нет других символов
            if_end_pos = len('if')
            if not content[if_end_pos:].lstrip().startswith('('):
                pos = pipeline_start_pos + if_end_pos
                raise ConditionMissingParenthesisError(original_line, line_num, pos)
                
            # Находим открывающую и закрывающую скобки
            open_paren_pos = content.find('(')
            close_paren_pos = content.find(')', open_paren_pos)
            
            if close_paren_pos == -1:
                # Нет закрывающей скобки
                pos = pipeline_start_pos + open_paren_pos
                raise ConditionMissingParenthesisError(original_line, line_num, pos)
                
            # Проверяем, что внутри скобок есть содержимое
            exp_content = content[open_paren_pos+1:close_paren_pos].strip()
            if not exp_content:
                pos = pipeline_start_pos + open_paren_pos + 1
                raise ConditionEmptyExpressionError(original_line, line_num, pos)
                
            # Проверяем наличие двоеточия после условия
            if not content[close_paren_pos+1:].lstrip().startswith(':'):
                pos = pipeline_start_pos + close_paren_pos + 1
                raise ConditionMissingColonError(original_line, line_num, pos)
                
            # Проверяем, что после двоеточия есть содержимое
            colon_pos = content.find(':', close_paren_pos)
            if_block_content = content[colon_pos+1:].strip()
            
            # Находим ELSE или ELIF, если они есть
            else_pos = -1
            elif_pos = -1
            
            # Ищем ELSE или ELIF за пределами строк и комментариев
            in_string = False
            string_char = None
            escape_next = False
            
            for i in range(colon_pos + 1, len(content)):
                c = content[i]
                
                # Обработка строковых литералов
                if not escape_next and c in ('"', "'"):
                    if not in_string:
                        in_string = True
                        string_char = c
                    elif c == string_char:
                        in_string = False
                elif c == '\\' and in_string:
                    escape_next = True
                    continue
                    
                # Если мы не в строке, ищем ELSE или ELIF
                if not in_string:
                    if content[i:i+4].lower() == 'else' and (i == 0 or not content[i-1].isalnum()):
                        else_pos = i
                        break
                    elif content[i:i+4].lower() == 'elif' and (i == 0 or not content[i-1].isalnum()):
                        elif_pos = i
                        break
                        
                escape_next = False

            # Проверка переменных в условном выражении IF
            if '$' in exp_content:
                self._check_condition_vars(exp_content, src_field_name, original_line, line_num)
            
            # Проверяем корректность ELSE
            if else_pos != -1:
                rest_after_else = content[else_pos+4:].lstrip()
                if not rest_after_else.startswith(':'):
                    pos = pipeline_start_pos + else_pos + 4
                    raise ConditionMissingColonError(original_line, line_num, pos)
                    
                else_content = rest_after_else[1:].strip()
                if not else_content:
                    pos = pipeline_start_pos + else_pos + 4 + len(rest_after_else[:rest_after_else.find(':')+1])
                    raise ConditionInvalidError(original_line, line_num, 
                                               "После ELSE: должно быть указано действие", pos)
                                               
                # Проверка переменных в блоке ELSE
                if '$' in else_content:
                    self._check_condition_vars(else_content, src_field_name, original_line, line_num)
            
            # Проверяем корректность ELIF (аналогично проверке IF)
            if elif_pos != -1:
                rest_after_elif = content[elif_pos+4:].lstrip()
                if not rest_after_elif.startswith('('):
                    pos = pipeline_start_pos + elif_pos + 4
                    raise ConditionMissingParenthesisError(original_line, line_num, pos)
                    
                # Находим скобки ELIF
                elif_open_paren = content.find('(', elif_pos)
                elif_close_paren = content.find(')', elif_open_paren)
                
                if elif_close_paren == -1:
                    pos = pipeline_start_pos + elif_open_paren
                    raise ConditionMissingParenthesisError(original_line, line_num, pos)
                    
                # Проверяем содержимое скобок
                elif_exp_content = content[elif_open_paren+1:elif_close_paren].strip()
                if not elif_exp_content:
                    pos = pipeline_start_pos + elif_open_paren + 1
                    raise ConditionEmptyExpressionError(original_line, line_num, pos)
                    
                # Проверка переменных в условном выражении ELIF
                if '$' in elif_exp_content:
                    self._check_condition_vars(elif_exp_content, src_field_name, original_line, line_num)
                    
                # Проверяем двоеточие после ELIF
                rest_after_elif_exp = content[elif_close_paren+1:].lstrip()
                if not rest_after_elif_exp.startswith(':'):
                    pos = pipeline_start_pos + elif_close_paren + 1
                    raise ConditionMissingColonError(original_line, line_num, pos)
                    
                # Проверяем содержимое блока ELIF
                elif_colon_pos = content.find(':', elif_close_paren)
                elif_block_content = content[elif_colon_pos+1:else_pos if else_pos != -1 else None].strip()
                if not elif_block_content:
                    pos = pipeline_start_pos + elif_colon_pos + 1
                    raise ConditionInvalidError(original_line, line_num, 
                                               "После ELIF: должно быть указано действие", pos)
                                               
                # Проверка переменных в блоке ELIF после двоеточия
                if '$' in elif_block_content:
                    self._check_condition_vars(elif_block_content, src_field_name, original_line, line_num)
            
            # Создаем узел для условного выражения
            node = ConditionNode(
                value=content,
                params={}
            )
            
            # Сохраняем информацию о позиции
            node_pos = pipeline_start_pos
            node.set_position_info(original_line, line_num, node_pos)
            
            return node
        
        # Если выражение начинается не с известных ключевых слов
        raise ConditionInvalidError(original_line, line_num, 
                                   "Неизвестная конструкция условного выражения", 
                                   pipeline_start_pos)

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


# Импортируем TokenType в конце файла, чтобы избежать циклических зависимостей
from .constants import NodeType 