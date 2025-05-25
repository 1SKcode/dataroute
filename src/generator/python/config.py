from typing import Dict, Type

# Импорты источников данных
from src.generator.python.source_getters.pydict_source_getter import PydictSourceGetter

# Импорты целевых хранилищ 
from src.generator.python.target_writers.pg_target_writer import PgTargetWriter

# Маппинг типов источников на соответствующие классы
SOURCE_TYPE_MAPPING: Dict[str, Type] = {
    "dict": PydictSourceGetter,
}

# Маппинг типов целевых хранилищ на соответствующие классы
TARGET_TYPE_MAPPING: Dict[str, Type] = {
    "postgres": PgTargetWriter,
}

# Маппинг типов нотификаторов
NOTIFIER_TYPE_MAPPING: Dict[str, str] = {
    "console": "src.generator.python.notifiers.console_notifier",
}

# Стандартные функции
STD_FUNCTIONS_PATH = "src.std_func.python"

# События для нотификаций
EVENT_TYPES = {
    "NOTIFY": "notify",  # Просто уведомление
    "SKIP": "skip",      # Пропустить текущую запись
    "ROLLBACK": "rollback"  # Прервать весь процесс
}
