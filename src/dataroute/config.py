class Config:
    """Глобальный конфиг для языка и режима отладки"""
    lang = "en"
    debug = False
    color = True

    @classmethod
    def set(cls, lang=None, debug=None, color=None):
        if lang is not None:
            cls.lang = lang
        if debug is not None:
            cls.debug = debug
        if color is not None:
            cls.color = color

    @classmethod
    def get_lang(cls):
        return cls.lang

    @classmethod
    def is_debug(cls):
        return cls.debug

    @classmethod
    def is_color(cls):
        return cls.color 