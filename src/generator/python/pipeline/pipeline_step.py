from typing import Dict, Any, Optional, Callable, List, Union
from enum import Enum
import importlib
import inspect
import re
import os
import sys
import importlib.util


class StepType(Enum):
    """Типы шагов пайплайна"""
    PYTHON_FUNCTION = "py_func"
    CONDITION = "condition"
    EVENT = "event"
    UNKNOWN = "unknown"


class ConditionType(Enum):
    """Типы условий"""
    IF = "if"
    IF_ELSE = "if_else"
    IF_ELIFS_ELSE = "if_elifs_else"


class EventType(Enum):
    """Типы событий"""
    NOTIFY = "NOTIFY"
    SKIP = "SKIP"
    ROLLBACK = "ROLLBACK"


class PipelineStep:
    """Представляет шаг пайплайна для обработки данных"""

    def __init__(
        self,
        step_data: Dict[str, Any],
        step_number: int,
        std_functions_path: str,
        user_functions_path: Optional[str] = None
    ):
        """
        Инициализирует шаг пайплайна.

        Args:
            step_data: Данные о шаге из JSON
            step_number: Номер шага в пайплайне
            std_functions_path: Путь к стандартным функциям
            user_functions_path: Путь к пользовательским функциям
        """
        self.step_data = step_data
        self.step_number = step_number
        self.std_functions_path = std_functions_path
        self.user_functions_path = user_functions_path
        self.type = self._determine_step_type()
        
    def _determine_step_type(self) -> StepType:
        """Определяет тип шага на основе данных"""
        step_type = self.step_data.get("type", "")
        
        if step_type == "py_func":
            return StepType.PYTHON_FUNCTION
        elif step_type == "condition":
            return StepType.CONDITION
        elif step_type == "event":
            return StepType.EVENT
        else:
            return StepType.UNKNOWN
    
    async def execute(
        self,
        input_value: Any,
        final_frame: Dict[str, Dict[str, Any]],
        notifier: Optional[Any] = None
    ) -> Any:
        """
        Выполняет шаг пайплайна.

        Args:
            input_value: Входное значение для шага
            final_frame: Текущий кадр результатов
            notifier: Объект для отправки уведомлений

        Returns:
            Результат выполнения шага
        """
        if self.type == StepType.PYTHON_FUNCTION:
            return await self._execute_python_function(input_value, final_frame)
        elif self.type == StepType.CONDITION:
            return await self._execute_condition(input_value, final_frame)
        elif self.type == StepType.EVENT:
            return await self._execute_event(input_value, final_frame, notifier)
        else:
            # Для неизвестного типа просто пропускаем шаг
            return input_value
    
    async def _execute_python_function(
        self,
        input_value: Any,
        final_frame: Dict[str, Dict[str, Any]]
    ) -> Any:
        """
        Выполняет Python-функцию.

        Args:
            input_value: Входное значение
            final_frame: Текущий кадр результатов

        Returns:
            Результат выполнения функции
        """
        function_name = self.step_data.get("full_str", "")
        if function_name.startswith("*"):
            function_name = function_name[1:]
            
        # Если в функции содержатся аргументы, извлекаем их
        match = re.match(r"([a-zA-Z0-9_]+)(?:\((.*)\))?", function_name)
        if not match:
            return input_value
            
        func_name, args_str = match.groups()
        args_str = args_str or ""
        
        # Поиск функции сначала в пользовательских, затем в стандартных
        func = self._load_function(func_name)
        if not func:
            return input_value
        
        # Подготовка аргументов
        args = self._prepare_arguments(args_str, final_frame)
        
        # Специальная обработка для $this
        param = self.step_data.get("param", "")
        if param == "$this":
            args.insert(0, input_value)
        elif param:
            # Если переданы другие параметры, обрабатываем их
            parsed_params = self._prepare_arguments(param, final_frame)
            args.extend(parsed_params)
        
        # Выполнение функции (может быть асинхронной или синхронной)
        if inspect.iscoroutinefunction(func):
            return await func(*args)
        else:
            return func(*args)
    
    async def _execute_condition(
        self,
        input_value: Any,
        final_frame: Dict[str, Dict[str, Any]]
    ) -> Any:
        """
        Выполняет условную конструкцию.

        Args:
            input_value: Входное значение
            final_frame: Текущий кадр результатов

        Returns:
            Результат выполнения условия
        """
        sub_type = self.step_data.get("sub_type", "")
        
        if sub_type == "if":
            # Простое условие if
            if_data = self.step_data.get("if", {})
            expression = if_data.get("exp", {}).get("full_str", "")
            
            # Заменяем переменные в выражении на их значения
            eval_expression = self._prepare_expression(expression, input_value, final_frame)
            
            # Оцениваем выражение
            try:
                condition_result = eval(eval_expression)
                if condition_result:
                    # Выполняем действие if
                    action_data = if_data.get("do", {})
                    action_step = PipelineStep(
                        action_data, 
                        self.step_number, 
                        self.std_functions_path,
                        self.user_functions_path
                    )
                    return await action_step.execute(input_value, final_frame)
            except Exception as e:
                # В случае ошибки просто возвращаем входное значение
                pass
                
            # Если условие не выполнено или произошла ошибка, возвращаем входное значение
            return input_value
            
        elif sub_type == "if_else":
            # Условие if-else
            if_data = self.step_data.get("if", {})
            else_data = self.step_data.get("else", {})
            expression = if_data.get("exp", {}).get("full_str", "")
            
            # Заменяем переменные в выражении на их значения
            eval_expression = self._prepare_expression(expression, input_value, final_frame)
            
            try:
                condition_result = eval(eval_expression)
                if condition_result:
                    # Выполняем действие if
                    action_data = if_data.get("do", {})
                    action_step = PipelineStep(
                        action_data, 
                        self.step_number, 
                        self.std_functions_path,
                        self.user_functions_path
                    )
                    return await action_step.execute(input_value, final_frame)
                else:
                    # Выполняем действие else
                    action_data = else_data.get("do", {})
                    action_step = PipelineStep(
                        action_data, 
                        self.step_number, 
                        self.std_functions_path,
                        self.user_functions_path
                    )
                    return await action_step.execute(input_value, final_frame)
            except Exception as e:
                # В случае ошибки просто возвращаем входное значение
                pass
                
            # Если произошла ошибка, возвращаем входное значение
            return input_value
            
        elif sub_type == "if_elifs_else":
            # Условие if-elif-...-else
            if_data = self.step_data.get("if", {})
            expression = if_data.get("exp", {}).get("full_str", "")
            
            # Заменяем переменные в выражении на их значения
            eval_expression = self._prepare_expression(expression, input_value, final_frame)
            
            try:
                condition_result = eval(eval_expression)
                if condition_result:
                    # Выполняем действие if
                    action_data = if_data.get("do", {})
                    action_step = PipelineStep(
                        action_data, 
                        self.step_number, 
                        self.std_functions_path,
                        self.user_functions_path
                    )
                    return await action_step.execute(input_value, final_frame)
                
                # Проверяем все elif блоки
                elif_index = 1
                while f"elif_{elif_index}" in self.step_data:
                    elif_data = self.step_data.get(f"elif_{elif_index}", {})
                    elif_expression = elif_data.get("exp", {}).get("full_str", "")
                    
                    # Заменяем переменные в выражении на их значения
                    eval_elif_expression = self._prepare_expression(elif_expression, input_value, final_frame)
                    
                    try:
                        elif_condition_result = eval(eval_elif_expression)
                        if elif_condition_result:
                            # Выполняем действие elif
                            action_data = elif_data.get("do", {})
                            action_step = PipelineStep(
                                action_data, 
                                self.step_number, 
                                self.std_functions_path,
                                self.user_functions_path
                            )
                            return await action_step.execute(input_value, final_frame)
                    except Exception:
                        pass
                    
                    elif_index += 1
                
                # Если ни одно условие не выполнено, выполняем else блок
                else_data = self.step_data.get("else", {})
                if else_data:
                    action_data = else_data.get("do", {})
                    action_step = PipelineStep(
                        action_data, 
                        self.step_number, 
                        self.std_functions_path,
                        self.user_functions_path
                    )
                    return await action_step.execute(input_value, final_frame)
                
            except Exception as e:
                # В случае ошибки просто возвращаем входное значение
                pass
            
            # Если ни одно условие не выполнено или произошла ошибка, возвращаем входное значение
            return input_value
        
        # Для неизвестного типа условия просто возвращаем входное значение
        return input_value
    
    async def _execute_event(
        self,
        input_value: Any,
        final_frame: Dict[str, Dict[str, Any]],
        notifier: Optional[Any] = None
    ) -> Any:
        """
        Выполняет событие.

        Args:
            input_value: Входное значение
            final_frame: Текущий кадр результатов
            notifier: Объект для отправки уведомлений

        Returns:
            Результат обработки события
        """
        from src.generator.python.exeptions import EventSkipException, EventRollbackException
        
        sub_type = self.step_data.get("sub_type", "")
        message = self.step_data.get("param", "")
        
        # Преобразуем строковый параметр (если он в кавычках)
        if message.startswith('"') and message.endswith('"'):
            message = message[1:-1]
        
        # Отправляем уведомление через нотификатор
        if notifier:
            notifier.event_notify(sub_type, message)
        
        # Обрабатываем различные типы событий
        if sub_type == "SKIP":
            raise EventSkipException(message)
        elif sub_type == "ROLLBACK":
            raise EventRollbackException(message)
        
        # Для NOTIFY и других типов просто возвращаем входное значение
        return input_value
    
    def _load_function(self, func_name: str) -> Optional[Callable]:
        """
        Загружает функцию из пользовательских или стандартных модулей.

        Args:
            func_name: Имя функции

        Returns:
            Загруженная функция или None, если функция не найдена
        """
        # Проверяем специальные функции
        if func_name == "get":
            return lambda *args, **kwargs: args[0] if args else None
        elif func_name == "s1":
            return lambda x: int(x) if x and isinstance(x, str) and x.isdigit() else 0
        
        # Сначала пытаемся загрузить из пользовательских функций
        if self.user_functions_path:
            try:
                # Пытаемся найти файл с функцией в папке пользовательских функций
                import os
                import sys
                import importlib.util
                
                # Если указан относительный путь, добавляем текущую директорию
                if not os.path.isabs(self.user_functions_path):
                    module_path = os.path.join(os.getcwd(), self.user_functions_path)
                else:
                    module_path = self.user_functions_path
                
                # Ищем в разных файлах
                found = False
                
                # Сначала проверяем файл с именем функции
                file_path = os.path.join(module_path, f"{func_name}.py")
                if os.path.exists(file_path):
                    spec = importlib.util.spec_from_file_location(func_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, "func"):
                        return getattr(module, "func")
                    found = True
                
                # Также проверяем basic_funcs.py
                file_path = os.path.join(module_path, "basic_funcs.py")
                if os.path.exists(file_path):
                    spec = importlib.util.spec_from_file_location("basic_funcs", file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, func_name):
                        return getattr(module, func_name)
                    found = True
                
                if found:
                    # Если файл найден, но функция не найдена, возвращаем фиктивную функцию
                    return lambda *args, **kwargs: args[0] if args else None
                
            except Exception as e:
                # Логируем ошибку и продолжаем
                import traceback
                print(f"Ошибка при загрузке функции {func_name}: {str(e)}")
                traceback.print_exc()
        
        # Пытаемся загрузить из стандартных функций
        try:
            module = importlib.import_module(f"{self.std_functions_path}.{func_name}")
            return getattr(module, func_name)
        except (ImportError, AttributeError):
            # Если не удалось загрузить, пытаемся найти в глобальном пространстве имен
            if func_name in globals():
                return globals()[func_name]
        
        # Если функция не найдена, возвращаем функцию-заглушку
        return lambda *args, **kwargs: args[0] if args else None
    
    def _prepare_arguments(
        self,
        args_str: str,
        final_frame: Dict[str, Dict[str, Any]]
    ) -> List[Any]:
        """
        Подготавливает аргументы для функции.

        Args:
            args_str: Строка с аргументами
            final_frame: Текущий кадр результатов

        Returns:
            Список аргументов для функции
        """
        if not args_str:
            return []
        
        # Разбиваем строку аргументов по запятой, учитывая возможные вложенные скобки
        args = []
        current_arg = ""
        bracket_count = 0
        
        for char in args_str:
            if char == ',' and bracket_count == 0:
                args.append(current_arg.strip())
                current_arg = ""
            else:
                if char == '(':
                    bracket_count += 1
                elif char == ')':
                    bracket_count -= 1
                current_arg += char
                
        if current_arg:
            args.append(current_arg.strip())
        
        # Обрабатываем каждый аргумент
        processed_args = []
        for arg in args:
            # Проверяем, является ли аргумент ссылкой на переменную из final_frame
            if arg.startswith('$') and not arg.startswith('$$'):
                var_name = arg[1:]
                if var_name in final_frame:
                    processed_args.append(final_frame[var_name]['final_value'])
                else:
                    processed_args.append(None)
            # Проверяем строковые литералы
            elif (arg.startswith('"') and arg.endswith('"')) or (arg.startswith("'") and arg.endswith("'")):
                processed_args.append(arg[1:-1])
            # Проверяем числовые литералы
            elif arg.isdigit():
                processed_args.append(int(arg))
            elif arg.lower() == 'true':
                processed_args.append(True)
            elif arg.lower() == 'false':
                processed_args.append(False)
            elif arg.lower() == 'none':
                processed_args.append(None)
            else:
                # Для других типов пытаемся преобразовать в соответствующий тип
                try:
                    processed_args.append(eval(arg))
                except:
                    processed_args.append(arg)
        
        return processed_args
    
    def _prepare_expression(
        self,
        expression: str,
        input_value: Any,
        final_frame: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        Подготавливает выражение для выполнения, заменяя переменные на их значения.

        Args:
            expression: Выражение для оценки
            input_value: Текущее входное значение
            final_frame: Текущий кадр результатов

        Returns:
            Подготовленное выражение для eval()
        """
        # Заменяем $this на входное значение
        expression = expression.replace('$this', self._value_to_python_literal(input_value))
        
        # Заменяем переменные из final_frame
        for var_name, var_data in final_frame.items():
            if f'${var_name}' in expression:
                var_value = var_data.get('final_value')
                expression = expression.replace(f'${var_name}', self._value_to_python_literal(var_value))
        
        return expression
    
    def _value_to_python_literal(self, value: Any) -> str:
        """
        Преобразует значение в строковое представление Python-литерала.

        Args:
            value: Значение для преобразования

        Returns:
            Строковое представление литерала
        """
        if value is None:
            return 'None'
        elif isinstance(value, (int, float, bool)):
            return str(value)
        elif isinstance(value, str):
            return f'"{value}"'
        else:
            return str(value) 