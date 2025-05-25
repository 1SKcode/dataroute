from .config import Config
from .localization import Localization, Messages
import sys
import re
from typing import Optional
ANSI_COLORS = {
    "RS": "\033[0m",        # Сброс цвета
    "G": "\033[32m",        # Зеленый
    "R": "\033[31m",        # Красный
    "Y": "\033[33m",        # Желтый
    "O": "\033[38;5;208m",  # Оранжевый
    "BOLD": "\033[1m",      # Жирный шрифт акцента
}

def colorize(text: str, use_color: bool = True) -> str:
    if not use_color:
        # Удаляем все >NAME< теги
        return re.sub(r'>[A-Z]+<', '', text)
    def repl(match):
        tag = match.group(0)[1:-1]
        return ANSI_COLORS.get(tag, '')
    return re.sub(r'>[A-Z]+<', repl, text)

def pr(msg, *args, debug: Optional[bool] = None, lang: Optional[str] = None, color: Optional[bool] = None, **kwargs):
    """
    Универсальный вывод локализованных сообщений.
    
    Args:
        msg: Сообщение из Messages (например, Messages.Info.TOKENIZATION_START) или строка/ошибка
        *args: Дополнительные параметры для print
        debug: Флаг режима отладки (если None, используется Config.is_debug())
        lang: Язык сообщений (если None, используется Config.get_lang())
        color: Флаг использования цветов (если None, используется Config.is_color())
        **kwargs: Параметры для форматирования сообщения
    """
    # Используем переданные значения или берём из конфига
    use_debug = debug if debug is not None else Config.is_debug()
    use_lang = lang if lang is not None else Config.get_lang()
    use_color = color if color is not None else Config.is_color()
    
    # Если это не dict (например, строка или DSLSyntaxError), просто печатаем
    if not isinstance(msg, dict):
        print(colorize(str(msg), use_color), *args, file=sys.stdout)
        return
        
    # Определяем тип сообщения по имени класса Messages
    msg_type = None
    for cls in (Messages.Debug, Messages.Info, Messages.Warning, Messages.Error, Messages.Hint):
        if msg in cls.__dict__.values():
            msg_type = cls.__name__
            break
            
    # Debug-сообщения выводим только если debug включён
    if msg_type == "Debug" and not use_debug:
        return
        
    # Получаем строку на нужном языке
    text = Localization(use_lang).get(msg, **kwargs)
    text = colorize(text, use_color)
    print(text, *args, file=sys.stdout)