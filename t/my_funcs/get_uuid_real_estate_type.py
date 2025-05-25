def func(*args, **kwargs):
    if not args:
        return None
    tag = args[0]
    UUID_REAL_ESTATE_TYPE_MAP = {
    "Апартаменты": "1fc784b5-639c-4777-91ce-da6324ba59f7",
    "Квартира": "9f866b12-2848-4b60-b754-811212ce8657",
    "Машино-место": "53108344-b451-4f8f-87c7-27b9d8337eb6",
    "Загородная недвижимость": "82884858-ce63-4e1a-8356-1b9ce5afbbd9",
    "Таунхаус": "bfeaa7a8-f415-4a80-8c11-f88e55c3a9c9",
    "Кладовка": "25a2ed59-3178-4f0a-92fe-36f4e7d9c221",
    "Коммерческая недвижимость": "97852a12-6ba2-4b98-879e-6277a9d780f9",
    }
    
    return UUID_REAL_ESTATE_TYPE_MAP.get(tag) 