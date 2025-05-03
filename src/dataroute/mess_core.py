from .config import Config
from .localization import Localization, Messages
import sys

def pr(msg, *args, **kwargs):
    """
    Универсальный вывод локализованных сообщений.
    msg: сообщение из Messages (например, Messages.Info.TOKENIZATION_START) или строка/ошибка
    args/kwargs: параметры для format
    """
    # Если это не dict (например, строка или DSLSyntaxError), просто печатаем
    if not isinstance(msg, dict):
        print(msg, *args, file=sys.stdout)
        return
    # Определяем тип сообщения по имени класса Messages
    msg_type = None
    for cls in (Messages.Debug, Messages.Info, Messages.Warning, Messages.Error, Messages.Hint):
        if msg in cls.__dict__.values():
            msg_type = cls.__name__
            break
    # Debug-сообщения выводим только если debug включён
    if msg_type == "Debug" and not Config.is_debug():
        return
    # Получаем строку на нужном языке
    text = Localization(Config.get_lang()).get(msg, **kwargs)
    print(text, *args, file=sys.stdout)

# В будущем: notify, log, warn, error и т.д. 