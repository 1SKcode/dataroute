def func(*args, **kwargs):
    if not args:
        return None

    value = args[0]

    if value is None:
        return None

    # Попробуем привести к строке
    try:
        str_value = str(value).strip().lower()
    except Exception:
        return value  # если нельзя привести, вернём как есть

    # Значения, считающиеся пустыми
    null_variants = {"", "none", "null", "nan", "non"}

    if str_value in null_variants:
        return None

    # Пустые коллекции
    if isinstance(value, (list, dict, set, tuple)) and len(value) == 0:
        return None

    # NaN
    try:
        import math
        if isinstance(value, float) and math.isnan(value):
            return None
    except Exception:
        pass

    if isinstance(value, str):
        return value.strip()

    return value


# func("  none  ")       # → None
# func([])               # → None
# func("hello")          # → "hello"
# func(123)              # → 123
# func("   ")            # → None
# func(float("nan"))     # → None
