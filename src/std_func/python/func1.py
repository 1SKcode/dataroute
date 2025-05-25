def func(*args, **kwargs):
    if len(args) == 0:
        return None
    elif len(args) == 1:
        return args[0]
    else:
        return args