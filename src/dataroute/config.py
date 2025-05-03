class Config:
    """Глобальный конфиг для языка и режима отладки"""
    lang = "ru"
    debug = False

    @classmethod
    def set(cls, lang=None, debug=None):
        if lang is not None:
            cls.lang = lang
        if debug is not None:
            cls.debug = debug

    @classmethod
    def get_lang(cls):
        return cls.lang

    @classmethod
    def is_debug(cls):
        return cls.debug 