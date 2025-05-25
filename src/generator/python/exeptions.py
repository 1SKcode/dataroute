from typing import Dict, Any, List


class ETLException(Exception):
    """Базовый класс для всех исключений ETL процесса"""
    pass


class SourceValidationError(ETLException):
    """Исключение при ошибке валидации источника данных"""
    
    def __init__(self, report: Dict[str, Any]):
        self.report = report
        self.message = self._format_message()
        super().__init__(self.message)
    
    def _format_message(self) -> str:
        """Форматирует сообщение об ошибке на основе отчета валидации"""
        message = (
            f"Ошибка валидации источника данных '{self.report['source']}':\n"
            f"Общее количество записей: {self.report['total_received']}\n"
            f"Валидных записей: {self.report['valid_count']} ({self.report['percent_valid']}%)\n"
            f"Невалидных записей: {self.report['invalid_count']}\n"
        )
        
        if self.report['invalid_examples']:
            message += "Примеры невалидных записей:\n"
            for example in self.report['invalid_examples']:
                message += f"- Индекс {example['index']}: отсутствуют ключи {', '.join(example['missing_keys'])}\n"
        
        return message


class TargetValidationError(ETLException):
    """Исключение при ошибке валидации целевого хранилища"""
    
    def __init__(self, target_type: str, target_name: str, missing_fields: List[str]):
        self.target_type = target_type
        self.target_name = target_name
        self.missing_fields = missing_fields
        self.message = self._format_message()
        super().__init__(self.message)
    
    def _format_message(self) -> str:
        """Форматирует сообщение об ошибке валидации целевого хранилища"""
        return (
            f"Ошибка валидации целевого хранилища '{self.target_type}/{self.target_name}':\n"
            f"Отсутствующие поля: {', '.join(self.missing_fields)}"
        )


class PipelineExecutionError(ETLException):
    """Исключение при ошибке выполнения пайплайна"""
    
    def __init__(self, source_name: str, pipeline_step: str, error: Exception):
        self.source_name = source_name
        self.pipeline_step = pipeline_step
        self.error = error
        self.message = self._format_message()
        super().__init__(self.message)
    
    def _format_message(self) -> str:
        """Форматирует сообщение об ошибке выполнения пайплайна"""
        return (
            f"Ошибка выполнения пайплайна для поля '{self.source_name}' на шаге '{self.pipeline_step}':\n"
            f"{type(self.error).__name__}: {str(self.error)}"
        )


class ConfigurationError(ETLException):
    """Исключение при ошибке конфигурации"""
    
    def __init__(self, component: str, reason: str):
        self.component = component
        self.reason = reason
        self.message = f"Ошибка конфигурации компонента '{component}': {reason}"
        super().__init__(self.message)


class TargetWriteError(ETLException):
    """Исключение при ошибке записи в целевое хранилище"""
    
    def __init__(self, target_type: str, target_name: str, error: Exception):
        self.target_type = target_type
        self.target_name = target_name
        self.error = error
        self.message = (
            f"Ошибка записи в целевое хранилище '{target_type}/{target_name}':\n"
            f"{type(error).__name__}: {str(error)}"
        )
        super().__init__(self.message)


class EventSkipException(ETLException):
    """Исключение для пропуска текущей записи"""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class EventRollbackException(ETLException):
    """Исключение для отмены всего процесса ETL"""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
