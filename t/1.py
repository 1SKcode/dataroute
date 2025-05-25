import json
from dataroute import DataRoute


def main():
    test_input = """
        lang=py
        notify=tg/console/mail
        source=dict/my_dict
        norm=postgres/norm_data.norm_blocks
        $block9Floor=f49f5e6b-67f1-4596-a4f8-5f27f1f5f457
        norm:
            [block_uuid]    -> [block_uuid](str)
            [is_euro]       -> |*s1|IF($this IN $$mv.is_euro): *get(True) ELSE: *get(False)| -> [is_euro](bool)
            [rooms]         -> |*s1|IF($block_uuid == $block9Floor AND $this == "9" OR $this == None): *get(0)| -> [rooms](str)
            []              -> |*get(\"Свободна\")| -> [status](str)
            [section]       -> |*s1|IF($this == None): *get(\"Нет секции\")| -> [section_name](str)
            [price_sale]    -> |*s1| -> [$price_sale](int)
            [price_base]    -> |*s1|IF($price_sale != None OR $price_sale != \"0\"): *get($price_sale)| -> [price](int)
            [type]          -> |*get_tag_by_type($this)| -> [tags](str)
            [area_total]    -> [area_total](float)
            [area_given]    -> [area_given](float)
            [area_kitchen]  -> [area_kitchen](float)
            [number]        -> |IF($this == None): *get(\"-\")| -> [number](str)                
            [windows]       -> [windows](str)
            [window_view]   -> [window_view](str)
            [view_places]   -> [view_places](str)
            [floor]         -> |*s1|IF($this == None): *get(0)| -> [floor_of_flat](int)   
            [floors_in_section] -> [floors_in_section](int)
            [comment]       -> [comment](str)
            [plan_url]      -> [plan_url](str)
            [floor_plan_url] -> [floor_plan_url](str)
            [finising]      -> |*get_finishing($this)| -> [finishing](str)
            [uuid]          -> [flats_uuid](str)
            []              -> |*get_flats_type_uuid($block_uuid, $rooms, $tags)| -> [flats_type_uuid](str)
            [building_uuid] -> [building_uuid](str)
            []              -> |*get_uuid_real_estate_type($tags)| -> [uuid_real_estate_type](str)
            """
    
    
    dtrt = DataRoute(
        test_input,
        vars_folder="t/my_vars", 
        func_folder="t/my_funcs", 
        debug=True,
        lang="ru", 
        color=True
    )
    result = dtrt.compile_ic()
    dtrt.print_json()

    #dtrt.go(input_data, )
    #dtrt.listen()
    

    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()