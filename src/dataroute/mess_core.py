from .config import Config
from .localization import Localization, Messages
import sys
import re

ANSI_COLORS = {
    "RS": "\033[0m",        # Сброс цвета
    "G": "\033[32m",        # Зеленый
    "R": "\033[31m",        # Красный
    "Y": "\033[33m",        # Желтый
    "O": "\033[38;5;208m",  # Оранжевый
    "BOLD": "\033[1m",      # Жирный шрифт акцента
}

def colorize(text: str) -> str:
    if not Config.is_color():
        # Удаляем все >NAME< теги
        return re.sub(r'>[A-Z]+<', '', text)
    def repl(match):
        tag = match.group(0)[1:-1]
        return ANSI_COLORS.get(tag, '')
    return re.sub(r'>[A-Z]+<', repl, text)

def pr(msg, *args, **kwargs):
    """
    Универсальный вывод локализованных сообщений.
    msg: сообщение из Messages (например, Messages.Info.TOKENIZATION_START) или строка/ошибка
    args/kwargs: параметры для format
    """
    # Если это не dict (например, строка или DSLSyntaxError), просто печатаем
    if not isinstance(msg, dict):
        print(colorize(str(msg)), *args, file=sys.stdout)
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
    text = colorize(text)
    print(text, *args, file=sys.stdout)