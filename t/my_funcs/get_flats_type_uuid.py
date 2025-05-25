def func(*args, **kwargs):
    if not args:
        return None
    block_uuid = args[0]
    rooms = args[1]
    tags = args[2] if len(args) > 2 else kwargs.get("tags")

    FLATS_TYPE_UUID_MAP = {
        ("f49f5e6b-67f1-4596-a4f8-5f27f1f5f457", "9"): "019f2104-628f-468a-a368-2df80e0b3247",
        ("04c6223f-24fc-412b-bf49-2adcd8ddccc8", "1"): "019f2104-628f-468a-a368-2df80e0b3247",
        ("04c6223f-24fc-412b-bf49-2adcd8ddccc8", "2"): "b35e9518-4d9d-4e58-8b4a-51d7aa42d7ec",
        ("04c6223f-24fc-412b-bf49-2adcd8ddccc8", "3"): "8c89d8c7-7ea0-4412-a0cb-44cb12914309",
        ("04c6223f-24fc-412b-bf49-2adcd8ddccc8", "4"): "1102e5b0-cc60-45dc-bc86-520c1f48f085",
        ("04c6223f-24fc-412b-bf49-2adcd8ddccc8", "5"): "80033d77-b52a-44b9-a630-8f5243b93553",
    }

    FLATS_TYPE_UUID_BY_TAG = {
        "Квартира": {
            "0": "019f2104-628f-468a-a368-2df80e0b3247",
            "1": "b35e9518-4d9d-4e58-8b4a-51d7aa42d7ec",
            "2": "8c89d8c7-7ea0-4412-a0cb-44cb12914309",
            "3": "1102e5b0-cc60-45dc-bc86-520c1f48f085",
            "4": "80033d77-b52a-44b9-a630-8f5243b93553",
            "5": "e03ab11a-1d40-459e-8918-69d2a72f19bb",
            "6": "b1e0f483-af4a-4e22-9944-2e49dd148303",
            "7": "f61066c2-9dc4-49d8-93fd-485f979450dc",
            "8": "41acd6ed-b2a9-48da-b9e7-a45b7d645402",
            "9": "c2e97799-25d6-459e-a88c-ff16eee1f3a2",
        },
        "Апартаменты": {
            "0": "362b73de-c175-4479-a76c-c2ee422b89f5",
            "1": "84203563-c482-45ee-8388-4968fa947834",
            "2": "6f6a9f85-bfb6-4785-acb8-d0877124ee49",
            "3": "aacf7549-1286-421c-8280-a5ea73729e56",
            "4": "9cf2f8f2-b42a-459a-bd37-8d0bd053a6db",
            "5": "f7e3fbcc-98dc-4cfa-a799-e63c14c00690",
            "6": "a3be9f2b-5b1a-4a25-bbb7-956a73a0b469",
            "7": "dfde23eb-a9ba-49b3-8ac2-6481864b6f51",
            "8": "0a060ad3-06ae-4135-935a-0fc5088ff92c",
            "9": "9711fe08-37c2-441b-b5fc-c8b5c79749e5",
        },
    }

    SPECIAL_ROOMS = {
        "Помещение свободного назначения": "e9fff4ac-7a8d-445c-90e7-b5111bf41f99",
        "Торговое помещение": "4bf12c13-75cd-4eba-9f85-06f2394cc4ee",
        "Офисное помещение": "7e8ae9e7-6853-4f77-914e-42552670f965",
    }
    
    key = (block_uuid, rooms)
    if key in FLATS_TYPE_UUID_MAP:
        return FLATS_TYPE_UUID_MAP[key]
    if rooms in SPECIAL_ROOMS:
        return SPECIAL_ROOMS[rooms]
    if tags in FLATS_TYPE_UUID_BY_TAG:
        return FLATS_TYPE_UUID_BY_TAG[tags].get(rooms)
    return None
