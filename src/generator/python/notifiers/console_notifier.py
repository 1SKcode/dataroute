from typing import Optional
import logging
from datetime import datetime
import sys


class ConsoleNotifier:
    """Простой нотификатор для вывода сообщений в консоль"""
    
    COLORS = {
        "INFO": "\033[92m",     # Зеленый
        "WARNING": "\033[93m",  # Желтый
        "ERROR": "\033[91m",    # Красный
        "CRITICAL": "\033[91m\033[1m",  # Жирный красный
        "RESET": "\033[0m"      # Сброс цвета
    }
    
    def __init__(self, color: bool = True):
        """
        Инициализирует консольный нотификатор.
        
        Args:
            color: Использовать ли цветной вывод. По умолчанию True.
        """
        self.color = color
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Настраивает логгер для вывода в консоль"""
        logger = logging.getLogger("console_notifier")
        logger.setLevel(logging.INFO)
        
        # Очищаем существующие обработчики, если они есть
        if logger.handlers:
            logger.handlers.clear()
        
        # Создаем обработчик для вывода в консоль
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', 
                                     datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _colorize(self, level: str, message: str) -> str:
        """Добавляет цвет к сообщению в зависимости от уровня"""
        if not self.color:
            return message
        
        color = self.COLORS.get(level, self.COLORS["RESET"])
        return f"{color}{message}{self.COLORS['RESET']}"
    
    def info(self, message: str) -> None:
        """Выводит информационное сообщение"""
        self.logger.info(self._colorize("INFO", message))
    
    def warning(self, message: str) -> None:
        """Выводит предупреждение"""
        self.logger.warning(self._colorize("WARNING", message))
    
    def error(self, message: str) -> None:
        """Выводит сообщение об ошибке"""
        self.logger.error(self._colorize("ERROR", message))
    
    def critical(self, message: str) -> None:
        """Выводит критическое сообщение"""
        self.logger.critical(self._colorize("CRITICAL", message))
    
    def notify(self, message: str, level: str = "INFO") -> None:
        """
        Выводит уведомление с указанным уровнем важности.
        
        Args:
            message: Текст уведомления
            level: Уровень важности (INFO, WARNING, ERROR, CRITICAL)
        """
        level = level.upper()
        if level == "INFO":
            self.info(message)
        elif level == "WARNING":
            self.warning(message)
        elif level == "ERROR":
            self.error(message)
        elif level == "CRITICAL":
            self.critical(message)
        else:
            self.info(message)
    
    def event_notify(self, event_type: str, message: Optional[str] = None) -> None:
        """
        Обрабатывает уведомление о событии.
        
        Args:
            event_type: Тип события (NOTIFY, SKIP, ROLLBACK)
            message: Дополнительное сообщение
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if event_type == "NOTIFY":
            level = "INFO"
            prefix = "УВЕДОМЛЕНИЕ"
        elif event_type == "SKIP":
            level = "WARNING"
            prefix = "ПРОПУСК ЗАПИСИ"
        elif event_type == "ROLLBACK":
            level = "CRITICAL"
            prefix = "ОТМЕНА ПРОЦЕССА"
        else:
            level = "INFO"
            prefix = "СОБЫТИЕ"
        
        msg = f"{prefix}: {message}" if message else prefix
        self.notify(msg, level=level)
