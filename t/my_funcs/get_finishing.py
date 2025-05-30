finishing_groups = {
    "Без стен": ["Без стен"],
    "Без отделки": [
        "без отделки", "Без отделки", "нет", "Нет", "черновая", "Черновая", "черновая отделка",
        "without", "preFine", "Улучшенная черновая", "rough"
    ],
    "Чистовая отделка": [
        "Полная отделка", "Чистовая", "чистовая отделка", "Чистовая отделка",
        "Белая отделка", "MR Ready", "Премиум", "fine", "С ремонтом", "Дизайнерский ремонт",
        "Бизнес", "С отделкой"
    ],
    "С мебелью": [
        "С мебелью", "fineWithFurniture", "turnkey", "Чистовая отделка с мебелью"
    ],
    "Предчистовая отделка": [
        "предчистовая", " Предчистовая", "Предчистовая", "предчистовая отделка", "Предчистовая отделка",
        "MR Base", "White box", "Whitebox", "White Box", "Отделка White box", "WhiteBox",
        "серый ключ", "Отделка White Box"
    ]
}

finishing_to_tag = {
    synonym.strip(): tag
    for tag, synonyms in finishing_groups.items()
    for synonym in synonyms
}


def func(*args, **kwargs):
    if not args:
        return None

    value = args[0]
    if not isinstance(value, str):
        return None

    cleaned = value.strip()
    return finishing_to_tag.get(cleaned, None)
