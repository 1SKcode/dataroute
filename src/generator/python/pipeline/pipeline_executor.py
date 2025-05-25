from typing import Dict, List, Any, Optional, Set, Tuple
import asyncio
from pydantic import BaseModel, create_model, ValidationError

from src.generator.python.pipeline.pipeline_builder import PipelineBuilder
from src.generator.python.pipeline.pipeline_step import PipelineStep
from src.generator.python.exeptions import PipelineExecutionError, EventSkipException, EventRollbackException


class PipelineExecutor:
    """Класс для асинхронного выполнения пайплайнов"""
    
    def __init__(
        self,
        config: Dict[str, Any],
        std_functions_path: str,
        user_functions_path: Optional[str] = None,
        notifier: Optional[Any] = None
    ):
        """
        Инициализирует исполнитель пайплайнов.
        
        Args:
            config: Конфигурация ETL процесса из JSON
            std_functions_path: Путь к стандартным функциям
            user_functions_path: Путь к пользовательским функциям
            notifier: Объект для отправки уведомлений
        """
        self.config = config
        self.std_functions_path = std_functions_path
        self.user_functions_path = user_functions_path
        self.notifier = notifier
        self.pipeline_builders = {}
        
        # Инициализируем построители пайплайнов для каждого таргета
        for target_key, target_config in config.items():
            if target_key != "lang" and target_key != "global_vars":
                self.pipeline_builders[target_key] = PipelineBuilder(
                    target_config,
                    std_functions_path,
                    user_functions_path
                )
    
    async def execute(self, source_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Dict[str, Any]]]]:
        """
        Выполняет ETL процесс для указанных исходных данных.
        
        Args:
            source_data: Исходные данные для обработки
            
        Returns:
            Словарь с результатами для каждого таргета
        """
        results = {}
        
        # Обрабатываем каждый таргет
        for target_key, builder in self.pipeline_builders.items():
            target_config = self.config[target_key]
            results[target_key] = await self._process_target(target_config, builder, source_data)
            
        return results
    
    async def _process_target(
        self,
        target_config: Dict[str, Any],
        pipeline_builder: PipelineBuilder,
        source_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Dict[str, Any]]]:
        """
        Обрабатывает данные для указанного таргета.
        
        Args:
            target_config: Конфигурация таргета
            pipeline_builder: Построитель пайплайнов для таргета
            source_data: Исходные данные для обработки
            
        Returns:
            Список с обработанными данными для таргета
        """
        warehouse = []
        
        # Для каждой записи в исходных данных
        for record in source_data:
            try:
                # Обрабатываем запись и добавляем результат в warehouse
                final_frame = await self._process_record(record, target_config, pipeline_builder)
                if final_frame:
                    warehouse.append(final_frame)
            except EventSkipException as e:
                # Пропускаем текущую запись
                if self.notifier:
                    self.notifier.warning(f"Пропуск записи: {str(e)}")
                continue
            except EventRollbackException as e:
                # Прерываем весь процесс ETL
                if self.notifier:
                    self.notifier.critical(f"Отмена процесса ETL: {str(e)}")
                break
        
        return warehouse
    
    async def _process_record(
        self,
        record: Dict[str, Any],
        target_config: Dict[str, Any],
        pipeline_builder: PipelineBuilder
    ) -> Dict[str, Dict[str, Any]]:
        """
        Обрабатывает одну запись для указанного таргета.
        
        Args:
            record: Исходная запись для обработки
            target_config: Конфигурация таргета
            pipeline_builder: Построитель пайплайнов для таргета
            
        Returns:
            Словарь с обработанными данными записи
        """
        # Инициализируем final_frame для текущей записи
        final_frame = {}
        
        # Получаем план выполнения
        execution_plan = target_config.get("execution_plan", [])
        
        # Выполняем каждый уровень плана последовательно
        for level in execution_plan:
            # Для каждого уровня создаем задачи для асинхронного выполнения
            tasks = []
            for source_name in level:
                # Создаем задачу для выполнения пайплайна поля
                task = self._process_field(
                    source_name,
                    record,
                    target_config,
                    pipeline_builder,
                    final_frame
                )
                tasks.append(task)
            
            # Ждем выполнения всех задач текущего уровня
            await asyncio.gather(*tasks)
        
        return final_frame
    
    async def _process_field(
        self,
        source_name: str,
        record: Dict[str, Any],
        target_config: Dict[str, Any],
        pipeline_builder: PipelineBuilder,
        final_frame: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Обрабатывает одно поле записи.
        
        Args:
            source_name: Имя исходного поля
            record: Исходная запись
            target_config: Конфигурация таргета
            pipeline_builder: Построитель пайплайнов для таргета
            final_frame: Текущий кадр результатов
        """
        # Получаем конечный тип и имя поля
        final_type, final_name = pipeline_builder.get_final_type_and_name(source_name)
        
        # Если final_name не задан, пропускаем поле
        if final_name is None:
            return
        
        # Получаем исходное значение
        if source_name.startswith("__void"):
            # Для void-полей используем None
            input_value = None
        else:
            # Для обычных полей берем значение из записи
            input_value = record.get(source_name)
        
        # Строим пайплайн для поля
        pipeline = pipeline_builder.build_pipeline(source_name)
        
        # Если пайплайн пустой, просто копируем значение
        if not pipeline:
            final_value = input_value
        else:
            # Выполняем пайплайн
            try:
                final_value = input_value
                for step in pipeline:
                    final_value = await step.execute(final_value, final_frame, self.notifier)
            except Exception as e:
                # Обрабатываем ошибки выполнения пайплайна
                if not isinstance(e, (EventSkipException, EventRollbackException)):
                    raise PipelineExecutionError(source_name, str(step.step_number), e)
                raise e
        
        # Добавляем результат в final_frame
        final_frame[final_name] = {
            'source_name': source_name,
            'final_type': final_type,
            'final_value': self._cast_value(final_value, final_type)
        }
    
    def _cast_value(self, value: Any, type_name: Optional[str]) -> Any:
        """
        Преобразует значение к указанному типу.
        
        Args:
            value: Значение для преобразования
            type_name: Имя типа
            
        Returns:
            Преобразованное значение
        """
        if value is None or type_name is None:
            return value
        
        try:
            if type_name == "int":
                if value == "" or value is None:
                    return 0
                return int(value)
            elif type_name == "float":
                if value == "" or value is None:
                    return 0.0
                return float(value)
            elif type_name == "bool":
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes", "y", "t")
                return bool(value)
            elif type_name == "str":
                if value is None:
                    return ""
                return str(value)
            else:
                # Для неизвестных типов возвращаем значение как есть
                return value
        except (ValueError, TypeError):
            # В случае ошибки преобразования возвращаем значение по умолчанию для типа
            if type_name == "int":
                return 0
            elif type_name == "float":
                return 0.0
            elif type_name == "bool":
                return False
            elif type_name == "str":
                return ""
            else:
                return value 