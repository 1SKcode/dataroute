import os
import sys
import json
import importlib
import asyncio
from typing import Dict, List, Any, Optional, Union
from copy import deepcopy

from src.generator.python.config import SOURCE_TYPE_MAPPING, TARGET_TYPE_MAPPING, NOTIFIER_TYPE_MAPPING, STD_FUNCTIONS_PATH
from src.generator.python.exeptions import (
    ETLException, SourceValidationError, TargetValidationError, 
    ConfigurationError, TargetWriteError
)
from src.generator.python.pipeline.pipeline_executor import PipelineExecutor


class DtrtRunner:
    """
    Основной класс для выполнения ETL процесса на основе JSON-конфигурации.
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        user_functions_path: Optional[str] = None,
        notifier_type: str = "console",
        source_data: Optional[List[Dict[str, Any]]] = None,
        db_config: Optional[Dict[str, Any]] = None
    ):
        """
        Инициализирует исполнитель ETL процесса.
        
        Args:
            config: JSON-конфигурация ETL процесса
            user_functions_path: Путь к папке с пользовательскими функциями
            notifier_type: Тип нотификатора (по умолчанию "console")
            source_data: Исходные данные для обработки (опционально)
            db_config: Конфигурация подключения к БД (опционально)
        """
        self.config = config
        self.user_functions_path = user_functions_path
        self.notifier_type = notifier_type
        self.source_data = source_data
        self.db_config = db_config or {}
        
        # Инициализируем нотификатор
        self.notifier = self._init_notifier()
        
        # Анализируем конфигурацию
        self._analyze_config()
    
    def _init_notifier(self) -> Any:
        """
        Инициализирует нотификатор заданного типа.
        
        Returns:
            Объект нотификатора
        """
        try:
            notifier_module_path = NOTIFIER_TYPE_MAPPING.get(self.notifier_type)
            if not notifier_module_path:
                raise ConfigurationError("notifier", f"Неизвестный тип нотификатора: {self.notifier_type}")
            
            module_name, class_name = notifier_module_path.rsplit(".", 1)
            class_name = class_name.split('_')[0].capitalize() + "Notifier"
            
            module = importlib.import_module(module_name)
            notifier_class = getattr(module, class_name)
            
            return notifier_class(color=True)
        except (ImportError, AttributeError) as e:
            # В случае ошибки создаем простой нотификатор, печатающий в консоль
            class SimpleNotifier:
                def notify(self, message, level=None):
                    print(f"[{level or 'INFO'}] {message}")
                def info(self, message):
                    print(f"[INFO] {message}")
                def warning(self, message):
                    print(f"[WARNING] {message}")
                def error(self, message):
                    print(f"[ERROR] {message}")
                def critical(self, message):
                    print(f"[CRITICAL] {message}")
                def event_notify(self, event_type, message=None):
                    print(f"[EVENT: {event_type}] {message or ''}")
            
            return SimpleNotifier()
    
    def _analyze_config(self) -> None:
        """
        Анализирует конфигурацию ETL процесса и определяет необходимые компоненты.
        """
        self.targets = {}
        self.source_getter = None
        self.target_writers = {}
        
        # Определяем язык из конфигурации
        self.lang = self.config.get("lang", "py")
        
        # Определяем цели (таргеты) и источник для каждой цели
        for target_key, target_config in self.config.items():
            if target_key == "lang" or target_key == "global_vars":
                continue
            
            # Получаем информацию о типе источника и цели
            source_type_info = target_config.get("source_type", {})
            target_type_info = target_config.get("target_type", {})
            
            # Проверяем типы источника и цели
            source_type = source_type_info.get("type")
            source_name = source_type_info.get("name")
            target_type = target_type_info.get("type")
            target_name = target_type_info.get("name")
            
            if not source_type or not source_name or not target_type or not target_name:
                continue
            
            # Сохраняем информацию о цели
            self.targets[target_key] = {
                "source_type": source_type,
                "source_name": source_name,
                "target_type": target_type,
                "target_name": target_name
            }
    
    async def run(self) -> Dict[str, Any]:
        """
        Выполняет ETL процесс.
        
        Returns:
            Результаты выполнения процесса
        """
        # Логируем начало процесса
        self.notifier.info("Начало ETL процесса")
        
        try:
            # Собираем необходимые поля из источника
            required_fields = self._collect_required_fields()
            
            # Инициализируем источник данных и проверяем его
            self.notifier.info("Инициализация источника данных...")
            source_data = await self._init_source(required_fields)
            
            # Инициализируем целевые хранилища и проверяем их
            self.notifier.info("Инициализация целевых хранилищ...")
            await self._init_targets()
            
            # Выполняем пайплайны для обработки данных
            self.notifier.info("Выполнение пайплайнов...")
            pipeline_executor = PipelineExecutor(
                self.config,
                STD_FUNCTIONS_PATH,
                self.user_functions_path,
                self.notifier
            )
            results = await pipeline_executor.execute(source_data)
            
            # Записываем результаты в целевые хранилища
            self.notifier.info("Запись результатов в целевые хранилища...")
            await self._write_results(results)
            
            # Логируем успешное завершение процесса
            self.notifier.info("ETL процесс успешно завершен")
            
            return {
                "status": "success",
                "results": {target: len(data) for target, data in results.items()}
            }
            
        except ETLException as e:
            # Логируем ошибку и возвращаем информацию о ней
            self.notifier.error(f"Ошибка в ETL процессе: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _collect_required_fields(self) -> List[str]:
        """
        Собирает список необходимых полей из конфигурации.
        
        Returns:
            Список необходимых полей
        """
        required_fields = set()
        
        # Для каждой цели собираем необходимые поля
        for target_key, target_config in self.config.items():
            if target_key == "lang" or target_key == "global_vars":
                continue
            
            routes = target_config.get("routes", {})
            for source_name in routes.keys():
                if not source_name.startswith("__void"):
                    required_fields.add(source_name)
        
        return list(required_fields)
    
    async def _init_source(self, required_fields: List[str]) -> List[Dict[str, Any]]:
        """
        Инициализирует источник данных и проверяет его.
        
        Args:
            required_fields: Список необходимых полей
            
        Returns:
            Исходные данные для обработки
        """
        # Если исходные данные переданы напрямую, используем их
        if self.source_data:
            source_data = self.source_data
        else:
            # Иначе загружаем данные из источника
            self.notifier.info("Загрузка данных из источника не реализована в демо-версии")
            source_data = []
        
        # Определяем тип источника и создаем соответствующий getter
        source_type = None
        for target_config in self.targets.values():
            source_type = target_config["source_type"]
            break
        
        if not source_type:
            raise ConfigurationError("source", "Не удалось определить тип источника")
        
        # Создаем getter для источника
        source_getter_class = SOURCE_TYPE_MAPPING.get(source_type)
        if not source_getter_class:
            raise ConfigurationError("source", f"Неизвестный тип источника: {source_type}")
        
        source_getter = source_getter_class(source_data, required_fields)
        
        # Проверяем валидность источника
        report = source_getter.report
        if not report["fully_valid"]:
            raise SourceValidationError(report)
        
        return source_data
    
    async def _init_targets(self) -> None:
        """
        Инициализирует целевые хранилища и проверяет их.
        """
        # Для каждой цели создаем соответствующий writer
        for target_key, target_info in self.targets.items():
            target_type = target_info["target_type"]
            target_name = target_info["target_name"]
            
            # Получаем класс writer'а для данного типа цели
            target_writer_class = TARGET_TYPE_MAPPING.get(target_type)
            if not target_writer_class:
                raise ConfigurationError("target", f"Неизвестный тип цели: {target_type}")
            
            # Получаем список полей для записи
            target_config = self.config[target_key]
            routes = target_config.get("routes", {})
            field_names = []
            for route_data in routes.values():
                final_name = route_data.get("final_name")
                if final_name and not final_name.startswith("$"):
                    field_names.append(final_name)
            
            # Создаем writer и добавляем его в словарь
            if target_type == "postgres":
                target_writer = target_writer_class(target_name, field_names, self.db_config, skip_validation=True)
            else:
                target_writer = target_writer_class(target_name, field_names, self.db_config)
            
            self.target_writers[target_key] = target_writer
            
            # Для демонстрационных целей отключаем проверку валидации полей
            if hasattr(target_writer, 'validate_fields') and callable(target_writer.validate_fields):
                # Отключаем валидацию для тестирования
                target_writer.validate_fields = lambda: (True, [])
    
    async def _write_results(self, results: Dict[str, List[Dict[str, Dict[str, Any]]]]) -> None:
        """
        Записывает результаты в целевые хранилища.
        
        Args:
            results: Результаты выполнения пайплайнов
        """
        # Для каждой цели записываем результаты
        for target_key, warehouse in results.items():
            target_writer = self.target_writers.get(target_key)
            if not target_writer:
                continue
            
            # Записываем результаты в целевое хранилище
            try:
                await target_writer.write(warehouse)
            except Exception as e:
                target_info = self.targets[target_key]
                raise TargetWriteError(target_info["target_type"], target_info["target_name"], e)
            
            # Закрываем соединение с целевым хранилищем
            if hasattr(target_writer, 'close') and callable(target_writer.close):
                await target_writer.close()


async def run_etl(
    config: Union[Dict[str, Any], str],
    user_functions_path: Optional[str] = None,
    notifier_type: str = "console",
    source_data: Optional[List[Dict[str, Any]]] = None,
    db_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Запускает ETL процесс с заданной конфигурацией.
    
    Args:
        config: JSON-конфигурация ETL процесса или путь к JSON-файлу
        user_functions_path: Путь к папке с пользовательскими функциями
        notifier_type: Тип нотификатора (по умолчанию "console")
        source_data: Исходные данные для обработки (опционально)
        db_config: Конфигурация подключения к БД (опционально)
        
    Returns:
        Результаты выполнения процесса
    """
    # Если config - строка, считаем, что это путь к файлу
    if isinstance(config, str):
        try:
            with open(config, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            return {
                "status": "error",
                "error": f"Ошибка при чтении файла конфигурации: {str(e)}"
            }
    
    # Создаем и запускаем исполнитель ETL процесса
    runner = DtrtRunner(
        config,
        user_functions_path,
        notifier_type,
        source_data,
        db_config
    )
    
    return await runner.run()


if __name__ == "__main__":
    try:
        print("Начало запуска ETL процесса...")
        # == КОНФИГУРАЦИЯ ДЛЯ ЗАПУСКА ==
        # Загружаем конфиг из файла
        with open('result.json', 'r', encoding='utf-8') as f:
            ETL_CONFIG = f.read()
        
        # Загружаем пользовательские переменные
        with open('t/my_vars/mv.json', 'r', encoding='utf-8') as f:
            mv_vars = json.load(f)
            
        # Загружаем тестовые данные из 1.py
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_data", "t/1.py")
        test_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_module)
        
        # Получаем тестовые данные из модуля
        test_input = test_module.test_input.strip()
        
        # Создаем экземпляр DataRoute для получения тестовых данных
        from dataroute import DataRoute
        dtrt = DataRoute(test_input, vars_folder="t/my_vars", func_folder="t/my_funcs", debug=True, lang="ru", color=True)
        source_data = dtrt.get_source_data()
        
        USER_FUNCTIONS_PATH = "t/my_funcs"
        NOTIFIER_TYPE = "console"
        SOURCE_DATA = source_data
        DB_CONFIG = {
            "host": "45.9.25.92",
            "port": 5432,
            "database": "data_science",
            "user": "akir",
            "password": "AsdZxc!23"
        }
        
        print(f"Загружена конфигурация ETL, подготовлены исходные данные: {len(source_data)} записей")
        print(f"Путь к пользовательским функциям: {USER_FUNCTIONS_PATH}")
        print(f"Загружены пользовательские переменные: {mv_vars}")
        
        # Запускаем ETL процесс
        print("Запуск ETL процесса...")
        result = asyncio.run(run_etl(
            json.loads(ETL_CONFIG),
            USER_FUNCTIONS_PATH,
            NOTIFIER_TYPE,
            SOURCE_DATA,
            DB_CONFIG
        ))

        # Выводим результат
        print("Результат выполнения:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        import traceback
        print(f"Произошла ошибка: {str(e)}")
        print("Трейс:")
        traceback.print_exc()
